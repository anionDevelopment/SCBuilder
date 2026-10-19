import os
from ScriptCollection.TFCPS.SCTaskRunnerServer import SCTaskRunnerServer

version = "1.2.18"
__version__ = version


def get_required_environment_variable(name: str) -> str:
    """Returns the value of the given environment-variable. A variable which is not set or which is empty lets the start fail,
    because the runner would otherwise accept clients which do not know any credentials: the server compares the received
    credentials with "<username>:<password>", so empty credentials would mean that a client which sends ":" is accepted and
    can run arbitrary programs on this host."""
    value = os.environ.get(name, "")
    if value == "":
        raise ValueError(f"The environment-variable \"{name}\" must be set to a non-empty value.")
    return value


def main() -> None:
    """Starts the macOS-task-runner. It builds operating-system-bound build-steps (e.g. flutter macos-desktop-builds)
    natively on this macOS-host on behalf of remote clients (see ScriptCollection's TFCPS_RemoteBuild) that require
    RunnerOperatingSystem.MacOS. iOS-builds do not use this runner - they delegate to RunnerOperatingSystem.IOS, served by
    the dedicated SCTaskRunnerIOS-codeunit instead. The required toolchain (e.g. flutter, Xcode) must be installed on this
    host. There is no container-variant because there are no macOS-containers. Configuration is read from
    environment-variables:
    - SCTaskRunner_Username / SCTaskRunner_Password: basic-auth-credentials the clients must use (required).
    - SCTaskRunner_Port: TCP-port to listen on (default 8080).
    - SCTaskRunner_CertificateFile / SCTaskRunner_CertificateKeyFile: when both are set the server is served over TLS
      (https); when none of them is set plain http is used (e.g. when TLS is terminated by a reverse-proxy in front of the
      runner); setting only one of them lets the start fail instead of silently falling back to plain http."""
    username = get_required_environment_variable("SCTaskRunner_Username")
    password = get_required_environment_variable("SCTaskRunner_Password")
    port = int(os.environ.get("SCTaskRunner_Port", "8080"))
    certificate_file = os.environ.get("SCTaskRunner_CertificateFile", None)
    certificate_key_file = os.environ.get("SCTaskRunner_CertificateKeyFile", None)
    if (certificate_file is None) != (certificate_key_file is None):
        raise ValueError("The environment-variables \"SCTaskRunner_CertificateFile\" and \"SCTaskRunner_CertificateKeyFile\" must either both be set or both be not set.")
    SCTaskRunnerServer("MacOS", username, password).run(port=port, certificate_file=certificate_file, certificate_key_file=certificate_key_file)


if __name__ == "__main__":
    main()
