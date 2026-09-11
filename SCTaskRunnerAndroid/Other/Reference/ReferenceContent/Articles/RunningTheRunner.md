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
| `SCTaskRunner_GradleMaxHeap` | Maximum heap of the gradle-build (see "Memory") | `2g` |
| `SCTaskRunner_GradleMaxMetaspace` | Maximum metaspace of the gradle-build (see "Memory") | `768m` |
| `SCTaskRunner_GradleMaxWorkers` | Maximum amount of gradle-worker-processes (see "Memory") | `2` |

`SCTaskRunner_Username` and `SCTaskRunner_Password` must be set. They are compared as one string `<username>:<password>`,
so leaving them at their (empty) default means that a client which sends exactly `:` as its credentials is accepted, which
is not a meaningful protection.

When both `SCTaskRunner_CertificateFile` and `SCTaskRunner_CertificateKeyFile` are set, the runner is served over **TLS
(https)** directly. Otherwise it is served over plain http - use this when TLS is terminated by a reverse-proxy in front of
the runner instead.

## Memory

The runner has a fixed memory-budget (the memory-limit of its container), while the repository it builds can not know on
which runner it will be built. The amount of memory a build may use is therefore configured **here** and not in the built
repository. This matters in practice: a flutter-project brings an `android/gradle.properties` generated from flutter's
template which requests 8 GiB of heap plus 4 GiB of metaspace. In a container with a smaller limit the kernel kills the
gradle-process while it builds, and gradle reports the very unspecific error
`Gradle build daemon disappeared unexpectedly (it may have been killed or may have crashed)`.

`EntryPoint.sh` therefore writes a `gradle.properties` into `$GRADLE_USER_HOME` on every container-start. Of the
`gradle.properties`-files gradle reads, that one has precedence over the one of the project, so it is the only place from
which flutter's template can be overruled without modifying the built repository. Besides the two memory-values it also
disables the gradle-daemon (a daemon which outlives a job would have its working-directory - the job-workspace - deleted
underneath it, and would keep its whole heap allocated while the runner packs the result-archive), disables parallel
project-execution and file-system-watching, and compiles kotlin in-process instead of in an own daemon-JVM.

The defaults fit into a container with **6 GiB**: about 3.3 GiB for the gradle-process (heap plus metaspace plus
code-cache and JVM-overhead), about 1 GiB for the dart-AOT-compiler which runs as part of the android-build, and the rest
for the server-process and headroom. Raise `SCTaskRunner_GradleMaxHeap` (and the container-limit with it) if a bigger app
runs out of heap; the symptom for that is a regular `OutOfMemoryError` of the build, not a disappeared process.

## Caches

Two folders are pure download-caches and should be mounted as volumes:

| Folder | Content |
|---|---|
| `/Caches/gradle` (`$GRADLE_USER_HOME`) | The gradle-distribution the project's gradle-wrapper asks for, plus all maven-dependencies of the android-build. |
| `/Caches/pub` (`$PUB_CACHE`) | The dart-/flutter-packages of the built app. |

They are not required for correctness - the caches also work while a container runs without them, because they live
outside the job-workspace which is deleted after every job. Without volumes they are lost whenever the container is
replaced (image-update, host-reboot), so the next build re-downloads several hundred megabytes, and they grow the writable
container-layer instead of a volume.

Use **named volumes**, not bind-mounts: a named volume is pre-filled from the image on first use, a bind-mount of an empty
host-folder would hide what the image brings.

`/tmp` is worth a volume too: the job-workspaces are created below `/tmp/SCTaskRunner`, so a running job holds the whole
repository of the client plus its complete build-output there.

## Logs

The runner writes its log to the console-output of the container (`docker logs sctaskrunnerandroid`), it does not write a
log-file. It logs:

