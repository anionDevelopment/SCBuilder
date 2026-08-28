import os
from ScriptCollection.TFCPS.SCTaskRunnerServer import SCTaskRunnerServer


def main() -> None:
    """Starts the Android-task-runner. It builds Android-app build-steps (e.g. flutter appbundle-builds) on behalf of
    remote clients (see ScriptCollection's TFCPS_RemoteBuild), using the Flutter-/Android-SDK-/NDK-toolchain that is
    installed in this container-image (see the Dockerfile). Unlike SCTaskRunnerWindows/SCTaskRunnerMacOS - which run
    natively because there are no Windows-/macOS-containers - this runner is delivered as a container: the Android-SDK
    works inside a Linux-container, so the container itself can just run permanently and accept jobs. Configuration is
    read from environment-variables:
    - SCTaskRunner_Username / SCTaskRunner_Password: basic-auth-credentials the clients must use.
    - SCTaskRunner_Port: TCP-port to listen on (default 8080).
    - SCTaskRunner_CertificateFile / SCTaskRunner_CertificateKeyFile: when both are set the server is served over TLS
      (https); otherwise plain http is used (e.g. when TLS is terminated by a reverse-proxy in front of the runner)."""
    username = os.environ.get("SCTaskRunner_Username", "")
    password = os.environ.get("SCTaskRunner_Password", "")
    port = int(os.environ.get("SCTaskRunner_Port", "8080"))
    certificate_file = os.environ.get("SCTaskRunner_CertificateFile", None)
    certificate_key_file = os.environ.get("SCTaskRunner_CertificateKeyFile", None)
    SCTaskRunnerServer("Android", username, password).run(port=port, certificate_file=certificate_file, certificate_key_file=certificate_key_file)


if __name__ == "__main__":
    main()
