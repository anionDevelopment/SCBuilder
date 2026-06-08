import os

from ScriptCollection.GeneralUtilities import Platform
from ScriptCollection.TFCPS.Docker.TFCPS_CodeUnitSpecific_Docker import TFCPS_CodeUnitSpecific_Docker_Functions,TFCPS_CodeUnitSpecific_Docker_CLI


def build():
    platforms:list[Platform] = [
            Platform.Linux_AMD64,
            #Platform.Linux_ARM64,
    ]
    tf:TFCPS_CodeUnitSpecific_Docker_Functions=TFCPS_CodeUnitSpecific_Docker_CLI.parse(__file__)
    github_runner_version=tf.tfcps_Tools_General.get_dependency_version_in_resources_folder(os.path.join(tf.get_codeunit_folder(),"Other","Resources"),"GitHubRunner")
    tf.build(platforms,{
        "image_debian":tf.tfcps_Tools_General.oci_image_manager.get_registry_address_for_image_with_default_tag(tf.get_repository_folder(),"Debian"),
        "GitHubRunnerVersion":github_runner_version,
    })


if __name__ == "__main__":
    build()