| When | What |
|---|---|
| Start | That the runner starts and which work-folder it uses - logged before it binds its port, so a start which fails on its port or its certificate is visible too - and afterwards the address it listens on. |
| A job arrives | The job-id, the program with its arguments, the folder it runs in, the codeunit it belongs to, and how many bytes of repository-content were transferred. |
| A job is prepared | Which repository the job builds. This is taken from the `.git`-configuration of the transferred repository (which is transferred anyway), so it costs the client nothing; a credential which is part of that address is removed before it is logged. |
| Every 60 seconds | That a job is still running, since how long, and how many lines of output it has produced so far. A build produces its output for the client and not for the runner, so without this the log would state nothing for the whole duration of a build. |
| A job ends | Its state, its exitcode and how long it took. This is logged in any case - also when the client which submitted it is no longer connected, because a job keeps running when the connection to its client breaks. |
| A job failed | The last 25 lines of its output, so the log states why a build failed even when no client fetched that output. |
| Something went wrong inside the runner | The complete error including its stacktrace, under an error-id. |

The complete output of the built app is **not** part of this log: it belongs to the job and is fetched by the client,
which prints it as part of its own build-output.

## Which error reaches whom

The runner separates a build which does not work from a runner which does not work:

- **The app does not compile** (or its build fails for any other reason): that is what the client asked for, so its
  **complete output is transferred** and the client prints it. The job ends with the exitcode of the build.
- **The runner itself fails** (it can not extract the transferred repository, can not start the program, or any other
  unexpected error): the client only gets the statement that the runner failed plus an **error-id**, and a request which
  fails this way is answered with **500** without details. The details - stacktraces and paths inside the runner - are
  written to the log of the runner only, under that same error-id. They state something about the internals of the
  runner, which the one who waits for a build can not act on; the error-id is what brings both sides together.

This requires the `ScriptCollection`-version pinned in `Other/Resources/Dependencies/ScriptCollection/Version.txt` to be
`4.4.21` or newer. Older versions log nothing at all, because everything the server logs is logged as `Information` while
the default-loglevel of those versions discards that.

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

## Run with docker-compose behind a reverse-proxy

This is the recommended deployment when the runner is reachable from the internet: TLS and the credentials are handled by
the reverse-proxy, the runner itself is not published on the host at all.

`docker-compose.yml`:

```yaml
services:

  sctaskrunnerandroid:
    image: sctaskrunnerandroid:latest
    container_name: sctaskrunnerandroid
    restart: unless-stopped
    environment:
      SCTaskRunner_Username: ${SCTASKRUNNER_USERNAME:?set it in .env}
      SCTaskRunner_Password: ${SCTASKRUNNER_PASSWORD:?set it in .env}
      SCTaskRunner_Port: "8080"
    expose:
      - "8080"
    volumes:
      - sctaskrunner-work:/tmp
      - sctaskrunner-gradle:/Caches/gradle
      - sctaskrunner-pubcache:/Caches/pub
    networks:
      - runner-net
    # The defaults of SCTaskRunner_GradleMaxHeap/_GradleMaxMetaspace/_GradleMaxWorkers are sized for this limit; raise
    # both together, not just one of them.
    mem_limit: 6g
    pids_limit: 2048
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    healthcheck:
      # "/os" is the discovery-endpoint of the runner-protocol and the only endpoint which answers without a job; it
      # requires authentication like every other endpoint, hence the credentials.
      test: ["CMD-SHELL", "curl -fsS -u \"$$SCTaskRunner_Username:$$SCTaskRunner_Password\" http://127.0.0.1:8080/os || exit 1"]
      interval: 60s
      timeout: 10s
      retries: 3
      start_period: 30s

  reverseproxy:
    image: nginx:stable
    container_name: sctaskrunnerandroid-proxy
    restart: unless-stopped
    depends_on:
      - sctaskrunnerandroid
    ports:
      - "443:443"
    volumes:
      - ./nginx/SCTaskRunner.conf:/etc/nginx/conf.d/default.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    networks:
      - runner-net

networks:
  runner-net:

volumes:
  sctaskrunner-work:
  sctaskrunner-gradle:
  sctaskrunner-pubcache:
```

`.env` next to it:

