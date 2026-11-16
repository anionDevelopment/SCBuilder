import json
import re
import urllib.error
import urllib.request
from ScriptCollection.GeneralUtilities import GeneralUtilities
from ScriptCollection.TFCPS.Docker.TFCPS_CodeUnitSpecific_Docker import TFCPS_CodeUnitSpecific_Docker_Functions,TFCPS_CodeUnitSpecific_Docker_CLI

class Updater:

    # The duration after which the request to an api is aborted, so that an api which does not answer can not make this
    # script hang forever.
    __timeout_in_seconds: int = 30

    def __init__(self):
        self.__tf: TFCPS_CodeUnitSpecific_Docker_Functions = TFCPS_CodeUnitSpecific_Docker_CLI.parse(__file__)

    @GeneralUtilities.check_arguments
    def __load_json(self, url: str) -> object:
        """Returns the json-document which the given address answers with.

        The api of a package-registry is asked directly instead of running the corresponding commandline-tool: this
        script has to be runnable on a machine which does not have every tool of the image installed, and the api
        answers with the list of the published versions without an account."""
        headers: dict[str, str] = {"Accept": "application/json", "User-Agent": "SCTaskRunnerAndroid-UpdateDependencies"}
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=Updater.__timeout_in_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exception:
            if exception.code == 403 or exception.code == 429:
                # This is not a defect of this script and it is not something which is solved by trying again
                # immediately, so it is stated as what it is instead of appearing as a traceback of urllib.
                raise ValueError(f"The api answered that the rate-limit is exceeded while asking \"{url}\". Run this script again later.") from exception
            raise

    @GeneralUtilities.check_arguments
    def __get_available_versions_of_pypi_package(self, package_name: str) -> list[str]:
        """Returns the released versions of the given python-package.

        Only a version which has files is taken into account: a release whose files were removed can not be installed
        anymore, so it must not become the version the image is built with."""
        answer = self.__load_json(f"https://pypi.org/pypi/{package_name}/json")
        return [version for version, files in answer["releases"].items() if len(files) > 0 and re.match(r"^\d+\.\d+\.\d+$", version) is not None]

    def __register_available_versions_functions(self) -> None:
        """Registers for every dependency of this codeunit where its available versions come from.

        The dependencies are the folders of "Other/Resources/Dependencies". A dependency which is not registered here
        must be listed in the ignored dependencies of the codeunit-file, otherwise the update fails. Ignored are:
        - Flutter: this image is not the only environment which builds a flutter-codeunit. Only its android-target is
          built here, everything else is built in the SCBuilder-image (which pins the same version) or on the machine
          of the developer, and a flutter-package states in its "pubspec.yaml" which Dart-SDK it is built with. An
          environment whose flutter differs from the others therefore either can not resolve the packages at all or
          produces screenshots which do not match the checked-in baseline-images of the visual-regression-tests. The
          version is raised by hand - here, in SCBuilder and on the machines of the developers together - so that it
          can not drift apart environment by environment, depending on where the update ran last. The
          android-platform- and the ndk-pin have to be checked in the same step, because the Flutter-Gradle-plugin
          picks both of them for an app itself (see the Dockerfile).
        - JDK: the pinned value states the build of a temurin-release, which the download-url of the image is built
          from. Its form is not the one of the other dependencies, so it is taken over deliberately together with that
          url. Kept in sync with the JDK-pin of SCBuilder.
        - AndroidCmdlineTools, AndroidPlatform, AndroidBuildTools, AndroidNdk: there is no reliable "list of available
          versions"-api for them. Which of them an android-build needs is not a matter of taste either - the platform-
          and the ndk-version are the ones the Flutter-Gradle-plugin states in
          "packages/flutter_tools/gradle/src/main/kotlin/FlutterExtension.kt" ("compileSdkVersion" respectively
          "ndkVersion") of the pinned FlutterVersion, so they are read from there and pinned by hand whenever that
          version is bumped (see the Dockerfile)."""
        self.__tf.register_available_versions_function("ScriptCollection", lambda current_version: self.__get_available_versions_of_pypi_package("ScriptCollection"))

    def update_dependencies(self):
        """Updates the dependencies of this codeunit using the generic dependency-update of ScriptCollection, which also
        informs about newer major-versions which are not taken over."""
        self.__register_available_versions_functions()
        self.__tf.update_dependencies()

def update_dependencies():
    updater=Updater()
    updater.update_dependencies()


if __name__ == "__main__":
    update_dependencies()
