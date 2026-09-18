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

# Run the script which the environment-variable "CustomScriptPath" states, if it states one. This is the hook with
# which the start of a container can be extended (a registry-login, a certificate, a mounted tool) without building an
# own image on top of this one. It runs before the actual command, so that command already sees what the script set up.
# A stated path which does not exist and a script which fails are both a defect of the setup of the container and not
# something this image can compensate: the command would run in an environment which was not prepared, without anybody
# noticing it. The container-start therefore fails instead of continuing. A failed script ends the container-start with
# its own exit-code, so the reason why it failed stays visible to whoever started the container.
# The script is run by bash and not executed directly, because the file which this variable states is usually
# bind-mounted into the container and a bind-mounted file does not necessarily carry the executable-bit; executing it
# directly would let a file which exists (which is the condition stated here) fail with "Permission denied".
if [ -n "${CustomScriptPath}" ]; then
  if [ -f "${CustomScriptPath}" ]; then
    echo "Running the custom-script \"${CustomScriptPath}\"."
    bash "${CustomScriptPath}"
    CustomScriptExitCode=$?
    if [ "${CustomScriptExitCode}" -ne 0 ]; then
      echo "The custom-script \"${CustomScriptPath}\" failed with exit-code ${CustomScriptExitCode}." >&2
      exit "${CustomScriptExitCode}"
    fi
  else
    echo "The environment-variable \"CustomScriptPath\" states the file \"${CustomScriptPath}\", but that file does not exist." >&2
    exit 1
  fi
fi

exec "$@"
