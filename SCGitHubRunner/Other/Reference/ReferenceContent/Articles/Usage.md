# Usage

SCGitHubRunner is a slim, permanently running self-hosted GitHub-Actions-runner. It starts a separate job-container (for example the `SCBuilder` image) per job — the "GitLab-style" model.

## Why a custom image is needed

When a job uses `jobs.<id>.container.image`, the runner mounts its own directories into the job-container, among them `externals` (which contains node20) at `/__e`. JavaScript-actions like `actions/checkout` are executed with `/__e/node20/bin/node` — **not** with any node installed in the job-image.

If the runner itself runs in a container, it asks the **host** docker-daemon to bind-mount `<runner>/externals` into the job-container. The host resolves that source-path on the **host** filesystem. So the runner's `externals` directory must exist on the host under the **exact same absolute path** the runner sees inside its container — otherwise `/__e` is empty and you get:

```
exec: "/__e/node20/bin/node": stat /__e/node20/bin/node: no such file or directory
```

Common runner-images (`myoung34/github-runner`, the official `actions/runner` image) hardcode the runner-directory (`/actions-runner`, `/home/runner`), which makes it impossible to keep it host-identical **and** unique per runner. SCGitHubRunner installs and runs the runner from a configurable `RUNNER_HOME`, so you can give each runner its own host-identical directory.

## Environment-variables

