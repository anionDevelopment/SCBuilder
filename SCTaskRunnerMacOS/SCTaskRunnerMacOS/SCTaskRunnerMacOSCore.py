import os
from ScriptCollection.TFCPS.SCTaskRunnerServer import SCTaskRunnerServer

version = "1.2.6"
__version__ = version


def main() -> None:
    """Starts the macOS-task-runner. It builds operating-system-bound build-steps (e.g. flutter ios-builds) natively on this
    macOS-host on behalf of remote clients (see ScriptCollection's TFCPS_RemoteBuild). The required toolchain (e.g. flutter,
    Xcode) must be installed on this host. There is no container-variant because there are no macOS-containers and iOS-builds
    require the native macOS-toolchain. Configuration is read from environment-variables:
    - SCTaskRunner_Username / SCTaskRunner_Password: basic-auth-credentials the clients must use.
    - SCTaskRunner_Port: TCP-port to listen on (default 8080).
    - SCTaskRunner_CertificateFile / SCTaskRunner_CertificateKeyFile: when both are set the server is served over TLS
      (https); otherwise plain http is used (e.g. when TLS is terminated by a reverse-proxy in front of the runner)."""
    username = os.environ.get("SCTaskRunner_Username", "")
    password = os.environ.get("SCTaskRunner_Password", "")
    port = int(os.environ.get("SCTaskRunner_Port", "8080"))
    certificate_file = os.environ.get("SCTaskRunner_CertificateFile", None)
    certificate_key_file = os.environ.get("SCTaskRunner_CertificateKeyFile", None)
    SCTaskRunnerServer("MacOS", username, password).run(port=port, certificate_file=certificate_file, certificate_key_file=certificate_key_file)


if __name__ == "__main__":
    main()
