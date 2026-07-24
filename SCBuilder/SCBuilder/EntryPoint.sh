#!/bin/bash

# Ensure a multi-platform-capable buildx builder ("docker-container" driver) is selected before the actual
# command runs. Without this, containers started from this image fall back to whatever buildx builder is
# selected on the host docker-daemon that this image's docker.sock is mounted from (usually "default"/
# "desktop-linux", the classic "docker" driver), which needs the host-daemon to have QEMU/binfmt handlers
# registered for the target platform. The "docker-container" driver bundles/bootstraps its own emulation and
# does not depend on that host-state. The builder can not be created at image-build-time (docker buildx create
# needs a reachable docker-daemon, which is not available during "docker build"), so this happens here instead,
# once per container-start.
docker buildx inspect scbuilder >/dev/null 2>&1 || docker buildx create --name scbuilder --driver docker-container --use >/dev/null 2>&1
docker buildx use scbuilder >/dev/null 2>&1

exec "$@"
