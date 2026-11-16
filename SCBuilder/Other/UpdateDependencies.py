import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from ScriptCollection.GeneralUtilities import GeneralUtilities
from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore
from ScriptCollection.TFCPS.Docker.TFCPS_CodeUnitSpecific_Docker import TFCPS_CodeUnitSpecific_Docker_Functions,TFCPS_CodeUnitSpecific_Docker_CLI

class Updater:

    # The duration after which the request to an api is aborted, so that an api which does not answer can not make this
    # script hang forever.
    __timeout_in_seconds: int = 30

    # How many pages of tags are read from a forge. A project with many tags (kubernetes for example) has more of them
    # than one page holds.
    __amount_of_pages_of_tags_to_read: int = 5

    def __init__(self):
        self.__tf: TFCPS_CodeUnitSpecific_Docker_Functions = TFCPS_CodeUnitSpecific_Docker_CLI.parse(__file__)
        self.__sc: ScriptCollectionCore = ScriptCollectionCore()

    @GeneralUtilities.check_arguments
    def __load_json(self, url: str) -> object:
        """Returns the json-document which the given address answers with.

        The api of a forge or of a package-registry is asked directly instead of running the corresponding
        commandline-tool: this script has to be runnable on a machine which does not have every tool of the image
        installed, and every one of these apis answers with the list of the published versions without an account.

        A token is sent if the environment states one. Github allows 60 requests per hour without one and several
        thousand with one, so a machine which has a token (a pipeline for example) does not have to care about the
        limit at all."""
        headers: dict[str, str] = {"Accept": "application/json", "User-Agent": "SCBuilder-UpdateDependencies"}
        if url.startswith("https://api.github.com/"):
            token: str = os.environ.get("GH_TOKEN", os.environ.get("GITHUB_TOKEN", GeneralUtilities.empty_string))
            if GeneralUtilities.string_has_content(token):
                headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=Updater.__timeout_in_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exception:
            if exception.code == 403 or exception.code == 429:
                # This is not a defect of this script and it is not something which is solved by trying again
                # immediately, so it is stated as what it is instead of appearing as a traceback of urllib.
                raise ValueError(f"The api answered that the rate-limit is exceeded while asking \"{url}\". Set the environment-variable \"GH_TOKEN\" to a github-token to raise that limit, or run this script again later.") from exception
            raise

    @GeneralUtilities.check_arguments
    def __get_available_versions_from_tags(self, url_of_the_page: str, tag_prefix: str, current_version: str) -> list[str]:
        """Returns the versions which the tags of a repository state.

        The tags are read and not the releases, because a project which publishes its artifacts without creating a
        release-entry (which some of these projects do) would otherwise look like a project without any version. Only a
        tag which consists of the given prefix and three numbers is taken into account, so that a pre-release or a tag
        which belongs to something else does not become the version the image is built with.

        The reading stops as soon as the version which is currently pinned was seen: a forge answers with its newest
        tags first, and a version which is older than the pinned one can not become the chosen one anyway. That keeps
        this at one request per dependency in the normal case, which matters because the rate-limit of github is 60
        requests per hour for a machine without a token."""
        result: list[str] = []
        regex = re.compile("^" + re.escape(tag_prefix) + r"(\d+\.\d+\.\d+)$")
        for page in range(1, Updater.__amount_of_pages_of_tags_to_read + 1):
            tags = self.__load_json(f"{url_of_the_page}&page={page}")
            if len(tags) == 0:
                break
            for tag in tags:
                match = regex.match(tag["name"])
                if match is not None:
                    result.append(match.group(1))
            if current_version in result:
                break
        return result

    @GeneralUtilities.check_arguments
    def __get_available_versions_of_github_project(self, repository: str, tag_prefix: str, current_version: str) -> list[str]:
        """Returns the released versions of the given github-project ("<owner>/<name>")."""
        return self.__get_available_versions_from_tags(f"https://api.github.com/repos/{repository}/tags?per_page=100", tag_prefix, current_version)

    @GeneralUtilities.check_arguments
    def __get_available_versions_of_gitlab_project(self, project: str, tag_prefix: str, current_version: str) -> list[str]:
        """Returns the released versions of the given gitlab-project ("<group>/<name>")."""
        return self.__get_available_versions_from_tags(f"https://gitlab.com/api/v4/projects/{urllib.parse.quote(project, safe='')}/repository/tags?per_page=100", tag_prefix, current_version)

    @GeneralUtilities.check_arguments
    def __get_available_versions_of_flutter(self) -> list[str]:
        """Returns the versions which flutter released on its stable-channel.

        The release-list of flutter is asked and not its tags: flutter tags every pre-release as well, and there are so
        many of them that the released versions would not be found among them reliably. This list is additionally the
        one the sdk itself is downloaded from."""
        answer = self.__load_json("https://storage.googleapis.com/flutter_infra_release/releases/releases_linux.json")
        return [release["version"] for release in answer["releases"] if release["channel"] == "stable" and re.match(r"^\d+\.\d+\.\d+$", release["version"]) is not None]

    @GeneralUtilities.check_arguments
    def __get_available_versions_of_nuget_package(self, package_id: str) -> list[str]:
        """Returns the released versions of the given nuget-package.

        The flat-container-api answers with the complete list of the versions of exactly this package and expects the
        id in lowercase."""
        answer = self.__load_json(f"https://api.nuget.org/v3-flatcontainer/{package_id.lower()}/index.json")
        return [version for version in answer["versions"] if re.match(r"^\d+\.\d+\.\d+$", version) is not None]

    @GeneralUtilities.check_arguments
    def __get_available_versions_of_pypi_package(self, package_name: str) -> list[str]:
        """Returns the released versions of the given python-package.

        Only a version which has files is taken into account: a release whose files were removed can not be installed
        anymore, so it must not become the version the image is built with."""
        answer = self.__load_json(f"https://pypi.org/pypi/{package_name}/json")
        return [version for version, files in answer["releases"].items() if len(files) > 0 and re.match(r"^\d+\.\d+\.\d+$", version) is not None]

    @GeneralUtilities.check_arguments
    def __get_available_versions_of_crate(self, crate_name: str) -> list[str]:
        """Returns the released versions of the given crate of crates.io.

        A version which was yanked is not taken into account, because it is not meant to be installed anymore, and
        only a version which consists of three numbers is taken into account, so that a pre-release does not become
        the version the image is built with."""
        answer = self.__load_json(f"https://crates.io/api/v1/crates/{crate_name}/versions")
        return [version["num"] for version in answer["versions"] if not version.get("yanked", False) and re.match(r"^\d+\.\d+\.\d+$", version["num"]) is not None]

    def __get_latest_version_of_cursor_cli(self) -> str:
        """Returns the newest version of cursor-cli.

        Cursor does not publish a list of its versions. The only source is its official installer, which contains the
        version it downloads. That version consists of a date and a commit-hash (for example "2026.11.13-eacade1")
        and not of three numbers, so the echolon can not be applied to it and the newest version is always taken over.
        That is why it is in the ignored dependencies of the codeunit-file and updated by this script itself."""
        request = urllib.request.Request("https://cursor.com/install", headers={"User-Agent": "SCBuilder-UpdateDependencies"})
        with urllib.request.urlopen(request, timeout=Updater.__timeout_in_seconds) as response:
            installer: str = response.read().decode("utf-8")
        match = re.search(r"https://downloads\.cursor\.com/lab/(\d{4}\.\d{2}\.\d{2}-[0-9a-f]+)/", installer)
        if match is None:
            raise ValueError("The installer of cursor-cli does not contain a download-url with a version.")
        return match.group(1)

    @GeneralUtilities.check_arguments
    def __get_available_versions_of_npm_package(self, package_name: str) -> list[str]:
        """Returns the released versions of the given npm-package.

        "npm view <package> versions --json" answers with all published versions. Only a version which consists of three
        numbers is taken into account, so that a pre-release (for example "8.0.0-beta.1") does not become the version the
        image is built with. npm is executed over epew, which is how ScriptCollection runs npm everywhere else."""
        output: str = self.__sc.run_with_epew("npm", f"view {package_name} versions --json", os.path.dirname(__file__))[1]
        return [version for version in json.loads(output) if re.match(r"^\d+\.\d+\.\d+$", version) is not None]

    @GeneralUtilities.check_arguments
    def __register_npm_dependency(self, dependency_name: str, package_name: str) -> None:
        self.__tf.register_available_versions_function(dependency_name, lambda current_version: self.__get_available_versions_of_npm_package(package_name))

    @GeneralUtilities.check_arguments
    def __register_nuget_dependency(self, dependency_name: str, package_id: str) -> None:
        self.__tf.register_available_versions_function(dependency_name, lambda current_version: self.__get_available_versions_of_nuget_package(package_id))

    @GeneralUtilities.check_arguments
    def __register_pypi_dependency(self, dependency_name: str, package_name: str) -> None:
        self.__tf.register_available_versions_function(dependency_name, lambda current_version: self.__get_available_versions_of_pypi_package(package_name))

    @GeneralUtilities.check_arguments
    def __register_crate_dependency(self, dependency_name: str, crate_name: str) -> None:
        self.__tf.register_available_versions_function(dependency_name, lambda current_version: self.__get_available_versions_of_crate(crate_name))

    @GeneralUtilities.check_arguments
    def __register_github_dependency(self, dependency_name: str, repository: str, tag_prefix: str) -> None:
        self.__tf.register_available_versions_function(dependency_name, lambda current_version: self.__get_available_versions_of_github_project(repository, tag_prefix, current_version))

    @GeneralUtilities.check_arguments
    def __register_gitlab_dependency(self, dependency_name: str, project: str, tag_prefix: str) -> None:
        self.__tf.register_available_versions_function(dependency_name, lambda current_version: self.__get_available_versions_of_gitlab_project(project, tag_prefix, current_version))

    def __register_available_versions_functions(self) -> None:
        """Registers for every dependency of this codeunit where its available versions come from.

        The dependencies are the folders of "Other/Resources/Dependencies", where each of them contains the version which
        the build of the image uses (see "Other/Build/Build.py"). The registrations are kept in the same (alphabetical)
        order as those folders. A dependency which is not registered here must be listed in the ignored dependencies of
        the codeunit-file, otherwise the update fails. Ignored are:
        - Chromium, Codespell, Kotlin, PlantUML: no source for their available versions is implemented yet.
        - CursorCli: its version is not of the form "<major>.<minor>.<patch>", so it is updated by this script itself.
        - DotNetSdk: the pinned value is the feature-band of the apt-package "dotnet-sdk-<band>", which is taken over
          deliberately when the image moves to another band.
        - JDK: the pinned value states the build of a temurin-release, which the download-url of the image is built from,
          so it is taken over deliberately together with that url.
        - Node: the major-version is the one which the nodesource-setup-script expects, so it is taken over deliberately."""
        self.__register_npm_dependency("AngularCli", "@angular/cli")
        self.__register_pypi_dependency("AzureCli", "azure-cli")
        self.__register_crate_dependency("CargoCycloneDx", "cargo-cyclonedx")
        self.__register_crate_dependency("CargoLlvmCov", "cargo-llvm-cov")
        self.__register_npm_dependency("ClaudeCode", "@anthropic-ai/claude-code")
        self.__register_npm_dependency("Codex", "@openai/codex")
        self.__register_npm_dependency("Copilot", "@github/copilot")
        self.__register_nuget_dependency("CycloneDx", "CycloneDX")
        self.__register_npm_dependency("CycloneDxNpm", "@cyclonedx/cyclonedx-npm")
        self.__register_nuget_dependency("DocFx", "docfx")
        self.__register_nuget_dependency("DotNetT4", "dotnet-t4")
        self.__register_github_dependency("Epew", "anionDevelopment/Epew", "v")
        self.__register_npm_dependency("Eslint", "eslint")
        self.__tf.register_available_versions_function("Flutter", lambda current_version: self.__get_available_versions_of_flutter())
        self.__register_npm_dependency("GeminiCli", "@google/gemini-cli")
        self.__register_github_dependency("GitHubCli", "cli/cli", "v")
        self.__register_gitlab_dependency("GitLabCli", "gitlab-org/cli", "v")
        self.__register_github_dependency("GitLfs", "git-lfs/git-lfs", "v")
        self.__register_nuget_dependency("GitVersionTool", "GitVersion.Tool")
        self.__register_github_dependency("Go", "golang/go", "go")
        self.__register_npm_dependency("GoTask", "@go-task/cli")
        self.__register_npm_dependency("GulpCli", "gulp-cli")
        self.__register_github_dependency("Helm", "helm/helm", "v")
        self.__register_github_dependency("Jq", "jqlang/jq", "jq-")
        self.__register_github_dependency("Kubectl", "kubernetes/kubernetes", "v")
        self.__register_github_dependency("Kustomize", "kubernetes-sigs/kustomize", "kustomize/v")
        self.__register_pypi_dependency("MistralVibe", "mistral-vibe")
        self.__register_npm_dependency("OpenCode", "opencode-ai")
        self.__register_npm_dependency("OpenSpec", "@fission-ai/openspec")
        self.__register_npm_dependency("Playwright", "playwright")
        self.__register_npm_dependency("Pnpm", "pnpm")
        self.__register_npm_dependency("Prettier", "prettier")
        self.__register_nuget_dependency("ReportGenerator", "dotnet-reportgenerator-globaltool")
        self.__register_github_dependency("Rust", "rust-lang/rust", "")
        self.__register_pypi_dependency("ScriptCollection", "ScriptCollection")
        self.__register_github_dependency("ShellCheck", "koalaman/shellcheck", "v")
        self.__register_nuget_dependency("Swashbuckle", "swashbuckle.aspnetcore.cli")
        self.__register_npm_dependency("TypeScript", "typescript")
        self.__register_npm_dependency("Vega", "vega")
        self.__register_npm_dependency("VegaCli", "vega-cli")
        self.__register_npm_dependency("VegaEmbed", "vega-embed")
        self.__register_npm_dependency("VegaLite", "vega-lite")
        self.__register_github_dependency("Yq", "mikefarah/yq", "v")

    def update_dependencies(self):
        """Updates the dependencies of this codeunit using the generic dependency-update of ScriptCollection, which also
        informs about newer major-versions which are not taken over."""
        self.__register_available_versions_functions()
        self.__tf.update_dependencies()
        self.__tf.set_dependency_version("CursorCli", self.__get_latest_version_of_cursor_cli())

def update_dependencies():
    updater=Updater()
    updater.update_dependencies()


if __name__ == "__main__":
    update_dependencies()
