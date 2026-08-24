import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from ScriptCollection.GeneralUtilities import GeneralUtilities, VersionEcholon
from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore
from ScriptCollection.TFCPS.Docker.TFCPS_CodeUnitSpecific_Docker import TFCPS_CodeUnitSpecific_Docker_Functions,TFCPS_CodeUnitSpecific_Docker_CLI

class Updater:

    # How far a dependency is allowed to be updated. This is the same value which
    # TFCPS_CodeUnitSpecific_Base.update_dependencies uses by default: a new major-version of a tool can change its
    # behaviour or its commandline, which the image and the codeunits which use it have to be adapted to, so a
    # major-version is taken over deliberately and not as a side-effect of running this script.
    __echolon: VersionEcholon = VersionEcholon.LatestPatchOrLatestMinor

    # The duration after which the request to an api is aborted, so that an api which does not answer can not make this
    # script hang forever.
    __timeout_in_seconds: int = 30

    # How many pages of tags are read from a forge. A project with many tags (kubernetes for example) has more of them
    # than one page holds.
    __amount_of_pages_of_tags_to_read: int = 5

    def __init__(self):
        self.__tf: TFCPS_CodeUnitSpecific_Docker_Functions = TFCPS_CodeUnitSpecific_Docker_CLI.parse(__file__)
        self.__sc: ScriptCollectionCore = ScriptCollectionCore()
        self.__resources_folder: str = os.path.join(self.__tf.get_codeunit_folder(), "Other", "Resources")

    @GeneralUtilities.check_arguments
    def __set_dependency_version(self, dependency_name: str, new_version: str) -> None:
        """Sets the version of the given dependency to the given value.

        The version is written into "Other/Resources/Dependencies/<dependency>/Version.txt", which is the file the build
        of the image reads the value of the corresponding build-argument from (see "Other/Build/Build.py"). The used
        function resolves that path relative to the file which is passed to it, so this file has to stay in the folder it
        is located in. It only writes if the version actually changed, so a dependency which is already up to date does
        not result in a modified file."""
        self.__tf.tfcps_Tools_General.update_dependency_in_resources_folder(__file__, dependency_name, new_version)

    @GeneralUtilities.check_arguments
    def __load_json(self, url: str) -> object:
        """Returns the json-document which the given address answers with.

        The api of a forge or of a package-registry is asked directly instead of running the corresponding
        commandline-tool: this script has to be runnable on a machine which does not have every tool of the image
        installed, and every one of these apis answers with the list of the published versions without an account.

        A token is sent if the environment states one. Github allows 60 requests per hour without one and several
        thousand with one, so a machine which has a token (a pipeline for example) does not have to care about the
        limit at all."""
        headers: dict[str, str] = {"Accept": "application/json", "User-Agent": "SCBuilder-UpdateDependency"}
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
    def __update_dependency(self, dependency_name: str, available_versions: list[str], version_prefix: str = "") -> None:
        """Updates the given dependency to the newest of the given versions which the echolon allows.

        The prefix is the part which the version-file contains besides the version itself (PlantUML for example is
        pinned as "v1.2026.6"). It is removed before the versions are compared and added again before the value is
        written, so the file keeps the form which the build of the image expects."""
        chosen_version: str = GeneralUtilities.choose_version(available_versions, self.__get_current_version(dependency_name, version_prefix), self.__echolon)
        self.__set_dependency_version(dependency_name, version_prefix + chosen_version)

    @GeneralUtilities.check_arguments
    def __get_current_version(self, dependency_name: str, version_prefix: str) -> str:
        """Returns the version which is currently pinned for the given dependency, without the prefix of its file."""
        current_version: str = self.__tf.tfcps_Tools_General.get_dependency_version_in_resources_folder(self.__resources_folder, dependency_name)
        if not current_version.startswith(version_prefix):
            raise ValueError(f"The version \"{current_version}\" of the dependency \"{dependency_name}\" does not start with \"{version_prefix}\", so it can not be compared with the available versions.")
        return current_version[len(version_prefix):]

    @GeneralUtilities.check_arguments
    def __update_github_dependency(self, dependency_name: str, repository: str, tag_prefix: str, version_prefix: str = "") -> None:
        current_version: str = self.__get_current_version(dependency_name, version_prefix)
        self.__update_dependency(dependency_name, self.__get_available_versions_of_github_project(repository, tag_prefix, current_version), version_prefix)

    @GeneralUtilities.check_arguments
    def __update_gitlab_dependency(self, dependency_name: str, project: str, tag_prefix: str, version_prefix: str = "") -> None:
        current_version: str = self.__get_current_version(dependency_name, version_prefix)
        self.__update_dependency(dependency_name, self.__get_available_versions_of_gitlab_project(project, tag_prefix, current_version), version_prefix)

    @GeneralUtilities.check_arguments
    def __update_nuget_dependency(self, dependency_name: str, package_id: str) -> None:
        self.__update_dependency(dependency_name, self.__get_available_versions_of_nuget_package(package_id))

    @GeneralUtilities.check_arguments
    def __update_pypi_dependency(self, dependency_name: str, package_name: str) -> None:
        self.__update_dependency(dependency_name, self.__get_available_versions_of_pypi_package(package_name))

    @GeneralUtilities.check_arguments
    def __get_available_versions_of_npm_package(self, package_name: str) -> list[str]:
        """Returns the released versions of the given npm-package.

        "npm view <package> versions --json" answers with all published versions. Only a version which consists of three
        numbers is taken into account, so that a pre-release (for example "8.0.0-beta.1") does not become the version the
        image is built with. npm is executed over epew, which is how ScriptCollection runs npm everywhere else."""
        output: str = self.__sc.run_with_epew("npm", f"view {package_name} versions --json", os.path.dirname(__file__))[1]
        return [version for version in json.loads(output) if re.match(r"^\d+\.\d+\.\d+$", version) is not None]

    @GeneralUtilities.check_arguments
    def __update_npm_dependency(self, dependency_name: str, package_name: str) -> None:
        """Updates the given dependency, which is installed from the given npm-package, as far as the echolon allows."""
        current_version: str = self.__tf.tfcps_Tools_General.get_dependency_version_in_resources_folder(self.__resources_folder, dependency_name)
        available_versions: list[str] = self.__get_available_versions_of_npm_package(package_name)
        self.__set_dependency_version(dependency_name, GeneralUtilities.choose_version(available_versions, current_version, self.__echolon))

    # One function per dependency of this codeunit. The dependencies are the folders of
    # "Other/Resources/Dependencies", where each of them contains the version which the build of the image uses (see
    # "Other/Build/Build.py"), so the functions here are kept in the same (alphabetical) order as those folders to make
    # it visible at a glance whether one of them is missing.

    def __update_dependency_angularcli(self):
        self.__update_npm_dependency("AngularCli", "@angular/cli")

    def __update_dependency_azurecli(self):
        self.__update_pypi_dependency("AzureCli", "azure-cli")

    def __update_dependency_chromium(self):
        pass#TODO

    def __update_dependency_claude(self):
        self.__update_npm_dependency("ClaudeCode", "@anthropic-ai/claude-code")

    def __update_dependency_codex(self):
        self.__update_npm_dependency("Codex", "@openai/codex")

    def __update_dependency_copilot(self):
        self.__update_npm_dependency("Copilot", "@github/copilot")

    def __update_dependency_cyclonedx(self):
        self.__update_nuget_dependency("CycloneDx", "CycloneDX")

    def __update_dependency_cyclonedxnpm(self):
        self.__update_npm_dependency("CycloneDxNpm", "@cyclonedx/cyclonedx-npm")

    def __update_dependency_docfx(self):
        self.__update_nuget_dependency("DocFx", "docfx")

    def __update_dependency_dotnetsdk(self):
        # Not updated here: the pinned value ("10.0") is the feature-band of the apt-package
        # "dotnet-sdk-<band>" and not a complete version, so it is taken over deliberately when the image moves to
        # another band.
        pass

    def __update_dependency_dotnett4(self):
        self.__update_nuget_dependency("DotNetT4", "dotnet-t4")

    def __update_dependency_epew(self):
        self.__update_github_dependency("Epew", "anionDevelopment/Epew", "v")

    def __update_dependency_eslint(self):
        self.__update_npm_dependency("Eslint", "eslint")

    def __update_dependency_flutter(self):
        self.__update_dependency("Flutter", self.__get_available_versions_of_flutter())

    def __update_dependency_geminicli(self):
        self.__update_npm_dependency("GeminiCli", "@google/gemini-cli")

    def __update_dependency_githubcli(self):
        self.__update_github_dependency("GitHubCli", "cli/cli", "v")

    def __update_dependency_gitlabcli(self):
        self.__update_gitlab_dependency("GitLabCli", "gitlab-org/cli", "v")

    def __update_dependency_gitlfs(self):
        self.__update_github_dependency("GitLfs", "git-lfs/git-lfs", "v")

    def __update_dependency_gitversiontool(self):
        self.__update_nuget_dependency("GitVersionTool", "GitVersion.Tool")

    def __update_dependency_go(self):
        self.__update_github_dependency("Go", "golang/go", "go")

    def __update_dependency_gotask(self):
        self.__update_npm_dependency("GoTask", "@go-task/cli")

    def __update_dependency_gulpcli(self):
        self.__update_npm_dependency("GulpCli", "gulp-cli")

    def __update_dependency_helm(self):
        self.__update_github_dependency("Helm", "helm/helm", "v")

    def __update_dependency_jre(self):
        # Not updated here: the pinned value ("21.0.6+7") states the build of a temurin-release, which the
        # download-url of the image is built from. Its form is not the one of the other dependencies, so it is taken
        # over deliberately together with that url.
        pass

    def __update_dependency_jq(self):
        self.__update_github_dependency("Jq", "jqlang/jq", "jq-")

    def __update_dependency_kubectl(self):
        self.__update_github_dependency("Kubectl", "kubernetes/kubernetes", "v")

    def __update_dependency_kustomize(self):
        self.__update_github_dependency("Kustomize", "kubernetes-sigs/kustomize", "kustomize/v")

    def __update_dependency_mistralvibe(self):
        self.__update_pypi_dependency("MistralVibe", "mistral-vibe")

    def __update_dependency_node(self):
        # Not updated here: the pinned value ("22") is the major-version which the nodesource-setup-script
        # expects, and a new major-version is taken over deliberately (see the echolon above).
        pass

    def __update_dependency_opencode(self):
        self.__update_npm_dependency("OpenCode", "opencode-ai")

    def __update_dependency_openspec(self):
        self.__update_npm_dependency("OpenSpec", "@fission-ai/openspec")

    def __update_dependency_plantuml(self):
        # The version-file of plantuml contains the tag itself (for example "v1.2026.6"), so the "v" is part
        # of the value which is written.
        self.__update_github_dependency("PlantUML", "plantuml/plantuml", "v", "v")

    def __update_dependency_playwright(self):
        self.__update_npm_dependency("Playwright", "playwright")

    def __update_dependency_pnpm(self):
        self.__update_npm_dependency("Pnpm", "pnpm")

    def __update_dependency_prettier(self):
        self.__update_npm_dependency("Prettier", "prettier")

    def __update_dependency_reportgenerator(self):
        self.__update_nuget_dependency("ReportGenerator", "dotnet-reportgenerator-globaltool")

    def __update_dependency_rust(self):
        self.__update_github_dependency("Rust", "rust-lang/rust", "")

    def __update_dependency_scriptcollection(self):
        self.__update_pypi_dependency("ScriptCollection", "ScriptCollection")

    def __update_dependency_shellcheck(self):
        self.__update_github_dependency("ShellCheck", "koalaman/shellcheck", "v")

    def __update_dependency_swashbuckle(self):
        self.__update_nuget_dependency("Swashbuckle", "swashbuckle.aspnetcore.cli")

    def __update_dependency_typescript(self):
        self.__update_npm_dependency("TypeScript", "typescript")

    def __update_dependency_vega(self):
        self.__update_npm_dependency("Vega", "vega")

    def __update_dependency_vegacli(self):
        self.__update_npm_dependency("VegaCli", "vega-cli")

    def __update_dependency_vegaembed(self):
        self.__update_npm_dependency("VegaEmbed", "vega-embed")

    def __update_dependency_vegalite(self):
        self.__update_npm_dependency("VegaLite", "vega-lite")

    def __update_dependency_yq(self):
        self.__update_github_dependency("Yq", "mikefarah/yq", "v")

    def update_dependencies(self):
        self.__update_dependency_angularcli()
        self.__update_dependency_azurecli()
        self.__update_dependency_chromium()
        self.__update_dependency_claude()
        self.__update_dependency_codex()
        self.__update_dependency_copilot()
        self.__update_dependency_cyclonedx()
        self.__update_dependency_cyclonedxnpm()
        self.__update_dependency_docfx()
        self.__update_dependency_dotnetsdk()
        self.__update_dependency_dotnett4()
        self.__update_dependency_epew()
        self.__update_dependency_eslint()
        self.__update_dependency_flutter()
        self.__update_dependency_geminicli()
        self.__update_dependency_githubcli()
        self.__update_dependency_gitlabcli()
        self.__update_dependency_gitlfs()
        self.__update_dependency_gitversiontool()
        self.__update_dependency_go()
        self.__update_dependency_gotask()
        self.__update_dependency_gulpcli()
        self.__update_dependency_helm()
        self.__update_dependency_jre()
        self.__update_dependency_jq()
        self.__update_dependency_kubectl()
        self.__update_dependency_kustomize()
        self.__update_dependency_mistralvibe()
        self.__update_dependency_node()
        self.__update_dependency_opencode()
        self.__update_dependency_openspec()
        self.__update_dependency_plantuml()
        self.__update_dependency_playwright()
        self.__update_dependency_pnpm()
        self.__update_dependency_prettier()
        self.__update_dependency_reportgenerator()
        self.__update_dependency_rust()
        self.__update_dependency_scriptcollection()
        self.__update_dependency_shellcheck()
        self.__update_dependency_swashbuckle()
        self.__update_dependency_typescript()
        self.__update_dependency_vega()
        self.__update_dependency_vegacli()
        self.__update_dependency_vegaembed()
        self.__update_dependency_vegalite()
        self.__update_dependency_yq()

def update_dependencies():
    updater=Updater()
    updater.update_dependencies()


if __name__ == "__main__":
    update_dependencies()
