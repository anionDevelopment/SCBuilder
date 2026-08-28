# Running the runner

Unlike `SCBuilder` (a one-shot image that runs `scbuildcodeunits` for the duration of a single build), SCTaskRunnerAndroid
is meant to run as a **permanently-running container** that waits for jobs sent by ScriptCollection's `TFCPS_RemoteBuild`
(see its remote-build-article for the client-side of the protocol).

## Configuration (environment-variables)

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

## Run as a long-lived container

```sh
docker run -d --name sctaskrunnerandroid --restart unless-stopped \
  -p 8080:8080 \
  -e SCTaskRunner_Username=runner \
  -e SCTaskRunner_Password=<secret> \
  sctaskrunnerandroid:latest
```

`--restart unless-stopped` keeps the runner available after a host-reboot or a crash, matching the "permanently running,
waits for jobs" model of `SCGitHubRunner`.

If TLS should be terminated by the container itself instead of by a reverse-proxy, mount the certificate/key and set
`SCTaskRunner_CertificateFile`/`SCTaskRunner_CertificateKeyFile` to their in-container paths:

```sh
docker run -d --name sctaskrunnerandroid --restart unless-stopped \
  -p 8443:8443 \
  -e SCTaskRunner_Port=8443 \
  -e SCTaskRunner_Username=runner \
  -e SCTaskRunner_Password=<secret> \
  -e SCTaskRunner_CertificateFile=/certs/runner.crt \
  -e SCTaskRunner_CertificateKeyFile=/certs/runner.key \
  -v /path/to/certs:/certs:ro \
  sctaskrunnerandroid:latest
```

## Make it reachable for the clients

Expose the runner to the clients (directly over TLS as configured above, or via an HTTPS-reverse-proxy). On the
client-side configure its URL and credentials in `~/.ScriptCollection/TFCPS/Runner.csv` (line `url;user;password`) or via
the `Runner_<name>_URL`/`_Username`/`_Password`-environment-variables.
