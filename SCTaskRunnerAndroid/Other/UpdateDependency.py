import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from ScriptCollection.GeneralUtilities import GeneralUtilities, VersionEcholon
from ScriptCollection.TFCPS.Docker.TFCPS_CodeUnitSpecific_Docker import TFCPS_CodeUnitSpecific_Docker_Functions,TFCPS_CodeUnitSpecific_Docker_CLI

class Updater:

    # How far a dependency is allowed to be updated. Same default as SCBuilder's updater uses: a new major-version of a
    # tool can change its behaviour or its commandline, which the image and the codeunits which use it have to be
    # adapted to, so a major-version is taken over deliberately and not as a side-effect of running this script.
    __echolon: VersionEcholon = VersionEcholon.LatestPatchOrLatestMinor

    # The duration after which the request to an api is aborted, so that an api which does not answer can not make this
    # script hang forever.
    __timeout_in_seconds: int = 30

    def __init__(self):
        self.__tf: TFCPS_CodeUnitSpecific_Docker_Functions = TFCPS_CodeUnitSpecific_Docker_CLI.parse(__file__)
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
        installed, and every one of these apis answers with the list of the published versions without an account."""
        headers: dict[str, str] = {"Accept": "application/json", "User-Agent": "SCTaskRunnerAndroid-UpdateDependency"}
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
    def __get_available_versions_of_flutter(self) -> list[str]:
        """Returns the versions which flutter released on its stable-channel.

        The release-list of flutter is asked and not its tags: flutter tags every pre-release as well, and there are so
        many of them that the released versions would not be found among them reliably. This list is additionally the
        one the sdk itself is downloaded from."""
        answer = self.__load_json("https://storage.googleapis.com/flutter_infra_release/releases/releases_linux.json")
        return [release["version"] for release in answer["releases"] if release["channel"] == "stable" and re.match(r"^\d+\.\d+\.\d+$", release["version"]) is not None]

    @GeneralUtilities.check_arguments
    def __get_available_versions_of_pypi_package(self, package_name: str) -> list[str]:
        """Returns the released versions of the given python-package.

        Only a version which has files is taken into account: a release whose files were removed can not be installed
        anymore, so it must not become the version the image is built with."""
        answer = self.__load_json(f"https://pypi.org/pypi/{package_name}/json")
        return [version for version, files in answer["releases"].items() if len(files) > 0 and re.match(r"^\d+\.\d+\.\d+$", version) is not None]

    @GeneralUtilities.check_arguments
    def __update_dependency(self, dependency_name: str, available_versions: list[str]) -> None:
        """Updates the given dependency to the newest of the given versions which the echolon allows."""
        current_version: str = self.__tf.tfcps_Tools_General.get_dependency_version_in_resources_folder(self.__resources_folder, dependency_name)
        chosen_version: str = GeneralUtilities.choose_version(available_versions, current_version, self.__echolon)
        self.__set_dependency_version(dependency_name, chosen_version)

    @GeneralUtilities.check_arguments
    def __update_pypi_dependency(self, dependency_name: str, package_name: str) -> None:
        self.__update_dependency(dependency_name, self.__get_available_versions_of_pypi_package(package_name))

    # One function per dependency of this codeunit which can actually be resolved to a list of available versions (kept
    # in the same order as the "Other/Resources/Dependencies"-folders, analogous to SCBuilder's updater).

    def __update_dependency_flutter(self):
        self.__update_dependency("Flutter", self.__get_available_versions_of_flutter())

    def __update_dependency_jre(self):
        # Not updated here: the pinned value ("21.0.6+7") states the build of a temurin-release, which the
        # download-url of the image is built from. Its form is not the one of the other dependencies, so it is taken
        # over deliberately together with that url. Kept in sync with the JRE-pin of SCBuilder.
        pass

    def __update_dependency_scriptcollection(self):
        self.__update_pypi_dependency("ScriptCollection", "ScriptCollection")

    # The four Android-SDK-dependencies (AndroidCmdlineTools/AndroidPlatform/AndroidBuildTools/AndroidNdk) are
    # deliberately not auto-updated, same as they never were in SCBuilder before Android-app-building moved into this
    # codeunit: there is no reliable "list of available versions"-api for them, so they are determined empirically by
    # running a Flutter-android-build with the pinned FlutterVersion and reading which packages the
    # Flutter-Gradle-plugin then auto-downloaded (see the comment in the Dockerfile), and re-pinned here by hand
    # whenever FlutterVersion is bumped.

    def update_dependencies(self):
        self.__update_dependency_flutter()
        self.__update_dependency_jre()
        self.__update_dependency_scriptcollection()

def update_dependencies():
    updater=Updater()
    updater.update_dependencies()


if __name__ == "__main__":
    update_dependencies()
