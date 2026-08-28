# SCTaskRunnerAndroid

![Development-state](https://img.shields.io/badge/development--state-active%20development-brightgreen)
![License](https://img.shields.io/badge/license-GPLv3-blue)

## General

SCTaskRunnerAndroid provides an HTTP-server that builds Android-app build-steps (for example flutter `appbundle`-builds) on
behalf of remote clients, using the Android-SDK/NDK/Flutter-toolchain contained in this image.

It is the counterpart of ScriptCollection's `TFCPS_RemoteBuild`: a client (a developer-machine or the Debian-build-pipeline)
sends the whole repository as a tar-archive, this runner builds the requested step and returns the codeunit-folder.

Unlike `SCTaskRunnerWindows`/`SCTaskRunnerMacOS` (which run natively, because there are no Windows-/macOS-containers),
`SCTaskRunnerAndroid` runs as a **container**: the Android-SDK/NDK works inside a Linux-container, so this image is meant to
run as a permanently-running container that waits for jobs (analogous in spirit to how `SCGitHubRunner` is a
permanently-running container), instead of as a one-shot build-image like `SCBuilder`.

Besides the name, this codeunit is built exactly like `SCBuilder` (same kind of Dockerfile, same
dependency-definition-/build-/update-scripts), but it only contains what is required to build Android-apps: Flutter, the
Android-SDK/NDK, the JRE the Android-Gradle-Plugin needs, and ScriptCollection (to run the server itself). Everything else
SCBuilder contains (dotnet, node, rust, go, docker, the ai-clis, ...) is deliberately not part of this image.

## How it works

Per job the runner:
1. extracts the received repository-archive into a fresh, empty workspace (isolation),
2. runs the requested program (e.g. `flutter build appbundle`) inside this container,
3. returns the codeunit-folder to the client,
4. deletes the workspace as soon as the client deletes the job (so no repository-content remains on the runner).

The actual server-logic lives in ScriptCollection (`ScriptCollection.TFCPS.SCTaskRunnerServer`); this codeunit only adds the
Android-toolchain (see [SCTaskRunnerAndroid/Dockerfile](./SCTaskRunnerAndroid/Dockerfile)) and the thin Android-entry-point
(`SCTaskRunnerAndroidCore.py`).

## Build

This product requires to use `scbuildcodeunits` implemented/provided by [ScriptCollection](https://github.com/anionDev/ScriptCollection) to build the project.

## Run

Run the built image as a long-lived container. Configuration is read from environment-variables:

| Variable | Meaning | Default |
|---|---|---|
| `SCTaskRunner_Username` | Basic-auth-username the clients must use | (empty) |
| `SCTaskRunner_Password` | Basic-auth-password the clients must use | (empty) |
| `SCTaskRunner_Port` | TCP-port to listen on | `8080` |
| `SCTaskRunner_CertificateFile` | Path to the TLS-certificate-file | (none) |
| `SCTaskRunner_CertificateKeyFile` | Path to the TLS-certificate-key-file | (none) |

```
docker run -d --name sctaskrunnerandroid --restart unless-stopped \
  -p 8080:8080 \
  -e SCTaskRunner_Username=runner \
  -e SCTaskRunner_Password=<secret> \
  sctaskrunnerandroid:latest
```

When both `SCTaskRunner_CertificateFile` and `SCTaskRunner_CertificateKeyFile` are set, the runner is served over **TLS
(https)** directly. Otherwise it is served over plain http - use this when TLS is terminated by a reverse-proxy in front of
the runner instead.

Expose the runner to the clients (directly over TLS as configured above, or via an HTTPS-reverse-proxy). On the client-side
configure its URL and credentials in `~/.ScriptCollection/TFCPS/Runner.csv` (line `url;user;password`) or via the
`Runner_<name>_URL`/`_Username`/`_Password`-environment-variables.

## Contribute

Contributions are always welcome.
