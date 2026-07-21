import os

from ScriptCollection.GeneralUtilities import Platform
from ScriptCollection.TFCPS.Docker.TFCPS_CodeUnitSpecific_Docker import TFCPS_CodeUnitSpecific_Docker_Functions,TFCPS_CodeUnitSpecific_Docker_CLI

 
def build():
    platforms:list[Platform] = [
            Platform.Linux_AMD64,
            #Platform.Linux_ARM64,
    ]
    tf:TFCPS_CodeUnitSpecific_Docker_Functions=TFCPS_CodeUnitSpecific_Docker_CLI.parse(__file__)
    resources_folder=os.path.join(tf.get_codeunit_folder(),"Other","Resources")
    def dependency_version(dependency_name:str)->str:
        return tf.tfcps_Tools_General.get_dependency_version_in_resources_folder(resources_folder,dependency_name)
    # the exact java-build (e.g. "21.0.6+7") is the JRE-pin; JavaVersion is its major (e.g. "21"). This is the same
    # JRE/Version.txt that ScriptCollection reads for the PlantUML-rendering, so the system-JDK matches that JRE.
    java_build_version=dependency_version("JRE")
    # each build-arg is read from the corresponding Other/Resources/Dependencies/<dependency>/Version.txt-file
    build_arguments={
        "image_debian":tf.tfcps_Tools_General.oci_image_manager.get_registry_address_for_image_with_default_tag(tf.get_repository_folder(),"Debian"),
        "JavaVersion":java_build_version.split(".")[0],
        "JavaBuildVersion":java_build_version,
        "NodeVersion":dependency_version("Node"),
        "ChromiumVersion":dependency_version("Chromium"),
        "GoVersion":dependency_version("Go"),
        "DotNetSdkVersion":dependency_version("DotNetSdk"),
        "EpewVersion":dependency_version("Epew"),
        "GitVersionToolVersion":dependency_version("GitVersionTool"),
        "ReportGeneratorVersion":dependency_version("ReportGenerator"),
        "DocFxVersion":dependency_version("DocFx"),
        "DotNetT4Version":dependency_version("DotNetT4"),
        "CycloneDxVersion":dependency_version("CycloneDx"),
        "SwashbuckleVersion":dependency_version("Swashbuckle"),
        "RustVersion":dependency_version("Rust"),
        "AngularCliVersion":dependency_version("AngularCli"),
        "GoTaskVersion":dependency_version("GoTask"),
        "PnpmVersion":dependency_version("Pnpm"),
        "TypeScriptVersion":dependency_version("TypeScript"),
        "EslintVersion":dependency_version("Eslint"),
        "PrettierVersion":dependency_version("Prettier"),
        "VegaVersion":dependency_version("Vega"),
        "VegaCliVersion":dependency_version("VegaCli"),
        "VegaLiteVersion":dependency_version("VegaLite"),
        "VegaEmbedVersion":dependency_version("VegaEmbed"),
        "CycloneDxNpmVersion":dependency_version("CycloneDxNpm"),
        "FlutterVersion":dependency_version("Flutter"),
        "ScriptCollectionVersion":dependency_version("ScriptCollection"),
        "ClaudeCodeVersion":dependency_version("ClaudeCode"),
        "CodexVersion":dependency_version("Codex"),
        "CopilotVersion":dependency_version("Copilot"),
    }
    tf.build(platforms,build_arguments)
    #TODO add sboms


if __name__ == "__main__":
    build()
