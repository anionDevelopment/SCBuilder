# Troubleshooting: "Docker exporter is not supported for the docker driver"

## Symptom

A codeunit-build that produces an OCI-image-artifact fails while exporting the image to a `.tar`. The build runs a `docker buildx build … --output type=docker,dest=…/<CodeUnit>_v<Version>_<Platform>.tar` and aborts with:

```
ERROR: failed to build: Docker exporter is not supported for the docker driver.
Switch to a different driver, or turn on the containerd image store, and try again.
Learn more at https://docs.docker.com/go/build-exporters/
```

This typically appears right after the Docker environment on the build-host was reset (for example after deleting and recreating containers, images and networks).

## Cause

The `type=docker` exporter (writing the built image into a `.tar`) is only supported by buildx's default `docker` driver when the **containerd image store** is enabled in the daemon. Without it, the exporter is unavailable and the build fails.

This is not a problem in the codeunit, in ScriptCollection or in the SCBuilder/SCGitHubRunner image. The `docker buildx build`-command is correct. The builds run against the **host Docker daemon** (the runner only mounts the host's `docker.sock`), so the relevant configuration lives on that host daemon — outside of any of these repositories.

The error usually surfaces because a previously working state was lost: either the containerd image store was enabled in the daemon and got reset on a daemon restart/reinstall, or an active `docker-container`-driver buildx-builder was removed so buildx fell back to the default `docker` driver.

## Fix (recommended): enable the containerd image store on the host

This is a daemon-level setting and therefore survives recreating containers, images and networks. Add to `/etc/docker/daemon.json` on the build-host:

```json
{
  "features": { "containerd-snapshotter": true }
}
```

If the file already contains other keys, only add the `features`-entry (keep the existing content). Then restart the daemon:

```sh
systemctl restart docker
```

Verify with `docker info`: the storage driver should now report containerd (for example `overlayfs` with the containerd snapshotter). Afterwards the `type=docker`-export works again with the default driver, and no buildx-builder needs to be maintained.

## Alternative: use a `docker-container`-driver builder

Use this only if the containerd image store must not be enabled globally. The `docker-container` driver supports the `type=docker`-tar-export without changing the daemon:

```sh
docker buildx create --name scbuilder --driver docker-container --use
docker buildx inspect --bootstrap
```

Notes:

- A buildx-builder is registered CLI-side in `$HOME/.docker/buildx` of whoever runs `docker buildx build`. It must therefore be created **in the same environment from which the build is invoked** (the runner/job environment), not only on the bare host — otherwise the build's CLI does not see it.
- The BuildKit instance itself (a `buildx_buildkit_scbuilder0`-container) runs on the daemon the socket points to, i.e. the host daemon.
- If that environment is ephemeral, the builder-registration is lost on recreation and the same error returns after the next reset. For this reason the containerd-image-store fix above is the more robust choice for runner-based builds.
- `docker buildx inspect --bootstrap` starts the BuildKit instance immediately (pulling the `moby/buildkit`-image and booting the `buildx_buildkit_*`-container) and waits until it is ready, instead of starting it lazily on the first build. This is optional but surfaces setup errors (image-pull, network, permissions) up front.

### How to tell the builder is healthy

In the `docker buildx inspect --bootstrap`-output, three lines confirm the setup is correct:

- `Driver: docker-container` — the driver that supports the `type=docker`-export (the default `docker` driver would not).
- `Status: running` — the BuildKit instance booted and is ready.
- `Platforms: linux/amd64, …` — the target-platform of the build (the codeunit-builds use `linux/amd64`) is listed.

If all three are present, the export-error is resolved and the build can produce the `.tar`.