| Variable | Required | Description |
|---|---|---|
| `ORG_NAME` | yes | GitHub-organization the runner registers to (`https://github.com/<ORG_NAME>`). |
| `RUNNER_HOME` | yes (for container-jobs) | Install/run-directory of the runner. **Must be bind-mounted host-identically.** |
| `ACCESS_TOKEN` | one of | Personal-access-token; a registration-token is fetched from it on demand (recommended for permanent runners). |
| `RUNNER_TOKEN` | one of | Registration-token directly (expires after ~1h). |
| `RUNNER_NAME` | no | Runner-name (defaults to the container-hostname). Must be unique. |
| `LABELS` | no | Comma-separated runner-labels (defaults to `self-hosted`). |
| `RUNNER_WORKDIR` | no | Work-directory; relative to `RUNNER_HOME` by default (`_work`). |
| `EPHEMERAL` | no | `true` registers the runner as ephemeral and deregisters it on exit. |
| `REMOVE_ON_EXIT` | no | `true` deregisters the runner on container-stop. |
| `SCRIPTCOLLECTION_CONFIGURATION_FOLDER` | no | Host-absolute path of a ScriptCollection-configuration-folder (containing `TFCPS/EnvironmentVariables.csv`); if set, it is bind-mounted read-only into every job-container this runner starts. See [Container-hooks](#container-hooks) below. |
| `SCRIPTCOLLECTION_CONFIGURATION_FOLDER_TARGET` | no | Target-path of the mount above inside the job-container. Defaults to `/root/.ScriptCollection` (the SCBuilder-image runs as `root`). |

## docker-compose

```yaml
services:
  myrunner:
    image: aniondev/scgithubrunner:v1.0.0
    container_name: myrunner
    restart: unless-stopped
    environment:
      ORG_NAME: anionDevelopment
      ACCESS_TOKEN: <github-personal-access-token>   # or: RUNNER_TOKEN: <registration-token>
      RUNNER_NAME: myrunner
      LABELS: self-hosted,scriptcollection
      RUNNER_HOME: /Workspace/Other/Runner/MyRunner
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      # host-identical (Host == Container) and unique per runner -> /__e resolves correctly:
      - /Workspace/Other/Runner/MyRunner:/Workspace/Other/Runner/MyRunner
```

For a second runner, copy the service and change `RUNNER_NAME`, `RUNNER_HOME` and the host-identical volume to a different unique directory (e.g. `.../MyRunner2`). Each runner gets its own directory, so there are no path-collisions and any number of runners can run in parallel.

## What is (and is not) needed for full runner-features

The two mounts above are sufficient for the core feature-set, because **everything the runner mounts into job- and service-containers lives under `RUNNER_HOME`**, which is already host-identical:

- `externals` → `/__e` (node20 for JavaScript-actions),
- `_work` → `/__w` (the workspace / checkout; the temp-directory `_work/_temp` lives inside it),
- the tool-cache → `/__t` (used by `actions/setup-*`; default `_work/_tool`).

These three container-paths are hardcoded in the runner-source (`Runner.Worker/Container/ContainerInfo.cs`, mapping the well-known `Work`/`Tools`/`Externals` directories); they are not configurable.

So **container-jobs, service-containers (`services:`), the tool-cache, `actions/checkout` and `actions/upload-artifact` all work without additional mounts.**

### Optional additions (only when you need them)

- **Private job-image**: if the job-`container.image` is private, the **host** docker-daemon must be able to pull it. Either `docker login` once on the host, or provide `container.credentials` in the workflow. This is not a compose-mount.
- **Custom tool-cache path**: only if you set `AGENT_TOOLSDIRECTORY`/`RUNNER_TOOL_CACHE` to a path *outside* `RUNNER_HOME` — then that path also needs a host-identical mount.
- **Time zone / locale**: add `TZ: Europe/Berlin` to `environment` for consistent timestamps in logs.
- **Private CA / corporate proxy**: mount CA-certs and set `HTTP_PROXY`/`HTTPS_PROXY`/`NODE_EXTRA_CA_CERTS` if your network requires it.
- **Resource-limits**: `cpus`/`mem_limit` (or compose `deploy.resources`) if you want to cap a runner.

## Container-hooks

SCGitHubRunner bundles the official [docker container-hook](https://github.com/actions/runner-container-hooks) and sets `ACTIONS_RUNNER_CONTAINER_HOOKS` to a thin wrapper around it (`PrepareJobMountHook.js`), so every job-container this runner starts goes through it - this is what makes `SCRIPTCOLLECTION_CONFIGURATION_FOLDER` (see the table above) work without a repository having to add a mount to its own workflow. The wrapper only inspects the `prepare_job`-command and otherwise delegates unchanged to the wrapped hook, so it does not change the runner's behavior for a repository which does not use `SCRIPTCOLLECTION_CONFIGURATION_FOLDER`.

```yaml
services:
  myrunner:
    image: aniondev/scgithubrunner:v1.0.0
    environment:
      # ...ORG_NAME, ACCESS_TOKEN, RUNNER_NAME, LABELS, RUNNER_HOME as above...
      SCRIPTCOLLECTION_CONFIGURATION_FOLDER: /srv/ScriptCollectionConfiguration
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /Workspace/Other/Runner/MyRunner:/Workspace/Other/Runner/MyRunner
```

`SCRIPTCOLLECTION_CONFIGURATION_FOLDER` must name the path exactly as it exists **on the runner-host** (the machine running the docker-daemon this runner talks to through the mounted `docker.sock`), the same rule `RUNNER_HOME` already follows - not a path inside this runner-container. Mounting that same folder into the runner-container as well (as described for the docker-executor in the "Build-runner-configuration"-article of the ScriptCollection-repository) is not required for this mechanism (the runner-container itself never reads the folder's content), but is harmless and can help when verifying the setup, for example with `docker compose exec myrunner ls /srv/ScriptCollectionConfiguration`.

To provide credentials for one specific runner only (rather than for every runner on the host), give that runner its own `SCRIPTCOLLECTION_CONFIGURATION_FOLDER` (a folder unique to it, not shared with other runners) instead of changing the image or `PrepareJobMountHook.js`.

If you need to customize a job-container further, replace `PrepareJobMountHook.js` with your own hook (or fork [runner-container-hooks](https://github.com/actions/runner-container-hooks)) and point `ACTIONS_RUNNER_CONTAINER_HOOKS` at it instead, either by building a custom image on top of this one or by overriding the environment-variable in the compose-file.

## Workflow

The workflow keeps the job-container — `SCGitHubRunner` only runs the runner, the build-tools live in the job-image:

```yaml
jobs:
  run-script:
    runs-on: [self-hosted, scriptcollection]
    container:
      image: aniondev/scbuilder:v1.0.0
      volumes:
        - /var/run/docker.sock:/var/run/docker.sock
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - run: scpreparebuildpipelineforgitlab
      - run: scbuildcodeunits -v 4
```

## Notes

- `RUNNER_HOME` is populated from the image's bundled runner-binaries on first start; the registration persists in that (host-mounted) directory across container-restarts.
- The runner needs the docker-socket to start the job-container, hence the `docker.sock` mount.
- If the build itself runs `docker run -v <workspace-path>:...` (bind-mounts, e.g. for local test-services), the same host-path-resolution applies to those paths; `docker build` is unaffected because it streams its context.
