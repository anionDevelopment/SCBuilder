from ScriptCollection.TFCPS.Docker.TFCPS_CodeUnitSpecific_Docker import TFCPS_CodeUnitSpecific_Docker_Functions,TFCPS_CodeUnitSpecific_Docker_CLI
from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore

class Updater:

    __sc:ScriptCollectionCore=None

    def __init__(self):
        self.__sc=ScriptCollectionCore()

    def __set_dependency_version(self,dependency_name:str,new_version:str):
        pass#TODO

    # One function per dependency of this codeunit. The dependencies are the folders of
    # "Other/Resources/Dependencies", where each of them contains the version which the build of the image uses (see
    # "Other/Build/Build.py"), so the functions here are kept in the same (alphabetical) order as those folders to make
    # it visible at a glance whether one of them is missing.
    # important note: when implementing a new version, consider the following: some packages can be installed using different ways/sources (npm, directly via curl, etc.). the update-function should look for a new version there where it will be installed from later in the dockerfile if possible.

    def __update_dependency_angularcli(self):
        pass#TODO

    def __update_dependency_azurecli(self):
        pass#TODO

    def __update_dependency_chromium(self):
        pass#TODO

    def __update_dependency_claude(self):
        pass#TODO

    def __update_dependency_codex(self):
        pass#TODO

    def __update_dependency_copilot(self):
        pass#TODO

    def __update_dependency_cyclonedx(self):
        pass#TODO

    def __update_dependency_cyclonedxnpm(self):
        pass#TODO

    def __update_dependency_docfx(self):
        pass#TODO

    def __update_dependency_dotnetsdk(self):
        pass#TODO

    def __update_dependency_dotnett4(self):
        pass#TODO

    def __update_dependency_epew(self):
        pass#TODO

    def __update_dependency_eslint(self):
        pass#TODO

    def __update_dependency_flutter(self):
        pass#TODO

    def __update_dependency_geminicli(self):
        pass#TODO

    def __update_dependency_githubcli(self):
        pass#TODO

    def __update_dependency_gitlabcli(self):
        pass#TODO

    def __update_dependency_gitlfs(self):
        pass#TODO

    def __update_dependency_gitversiontool(self):
        pass#TODO

    def __update_dependency_go(self):
        pass#TODO

    def __update_dependency_gotask(self):
        pass#TODO

    def __update_dependency_gulpcli(self):
        pass#TODO

    def __update_dependency_helm(self):
        pass#TODO

    def __update_dependency_jre(self):
        pass#TODO

    def __update_dependency_jq(self):
        pass#TODO

    def __update_dependency_kubectl(self):
        pass#TODO

    def __update_dependency_kustomize(self):
        pass#TODO

    def __update_dependency_node(self):
        pass#TODO

    def __update_dependency_opencode(self):
        pass#TODO

    def __update_dependency_openspec(self):
        pass#TODO

    def __update_dependency_plantuml(self):
        pass#TODO

    def __update_dependency_playwright(self):
        pass#TODO

    def __update_dependency_pnpm(self):
        pass#TODO

    def __update_dependency_prettier(self):
        pass#TODO

    def __update_dependency_reportgenerator(self):
        pass#TODO

    def __update_dependency_rust(self):
        pass#TODO

    def __update_dependency_scriptcollection(self):
        pass#TODO

    def __update_dependency_shellcheck(self):
        pass#TODO

    def __update_dependency_swashbuckle(self):
        pass#TODO

    def __update_dependency_typescript(self):
        pass#TODO

    def __update_dependency_vega(self):
        pass#TODO

    def __update_dependency_vegacli(self):
        pass#TODO

    def __update_dependency_vegaembed(self):
        pass#TODO

    def __update_dependency_vegalite(self):
        pass#TODO

    def __update_dependency_yq(self):
        pass#TODO

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
