# Installation as a background-service (Windows)

SCTaskRunnerWindows is delivered as a Python-wheel (`.whl`). On the Windows-host it is installed via `pip` and then run as a
background-service so it is always available to the remote clients (see ScriptCollection's `TFCPS_RemoteBuild`).

## 1. Prerequisites
- Python 3.11+ (with `pip`).
- The toolchain required by the delegated builds, e.g. Flutter and the Visual Studio build-tools (and any signing-tools).

## 2. Install the wheel
```
pip install SCTaskRunnerWindows-<version>-py3-none-any.whl
```
This also installs the `scriptcollection`-dependency and registers the console-command `sctaskrunnerwindows`
(in `<python>\Scripts\sctaskrunnerwindows.exe`), which starts the runner.

## 3. Configuration (environment-variables)

| Variable | Meaning | Default |
|---|---|---|
| `SCTaskRunner_Username` | Basic-auth-username the clients must use | (empty) |
| `SCTaskRunner_Password` | Basic-auth-password the clients must use | (empty) |
| `SCTaskRunner_Port` | TCP-port to listen on | `8080` |
| `SCTaskRunner_CertificateFile` | Path to the TLS-certificate-file | (none) |
| `SCTaskRunner_CertificateKeyFile` | Path to the TLS-certificate-key-file | (none) |

When both `SCTaskRunner_CertificateFile` and `SCTaskRunner_CertificateKeyFile` are set, the runner is served over **TLS
(https)** directly. Otherwise it is served over plain http - use this when TLS is terminated by a reverse-proxy in front of
the runner instead.

## 4. Run as a background-service

The runner is run **natively** (no container - flutter windows-desktop-builds require the native Windows-toolchain).

Note: `sctaskrunnerwindows` is a plain console-program, not a Windows-service itself (it does not talk to the
Service-Control-Manager). Therefore it must **not** be registered directly with `sc.exe create` (that would fail to start).
Use one of the following instead.

### Option A: Task Scheduler (built-in, recommended)
Task Scheduler ships with Windows. It can start the console-command at system-startup and restart it if it stops - no
third-party tool required.

Because a scheduled-task has no per-task environment-block, put the configuration into a small wrapper `run-runner.cmd`:
```bat
@echo off
set SCTaskRunner_Username=runner
set SCTaskRunner_Password=<secret>
set SCTaskRunner_Port=8080
set SCTaskRunner_CertificateFile=C:\certs\runner.crt
set SCTaskRunner_CertificateKeyFile=C:\certs\runner.key
"C:\Path\To\Python\Scripts\sctaskrunnerwindows.exe"
```
Register it to run at startup as the SYSTEM-account:
```
schtasks /Create /TN "SCTaskRunnerWindows" /TR "C:\path\to\run-runner.cmd" /SC ONSTART /RU SYSTEM /RL HIGHEST /F
```
To auto-restart it if it ever exits, open the task in the Task-Scheduler-UI → tab *Settings* → enable
"If the task fails, restart every: 1 minute" (and optionally "If the running task does not end when requested, force it to
stop").

### Option B: WinSW (actively-maintained third-party service-wrapper)
If you prefer a *real* Windows-service, use [WinSW](https://github.com/winsw/winsw) (actively maintained). Place `WinSW.exe`
next to a config-file `SCTaskRunnerWindows.xml` (WinSW supports a per-service environment-block, so no machine-wide variables
are needed):
```xml
<service>
  <id>SCTaskRunnerWindows</id>
  <name>SCTaskRunnerWindows</name>
  <description>Builds operating-system-bound build-steps on this Windows-host.</description>
  <executable>C:\Path\To\Python\Scripts\sctaskrunnerwindows.exe</executable>
  <env name="SCTaskRunner_Username" value="runner"/>
  <env name="SCTaskRunner_Password" value="&lt;secret&gt;"/>
  <env name="SCTaskRunner_Port" value="8080"/>
  <env name="SCTaskRunner_CertificateFile" value="C:\certs\runner.crt"/>
  <env name="SCTaskRunner_CertificateKeyFile" value="C:\certs\runner.key"/>
  <onfailure action="restart"/>
</service>
```
Then install and start the service:
```
WinSW.exe install
WinSW.exe start
```

## 5. Make it reachable for the clients
Expose the runner to the clients (directly over TLS as configured above, or via an HTTPS-reverse-proxy). On the client-side
configure its URL and credentials in `~/.ScriptCollection/TFCPS/Runner.csv` (line `url;user;password`) or via the
`Runner_<name>_URL`/`_Username`/`_Password`-environment-variables.
