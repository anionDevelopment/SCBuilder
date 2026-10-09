import os
from ScriptCollection.TFCPS.SCTaskRunnerServer import SCTaskRunnerServer


version = "1.2.14"
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
    """Starts the Android-task-runner. It builds Android-app build-steps (e.g. flutter appbundle-builds) on behalf of
    remote clients (see ScriptCollection's TFCPS_RemoteBuild), using the Flutter-/Android-SDK-/NDK-toolchain that is
    installed in this container-image (see the Dockerfile). Unlike SCTaskRunnerWindows/SCTaskRunnerMacOS - which run
    natively because there are no Windows-/macOS-containers - this runner is delivered as a container: the Android-SDK
    works inside a Linux-container, so the container itself can just run permanently and accept jobs. Configuration is
    read from environment-variables:
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
    SCTaskRunnerServer("Android", username, password).run(port=port, certificate_file=certificate_file, certificate_key_file=certificate_key_file)


if __name__ == "__main__":
    main()
