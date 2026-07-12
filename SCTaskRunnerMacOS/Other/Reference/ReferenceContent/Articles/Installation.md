# Installation as a background-service (macOS)

SCTaskRunnerMacOS is delivered as a Python-wheel (`.whl`). On the macOS-host it is installed via `pip` and then run as a
background-service (a `launchd`-daemon) so it is always available to the remote clients (see ScriptCollection's
`TFCPS_RemoteBuild`).

## 1. Prerequisites
- Python 3.11+ (with `pip3`).
- The toolchain required by the delegated builds, e.g. Flutter and Xcode.

## 2. Install the wheel
```
pip3 install SCTaskRunnerMacOS-<version>-py3-none-any.whl
```
This also installs the `scriptcollection`-dependency and registers the console-command `sctaskrunnermacos`, which starts the
runner. Note the absolute path of the command (e.g. via `which sctaskrunnermacos`) - it is needed for the launchd-daemon.

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

## 4. Run as a background-service (launchd)

The runner is run **natively** - there is no container-variant, because there are no macOS-containers and iOS-builds require
the native macOS-toolchain.

Create the daemon-definition `/Library/LaunchDaemons/com.aniondev.sctaskrunnermacos.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aniondev.sctaskrunnermacos</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/sctaskrunnermacos</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>SCTaskRunner_Username</key>
        <string>runner</string>
        <key>SCTaskRunner_Password</key>
        <string>&lt;secret&gt;</string>
        <key>SCTaskRunner_Port</key>
        <string>8080</string>
        <key>SCTaskRunner_CertificateFile</key>
        <string>/etc/sctaskrunner/runner.crt</string>
        <key>SCTaskRunner_CertificateKeyFile</key>
        <string>/etc/sctaskrunner/runner.key</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/var/log/sctaskrunnermacos.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/sctaskrunnermacos.log</string>
</dict>
</plist>
```

Adjust the path in `ProgramArguments` to the actual location of the `sctaskrunnermacos`-command (`which sctaskrunnermacos`).
Then load and start it:
```
sudo launchctl load /Library/LaunchDaemons/com.aniondev.sctaskrunnermacos.plist
```

## 5. Make it reachable for the clients
Expose the runner to the clients (directly over TLS as configured above, or via an HTTPS-reverse-proxy). On the client-side
configure its URL and credentials in `~/.ScriptCollection/TFCPS/Runner.csv` (line `url;user;password`) or via the
`Runner_<name>_URL`/`_Username`/`_Password`-environment-variables.
