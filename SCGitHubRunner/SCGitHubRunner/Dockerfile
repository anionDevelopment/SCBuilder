ARG image_debian
FROM ${image_debian}
ARG CodeUnitVersion
ARG GitHubRunnerVersion
ARG ContainerHooksDockerVersion
# TargetArch is the actions-runner archive-suffix ("x64" for amd64, "arm64" for arm64).
ARG TargetArch=x64
LABEL version=${CodeUnitVersion}
ENV ISRUNNINGINCONTAINER="true"
# The runner-agent runs as root inside this container; allow it explicitly.
ENV RUNNER_ALLOW_RUNASROOT="1"
# Default installation/run-directory of the runner. Override via the RUNNER_HOME env-variable
# and bind-mount that same path host-identically so the nested /__e mount works.
ENV RUNNER_HOME="/home/runner"

#basic tooling required by the runner-agent and the entrypoint
RUN apt-get update && \
    apt-get install -y curl ca-certificates git jq gnupg tar unzip && \
    rm -rf /var/lib/apt/lists/*

#docker-cli: the runner needs it to start the job-container on the host-daemon (via the mounted docker.sock)
RUN install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg && \
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce-cli docker-buildx-plugin docker-compose-plugin && \
    rm -rf /var/lib/apt/lists/*

#download the runner-agent into a template-location; the entrypoint copies it into RUNNER_HOME at start
RUN mkdir -p /opt/runner-template && \
    cd /opt/runner-template && \
    curl -fL -o runner.tar.gz "https://github.com/actions/runner/releases/download/v${GitHubRunnerVersion}/actions-runner-linux-${TargetArch}-${GitHubRunnerVersion}.tar.gz" && \
    tar xzf runner.tar.gz && \
    rm runner.tar.gz && \
    ./bin/installdependencies.sh && \
    rm -rf /var/lib/apt/lists/*

#container-hooks: lets ACTIONS_RUNNER_CONTAINER_HOOKS (set below) customize how the runner creates a job-container,
#without a repository having to change its workflow. The official docker-hook-implementation is downloaded as-is
#(runner-agent already provides the node20 it is executed with, see /opt/runner-template above) and PrepareJobMountHook.js
#wraps it: it only adds a mount (configured via SCRIPTCOLLECTION_CONFIGURATION_FOLDER, see Usage.md) and
#otherwise behaves exactly like the wrapped hook.
RUN mkdir -p /opt/container-hooks/docker && \
    cd /opt/container-hooks/docker && \
    curl -fL -o hooks.zip "https://github.com/actions/runner-container-hooks/releases/download/v${ContainerHooksDockerVersion}/actions-runner-hooks-docker-${ContainerHooksDockerVersion}.zip" && \
    unzip -q hooks.zip && \
    rm hooks.zip
COPY SCGitHubRunner/ContainerHooks/PrepareJobMountHook.js /opt/container-hooks/PrepareJobMountHook.js
ENV ACTIONS_RUNNER_CONTAINER_HOOKS="/opt/container-hooks/PrepareJobMountHook.js"

COPY SCGitHubRunner/EntryPoint.sh /EntryPoint.sh
RUN chmod +x /EntryPoint.sh

ENTRYPOINT ["/EntryPoint.sh"]
