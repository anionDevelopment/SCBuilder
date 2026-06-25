# SCTaskRunnerWindows

SCTaskRunnerWindows provides an HTTP-server that builds operating-system-bound build-steps (for example flutter
`windows`-builds) **natively on a Windows-host** on behalf of remote clients.

It is the counterpart of ScriptCollection's `TFCPS_RemoteBuild`: a client (a developer-machine or the Debian-build-pipeline)
sends the whole repository as a tar-archive, this runner builds the requested step on Windows and returns the codeunit-folder.

## How it works
Per job the runner:
1. extracts the received repository-archive into a fresh, empty workspace (isolation),
2. runs the requested program (e.g. `flutter build windows`) on this Windows-host,
3. returns the codeunit-folder to the client,
4. deletes the workspace as soon as the client deletes the job (so no repository-content remains on the runner).

The actual server-logic lives in ScriptCollection (`ScriptCollection.TFCPS.SCTaskRunnerServer`); this codeunit is only the
thin Windows-entry-point.

## Requirements
- Python with the `scriptcollection`-package installed.
- The toolchain required by the delegated builds (e.g. flutter, Visual Studio build-tools, signing-tools).

## Run
The runner runs natively (no container - Flutter windows-desktop-builds require the native Windows-toolchain). Configuration
is read from environment-variables:

| Variable | Meaning | Default |
|---|---|---|
| `SCTaskRunner_Username` | Basic-auth-username the clients must use | (empty) |
| `SCTaskRunner_Password` | Basic-auth-password the clients must use | (empty) |
| `SCTaskRunner_Port` | TCP-port to listen on | `8080` |

```
set SCTaskRunner_Username=runner
set SCTaskRunner_Password=<secret>
python SCTaskRunnerWindows\SCTaskRunnerWindows.py
```

Expose the runner to the clients over HTTPS (e.g. via a reverse-proxy) and configure its URL/credentials on the client-side
(`~/.ScriptCollection/TFCPS/Runner.csv` or `Runner_<name>_URL`/`_Username`/`_Password`-environment-variables).
