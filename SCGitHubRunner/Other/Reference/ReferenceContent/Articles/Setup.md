# Setup

Step-by-step guide to set up an SCGitHubRunner-based self-hosted runner. For the meaning of the environment-variables and how the `/__e` / `/__w` / `/__t` mounts work, see [Usage](./Usage.md).

## 1. Prerequisites

On the host that will run the runner:

- A running Docker-daemon (the runner starts the job-containers on it).
- Network-access to `github.com` and the registry that holds the runner- and job-images.
- A directory on the host for each runner (the host-identical `RUNNER_HOME`), e.g. `/Workspace/Other/Runner/MyRunner`.

For the workflow you also need the job-image available (e.g. `aniondev/scbuilder:<tag>`).

## 2. Build / obtain the runner-image

Build the codeunit from the repository-root:

```bash
task bb
```

(or only this codeunit by running `Build.py` in `SCGitHubRunner/Other/Build`). This produces the image `aniondev/scgithubrunner:<version>`. Make it available on the host either by pushing it to your registry and pulling it there, or by building it on the host directly.

To pin / update the bundled runner-agent version, edit
`SCGitHubRunner/Other/Resources/Dependencies/GitHubRunner/Version.txt`
and rebuild. The value must be an existing [actions/runner release](https://github.com/actions/runner/releases).

## 3. Create a token

The runner registers with the GitHub-organization. Two options:

- **Personal-access-token (recommended for permanent runners)** — set as `ACCESS_TOKEN`. The entrypoint fetches a fresh registration-token from it on every (re)configuration, so it survives restarts and re-registrations.
  - Classic PAT: scope `admin:org`.
  - Fine-grained PAT: organization-permission *Self-hosted runners* = read & write.
- **Registration-token** — set as `RUNNER_TOKEN`. Quick for a one-off test, but it expires after ~1 hour (Org → Settings → Actions → Runners → *New runner*).

## 4. Prepare the host-directory

```bash
sudo mkdir -p /Workspace/Other/Runner/MyRunner
```

It may stay empty — on first start the runner-binaries are copied into it from the image, and the registration then persists here across restarts.

## 5. Create the compose-file

`docker-compose.yml` on the host:

```yaml
services:
  myrunner:
    image: aniondev/scgithubrunner:latest
    container_name: myrunner
    environment:
      ORG_NAME: anionDevelopment
      ACCESS_TOKEN: <github-personal-access-token>   # or: RUNNER_TOKEN: <registration-token>
      RUNNER_NAME: myrunner
      LABELS: self-hosted,scriptcollection
      RUNNER_HOME: /Workspace/Other/Runner/MyRunner
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      # host-identical (Host == Container) and unique per runner:
      - /Workspace/Other/Runner/MyRunner:/Workspace/Other/Runner/MyRunner
```

## 6. Start and verify the registration

```bash
docker compose up -d
docker compose logs -f myrunner
```

In the logs you should see the runner configure itself and then `Listening for Jobs`. In GitHub (Org → Settings → Actions → Runners) the runner `myrunner` appears with status *Idle* and the label `scriptcollection`.

## 7. Verify a job runs (the /__e fix)

Trigger a workflow that targets this runner and uses a job-container:

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

`actions/checkout` must now run through without the `/__e/node20/bin/node: no such file or directory` error.

## 8. Add more runners

Copy the service-block, give it a unique `RUNNER_NAME`, `RUNNER_HOME` and host-identical volume (e.g. `/Workspace/Other/Runner/MyRunner2`). Any number of runners can run in parallel because each owns its own directory.

## 9. Decommission a previous runner

When replacing an old runner (e.g. a `myoung34/github-runner`):

```bash
docker compose -f <old-compose> down
```

Then remove it in GitHub (Org → Settings → Actions → Runners → *Remove*), especially if the new runner reuses the same name. (With `--replace`, SCGitHubRunner re-registers a same-named runner automatically.)

## 10. Updating

- **Runner-agent**: bump `GitHubRunner/Version.txt`, rebuild the image, then on the host `docker compose pull && docker compose up -d`. The host-`RUNNER_HOME` keeps the old binaries until you let the new container repopulate it (remove the binaries in `RUNNER_HOME` or use a fresh directory if you want a clean upgrade).
- **Job-image (scbuilder)**: just change the `container.image` tag in the workflow.

## Troubleshooting

- **`/__e/node20/bin/node: no such file or directory`** → `RUNNER_HOME` is not bind-mounted host-identically (Host path must equal container path). Check the `volumes` entry.
- **Runner does not appear in GitHub** → check `ORG_NAME` and the token/scopes; see `docker compose logs`.
- **`Must not run with sudo` / runs-as-root error** → the image sets `RUNNER_ALLOW_RUNASROOT=1`; do not override it.
- **Cannot pull the private job-image** → the host-daemon needs credentials (`docker login` on the host or `container.credentials` in the workflow).