```
SCTASKRUNNER_USERNAME=runner
SCTASKRUNNER_PASSWORD=<a long random password>
```

`nginx/SCTaskRunner.conf`:

```nginx
server {
    listen 443 ssl;
    http2 on;
    server_name runner.example.com;

    ssl_certificate     /etc/letsencrypt/live/runner.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/runner.example.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;

    # The client sends the complete repository (including .git and git-ignored files) as one request-body. The default of
    # 1m would reject every job with a 413 - and a client which is still sending usually sees that as a reset connection
    # instead of as a clean 413, so set this generously above the size of the largest repository. Do not set it to 0: it
    # is also the upper bound of what a single unauthorized request can make the runner write to its disk.
    client_max_body_size 16g;
    # Not the duration of the upload but the gap between two read-operations of the body, so this is what a stalling
    # connection runs into. The default of 60s is too low for an upload over a slow line.
    client_body_timeout  600s;
    # Gap between two write-operations towards the client, which applies to the (large) result-archive. Default is 60s.
    send_timeout 1800s;

    location / {
        # The runner runs the program a request names, so the credentials are the only thing between the internet and
        # code-execution on this machine. Restrict this further whenever the set of clients is known.
        # allow 203.0.113.10;
        # deny all;

        # The runner has no rate-limiting of its own. The limit has to stay above what a running build produces by
        # itself: while it waits for its job, the client asks for the state and for the log of that job once per
        # poll-interval (3 seconds by default), which is 40 requests per minute per running build - a lower limit makes
        # every build fail with a 429 as soon as the burst is used up.
        limit_req      zone=runner burst=20 nodelay;
        limit_req_status 429;

        proxy_pass http://sctaskrunnerandroid:8080;
        proxy_http_version 1.1;

        # Without proxy_request_buffering off, nginx writes the complete repository-archive to its own disk before it
        # forwards a single byte: that is an additional full write- and read-round over the whole size, the runner only
        # starts afterwards, and a disk which is too small for the archive ends the job with a 500. It requires
        # proxy_http_version 1.1 above.
        proxy_request_buffering off;
        proxy_buffering         off;

        # Packing the result-archive of a finished job takes a while and transports nothing in the meantime, so a low
        # read-timeout makes the client see a 504 for a build which actually succeeded. The client waits an hour for that
        # one request, so it is the proxy which decides here.
        proxy_read_timeout 1800s;
        proxy_send_timeout 1800s;

        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # The Authorization-header is passed on unchanged, so the runner checks the same credentials again.
    }
}
```

The `limit_req_zone` belongs into the `http`-block (`nginx.conf`):

```nginx
limit_req_zone $binary_remote_addr zone=runner:10m rate=2r/s;
```

`2r/s` is three times what one running build produces (see the comment at `limit_req` above), so a client can run a few
builds at the same time without being rate-limited, while the rate is still far below what is needed to submit jobs in
bulk.

Adding `auth_basic` in the reverse-proxy is possible, but with the same credentials it only checks what the runner checks
anyway - it is a second lock for the same key, not a second factor. An IP-allowlist, client-certificates or the
rate-limiting above protect against something the runner-credentials do not cover.

## Make it reachable for the clients

Expose the runner to the clients (directly over TLS as configured above, or via an HTTPS-reverse-proxy). On the
client-side configure its URL and credentials in `~/.ScriptCollection/TFCPS/Runner.csv` (line `url;user;password`) or via
the `Runner_<name>_URL`/`_Username`/`_Password`-environment-variables.

The prefix `Runner_` and the suffixes `_URL`/`_Username`/`_Password` are fixed; only the name in between is free. A build
which runs inside the SCBuilder-container can only use the environment-variables, because that container does not get the
configuration-folder mounted - declare their names in `<repository>/.ScriptCollection/ProductInformation.xml` below
`requiredenvironmentvariables` and put their values into `~/.ScriptCollection/TFCPS/EnvironmentVariables.csv`, so no
credential is part of a repository.
