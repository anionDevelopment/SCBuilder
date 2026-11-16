ARG image_debian
FROM ${image_debian}
ARG CodeUnitVersion
ARG DotNetRuntime
ARG PipIndexUrlArguments
ARG GoVersion
ARG PlatformForGoVersion
ARG JavaVersion
ARG JavaBuildVersion
ARG PlatformForJavaVersion=x64
ARG NodeVersion
# Exact debian-package-version of chromium (used for the headless browser-based frontend-tests), passed in from
# Other/Resources/Dependencies/Chromium/Version.txt. Pinned so that the image always contains a chromium-build which is
# known to work. Not every published build does: 150.0.7871.46-1~deb13u1 for example terminated with SIGTRAP directly
# during the startup, which made every karma-testrun fail with "Cannot start ChromeHeadless". Raise this value in that
# Version.txt only to a build which passes the chromium-smoke-test below.
# The pin has to be raised whenever debian publishes a new chromium-build: the debian-mirror carries exactly one
# chromium-version per suite, so a superseded version is removed permanently (it only remains on snapshot.debian.org)
# and apt then fails with "E: Version '<pinned version>' for 'chromium' was not found". The current version of the suite
# of the base-image is listed at https://packages.debian.org/chromium.
ARG ChromiumVersion
ARG DotNetSdkVersion
ARG EpewVersion
ARG GitVersionToolVersion
ARG ReportGeneratorVersion
ARG DocFxVersion
ARG DotNetT4Version
ARG CycloneDxVersion
ARG SwashbuckleVersion
ARG RustVersion
ARG CargoCycloneDxVersion
ARG CargoLlvmCovVersion
ARG AngularCliVersion
ARG GoTaskVersion
ARG PnpmVersion
ARG TypeScriptVersion
ARG EslintVersion
ARG PrettierVersion
ARG VegaVersion
ARG VegaCliVersion
ARG VegaLiteVersion
ARG VegaEmbedVersion
ARG CycloneDxNpmVersion
ARG PlaywrightVersion
ARG GulpCliVersion
ARG JqVersion
ARG YqVersion
ARG ShellCheckVersion
ARG GitLfsVersion
ARG GitHubCliVersion
ARG GitLabCliVersion
ARG KubectlVersion
ARG HelmVersion
ARG KustomizeVersion
ARG AzureCliVersion
ARG FlutterVersion
ARG ScriptCollectionVersion
ARG ClaudeCodeVersion
ARG CodexVersion
ARG CopilotVersion
ARG GeminiCliVersion
ARG CursorCliVersion
ARG OpenSpecVersion
ARG OpenCodeVersion
ARG MistralVibeVersion
ARG UpgradeScriptCollection=false
LABEL version=${CodeUnitVersion}
ENV SCBuilderVersion=${CodeUnitVersion}
ENV ISRUNNINGINCONTAINER="true"
ENV IS_SANDBOX="1"
#TODO make it possible to have an own apt-server for apt-/npm-/pip-packages etc. to get rid of rate limits

#install essential tools
RUN mkdir /Workspace && \
    mkdir /Workspace/Tools && \
    apt-get update && \
    apt-get install -y ca-certificates curl git wget build-essential nano gnupg python3 python3-pip python3-venv xz-utils zip unzip libglu1-mesa clang gcc g++ make cmake scons autoconf automake libtool pkg-config meson ninja-build libgtk-3-dev ffmpeg maven graphviz fonts-dejavu osslsigncode mono-devel && \
    rm -rf /var/lib/apt/lists/*

#install java (Eclipse-Temurin). Installed from the Temurin-tarball (like Go) instead of the Debian-openjdk-apt-package so
#the exact build can be pinned. This is the system-JDK used by maven and other JVM-tooling;
RUN JAVA_ASSET_VERSION="$(echo "${JavaBuildVersion}" | tr '+' '_')" && \
    curl -fsSL "https://github.com/adoptium/temurin${JavaVersion}-binaries/releases/download/jdk-${JavaBuildVersion}/OpenJDK${JavaVersion}U-jdk_${PlatformForJavaVersion}_linux_hotspot_${JAVA_ASSET_VERSION}.tar.gz" -o /tmp/java.tar.gz && \
    mkdir -p /usr/local/java && \
    tar -C /usr/local/java --strip-components=1 -xzf /tmp/java.tar.gz && \
    rm /tmp/java.tar.gz
ENV JAVA_HOME="/usr/local/java"
ENV PATH="${JAVA_HOME}/bin:${PATH}"
ENV ISRUNNINGINBUILDCONTAINER="true"

#install ca-certificates-java so that the JVM honors the system-wide trust-store. The TrustedRootCA-mechanism of ScriptCollection
#(see the article "TrustedRootCAs" of its reference, respectively TFCPS_CodeUnit_BuildCodeUnits.__collect_trusted_root_ca_arguments
#and SCBuilder/EntryPoint.sh) writes host-provided root-CA-certificates into /usr/local/share/ca-certificates/ at container-start and
#then runs "update-ca-certificates". ca-certificates-java installs the update-hook /etc/ca-certificates/update.d/jks-keystore which
#that run triggers, so the injected CAs end up in the shared JKS at /etc/ssl/certs/java/cacerts. Temurin was installed above into
#/usr/local/java and ships its own cacerts under $JAVA_HOME/lib/security/cacerts; we replace that file by a symlink to the shared
#location so Temurin reads the shared JKS transparently and no second mechanism is required for the JVM. The symlink is created
#before the apt-install so that the postinst-script of ca-certificates-java populates the keystore against Temurin from the start.
#JAVA_HOME and PATH are already set above, so the postinst can resolve "java"/"keytool" via Temurin.
RUN rm -f "${JAVA_HOME}/lib/security/cacerts" && \
    ln -sf /etc/ssl/certs/java/cacerts "${JAVA_HOME}/lib/security/cacerts" && \
    apt-get update && \
    apt-get install -y ca-certificates-java && \
    rm -rf /var/lib/apt/lists/*

#install dotnet
RUN wget https://packages.microsoft.com/config/debian/13/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    rm packages-microsoft-prod.deb && \
    apt-get update && \
    apt-get install -y dotnet-sdk-${DotNetSdkVersion} && \
    rm -rf /var/lib/apt/lists/*
ENV PATH="/root/.dotnet/tools:${PATH}"

#install epew
RUN wget https://github.com/anionDevelopment/Epew/releases/download/v${EpewVersion}/Epew_Artifacts_v${EpewVersion}.zip -O /tmp/epew.zip && \
    unzip /tmp/epew.zip -d /tmp/epew && \
    apt-get install -y /tmp/epew/Epew/BuildResult_Deb/Epew.deb && \
    rm -rf /tmp/epew.zip /tmp/epew

#install common tools
RUN dotnet tool install --global GitVersion.Tool --version ${GitVersionToolVersion} && ln -s /root/.dotnet/tools/dotnet-gitversion /root/.dotnet/tools/gitversion && \
    dotnet tool install --global dotnet-reportgenerator-globaltool --version ${ReportGeneratorVersion} && \
    dotnet tool install --global docfx --version ${DocFxVersion} && \
    dotnet tool install --global dotnet-t4 --version ${DotNetT4Version} && \
    dotnet tool install --global CycloneDX --version ${CycloneDxVersion} && \
    dotnet tool install --global swashbuckle.aspnetcore.cli --version ${SwashbuckleVersion}

# install rust
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
RUN /root/.cargo/bin/rustup toolchain install ${RustVersion} && \
    /root/.cargo/bin/rustup default ${RustVersion}

#install the cargo-tools which ScriptCollection calls for a codeunit with a cargo-project (TFCPS_CodeUnitSpecific_Rust):
#"cargo clippy" for the linting, "cargo llvm-cov" for the test-coverage (it needs the component "llvm-tools-preview") and
#"cargo cyclonedx" for the bill-of-materials. "--locked" builds every tool with the dependencies its own Cargo.lock pins,
#so the same version of a tool is always built from the same sources.
RUN /root/.cargo/bin/rustup component add clippy llvm-tools-preview && \
    /root/.cargo/bin/cargo install cargo-cyclonedx --version ${CargoCycloneDxVersion} --locked && \
    /root/.cargo/bin/cargo install cargo-llvm-cov --version ${CargoLlvmCovVersion} --locked && \
    rm -rf /root/.cargo/registry /root/.cargo/git

#install node (exact NodeVersion pinned via the official nodejs.org-tarball; npm is bundled in the tarball). The NodeSource
#setup-scripts only publish per-major URLs (setup_22.x), so pinning a build-level version via them is not possible and the
#tarball is the only way to install exactly the pinned build. The architecture-token used by nodejs.org (x64/arm64) is
#derived from "dpkg --print-architecture" (amd64/arm64), analog to the other tool-installs in this file.
RUN ARCHITECTURE="$(dpkg --print-architecture)" && \
    case "${ARCHITECTURE}" in \
        amd64) NODE_ARCH="x64" ;; \
        arm64) NODE_ARCH="arm64" ;; \
        *) echo "Unsupported architecture: ${ARCHITECTURE}" >&2; exit 1 ;; \
    esac && \
    curl -fsSL "https://nodejs.org/dist/v${NodeVersion}/node-v${NodeVersion}-linux-${NODE_ARCH}.tar.xz" -o /tmp/node.tar.xz && \
    tar -C /usr/local --strip-components=1 -xJf /tmp/node.tar.xz && \
    rm /tmp/node.tar.xz && \
    node --version && npm --version

#install angular-cli
RUN npm install -g @angular/cli@${AngularCliVersion} && \
    npm install -g @go-task/cli@${GoTaskVersion} && \
    npm install -g pnpm@${PnpmVersion} && \
    npm install -g typescript@${TypeScriptVersion} && \
    npm install -g eslint@${EslintVersion} && \
    npm install -g prettier@${PrettierVersion} && \
    npm install -g vega@${VegaVersion} && \
    npm install -g vega-cli@${VegaCliVersion} && \
    npm install -g vega-lite@${VegaLiteVersion} && \
    npm install -g vega-embed@${VegaEmbedVersion} && \
    npm install -g @cyclonedx/cyclonedx-npm@${CycloneDxNpmVersion} && \
    npm install -g gulp-cli@${GulpCliVersion}

#install docker
RUN install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg && \
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin && \
    rm -rf /var/lib/apt/lists/*

#install cli-tools which are frequently needed in build-pipelines. They are installed from their official release-artifacts and
#not from apt, because the debian-mirrors keep only the newest build of a package and therefore do not allow an exact version-pin
#(the same reason which is documented for chromium below), while release-artifacts stay available permanently. Every version is
#pinned via the corresponding Other/Resources/Dependencies/<Tool>/Version.txt-file.
#The architecture-token is determined at build-time so the instructions also work for an arm64-build: "dpkg --print-architecture"
#returns the token which most of these projects use (amd64/arm64), "uname -m" the one which shellcheck uses (x86_64/aarch64).
#Each block calls the installed tools once at the end, so a broken or wrongly-named artifact lets the image-build fail instead of
#failing the pipeline of a consuming repository.
RUN ARCHITECTURE="$(dpkg --print-architecture)" && \
    curl -fsSL "https://github.com/jqlang/jq/releases/download/jq-${JqVersion}/jq-linux-${ARCHITECTURE}" -o /usr/local/bin/jq && \
    curl -fsSL "https://github.com/mikefarah/yq/releases/download/v${YqVersion}/yq_linux_${ARCHITECTURE}" -o /usr/local/bin/yq && \
    chmod +x /usr/local/bin/jq /usr/local/bin/yq && \
    curl -fsSL "https://github.com/koalaman/shellcheck/releases/download/v${ShellCheckVersion}/shellcheck-v${ShellCheckVersion}.linux.$(uname -m).tar.xz" -o /tmp/shellcheck.tar.xz && \
    tar -C /usr/local/bin --strip-components=1 -xJf /tmp/shellcheck.tar.xz "shellcheck-v${ShellCheckVersion}/shellcheck" && \
    rm /tmp/shellcheck.tar.xz && \
    jq --version && yq --version && shellcheck --version

#install git-lfs. "git lfs install --system" registers the git-lfs-hooks system-wide, otherwise a checkout of a repository which
#uses git-lfs silently yields the pointer-files instead of the actual content.
RUN curl -fsSL "https://github.com/git-lfs/git-lfs/releases/download/v${GitLfsVersion}/git-lfs-linux-$(dpkg --print-architecture)-v${GitLfsVersion}.tar.gz" -o /tmp/git-lfs.tar.gz && \
    tar -C /usr/local/bin --strip-components=1 -xzf /tmp/git-lfs.tar.gz "git-lfs-${GitLfsVersion}/git-lfs" && \
    rm /tmp/git-lfs.tar.gz && \
    git lfs install --system && \
    git lfs version

#install the clis of the forges
RUN ARCHITECTURE="$(dpkg --print-architecture)" && \
    curl -fsSL "https://github.com/cli/cli/releases/download/v${GitHubCliVersion}/gh_${GitHubCliVersion}_linux_${ARCHITECTURE}.tar.gz" -o /tmp/gh.tar.gz && \
    tar -C /usr/local/bin --strip-components=2 -xzf /tmp/gh.tar.gz "gh_${GitHubCliVersion}_linux_${ARCHITECTURE}/bin/gh" && \
    curl -fsSL "https://gitlab.com/gitlab-org/cli/-/releases/v${GitLabCliVersion}/downloads/glab_${GitLabCliVersion}_linux_${ARCHITECTURE}.tar.gz" -o /tmp/glab.tar.gz && \
    tar -C /usr/local/bin --strip-components=1 -xzf /tmp/glab.tar.gz "bin/glab" && \
    rm /tmp/gh.tar.gz /tmp/glab.tar.gz && \
    gh --version && glab --version

#install the kubernetes-tooling
RUN ARCHITECTURE="$(dpkg --print-architecture)" && \
    curl -fsSL "https://dl.k8s.io/release/v${KubectlVersion}/bin/linux/${ARCHITECTURE}/kubectl" -o /usr/local/bin/kubectl && \
    chmod +x /usr/local/bin/kubectl && \
    curl -fsSL "https://get.helm.sh/helm-v${HelmVersion}-linux-${ARCHITECTURE}.tar.gz" -o /tmp/helm.tar.gz && \
    tar -C /usr/local/bin --strip-components=1 -xzf /tmp/helm.tar.gz "linux-${ARCHITECTURE}/helm" && \
    curl -fsSL "https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv${KustomizeVersion}/kustomize_v${KustomizeVersion}_linux_${ARCHITECTURE}.tar.gz" -o /tmp/kustomize.tar.gz && \
    tar -C /usr/local/bin -xzf /tmp/kustomize.tar.gz kustomize && \
    rm /tmp/helm.tar.gz /tmp/kustomize.tar.gz && \
    kubectl version --client && helm version && kustomize version

#install azure-cli. It gets an own virtual-environment so that its dependency-tree can not conflict with the one of
#scriptcollection in /opt/venv; only the "az"-entrypoint is linked into the path.
#Unlike the other tools of this image azure-cli does collect telemetry by default, AZURE_CORE_COLLECT_TELEMETRY=0 disables it.
ENV AZURE_CORE_COLLECT_TELEMETRY="0"
RUN python3 -m venv /opt/azure-cli && \
    /opt/azure-cli/bin/pip install --no-cache-dir ${PipIndexUrlArguments} azure-cli==${AzureCliVersion} && \
    ln -s /opt/azure-cli/bin/az /usr/local/bin/az && \
    az version

#copy entrypoint (ensures a multi-platform-capable buildx builder is available, see EntryPoint.sh, before running the
#actual command)
COPY SCBuilder/EntryPoint.sh /usr/local/bin/EntryPoint.sh
RUN chmod +x /usr/local/bin/EntryPoint.sh

#setup chromium for headless browser-based frontend-tests (e.g. angular/karma via "ng test --browsers ChromeHeadless").
#karma launches the chrome-binary directly via the CHROME_BIN environment-variable. Running chromium as root (the default in the
#build-container) requires --no-sandbox, and the limited /dev/shm in containers requires --disable-dev-shm-usage, so point CHROME_BIN
#to a wrapper that always adds these flags.
#chromium is installed in an own layer with an own apt-update so that the pinned version is resolved against a current
#apt-index instead of against an apt-index which was cached in an earlier layer. the exact version is pinned via the
#ChromiumVersion-build-argument (see above); chromium-common and chromium-sandbox must be pinned to the same version,
#otherwise apt installs a newer build of them and chromium fails due to the version-mismatch. the packages are held so
#that later apt-runs in this image can not replace the pinned build.
#the smoke-test afterwards ensures that the installed chromium-build can actually start in a container: a broken chromium-build
#must let the image-build fail instead of letting every frontend-test-run of every consuming repository fail with
#"Cannot start ChromeHeadless".
RUN apt-get update && \
    apt-get install -y chromium=${ChromiumVersion} chromium-common=${ChromiumVersion} chromium-sandbox=${ChromiumVersion} && \
    apt-mark hold chromium chromium-common chromium-sandbox && \
    rm -rf /var/lib/apt/lists/*
RUN printf '#!/bin/sh\nexec /usr/bin/chromium --no-sandbox --disable-dev-shm-usage "$@"\n' > /usr/local/bin/chromium-headless && \
    chmod +x /usr/local/bin/chromium-headless
ENV CHROME_BIN="/usr/local/bin/chromium-headless"
RUN "${CHROME_BIN}" --headless --disable-gpu --no-first-run --user-data-dir=/tmp/chromium-smoketest --dump-dom about:blank > /dev/null && \
    rm -rf /tmp/chromium-smoketest

#setup playwright for end-to-end-tests (e.g. "npx playwright test" in an angular-codeunit). Only the playwright-cli itself is
#installed globally; the packages a project needs at compile-time (@playwright/test etc.) belong into the package.json of the
#respective project. The version is pinned via the PlaywrightVersion-build-argument, see
#Other/Resources/Dependencies/Playwright/Version.txt.
#The browser-builds are downloaded into a fixed global location (PLAYWRIGHT_BROWSERS_PATH) instead of into the home-directory of
#the current user, so that they are found independently of who runs the tests and so that a "npm install" of a consuming project
#does not download them a second time.
#Note: a playwright-browser-build belongs to exactly one playwright-version. A project which uses another playwright-version in
#its package.json than the version pinned here does not find these browser-builds and downloads its own ones at runtime.
#Playwright launches chromium with --no-sandbox and --disable-dev-shm-usage on its own (chromiumSandbox is disabled by default),
#so - unlike for the karma-chromium above - no wrapper-script is needed for running as root in a container.
#Playwright itself does not collect telemetry; the only outgoing traffic is the browser-download, which happens here at
#image-build-time and not at runtime.
#PLAYWRIGHT_HTML_OPEN=never is required for unattended testruns: with the default "on-failure" the html-reporter starts a
#webserver after a failed testrun ("Serving HTML report at http://localhost:9323. Press Ctrl+C to quit.") and blocks until it
#gets interrupted. Playwright suppresses this only when the environment-variable CI is set or when stdin is no tty, so a
#testrun which is started interactively in this container (docker run -it) would hang forever without this setting. Instead
#of the webserver playwright now prints the hint "npx playwright show-report", the report itself is still written.
ENV PLAYWRIGHT_BROWSERS_PATH="/Workspace/Tools/PlaywrightBrowsers"
ENV PLAYWRIGHT_HTML_OPEN="never"
RUN npm install -g playwright@${PlaywrightVersion} && \
    playwright install --with-deps chromium firefox webkit && \
    rm -rf /var/lib/apt/lists/*
#the smoke-test ensures that every installed browser-build can actually be started in a container. A broken browser-build must
#let the image-build fail instead of letting every end-to-end-testrun of every consuming repository fail. NODE_PATH is required
#because playwright is installed globally and a global package is not resolvable from an arbitrary working-directory otherwise.
RUN NODE_PATH="$(npm root -g)" node -e "const {chromium,firefox,webkit}=require('playwright'); (async()=>{ for(const type of [chromium,firefox,webkit]){ const browser=await type.launch(); const page=await browser.newPage(); await page.setContent('<p>smoke-test</p>'); await browser.close(); } })().catch(error=>{console.error(error);process.exit(1);})"

#install flutter
WORKDIR /Workspace/Tools
ENV PATH="/Workspace/Tools/flutter/bin:/Workspace/Tools/flutter/bin/cache/dart-sdk/bin:${PATH}"
RUN git clone https://github.com/flutter/flutter.git -b ${FlutterVersion} --depth 1 && \
    dart --disable-analytics && \
    flutter precache && \
    flutter config --enable-linux-desktop && \
    flutter config --no-analytics && \
    flutter doctor -v

#Android-app-builds (flutter "appbundle"-target) no longer run in this image: the Android-SDK/NDK-toolchain moved into
#the dedicated SCTaskRunnerAndroid-codeunit/-image, which flutter's appbundle-build now delegates to unconditionally
#(see ScriptCollection's TFCPS_CodeUnitSpecific_Flutter and the remote-build-article in its reference). Flutter itself
#stays in this image because it is still needed here for the web/windows/linux-desktop targets.

#install xvfb (a virtual framebuffer) so a real, built flutter-linux-app can actually be launched in this container, e.g.
#to run "flutter test integration_test/..." against the genuine running app (a real GTK-window on an invisible X11-display)
#for full-app screenshots, as opposed to the widget-tree-only golden tests "flutter test" already runs on its own without
#any display. xvfb-run (bundled in the xvfb debian-package) wraps the given command with a freshly started, throwaway
#Xvfb-instance; "-a" lets it pick a free display-number automatically, avoiding clashes when several testruns happen on
#the same host. Not version-pinned, like the other apt-packages of the "essential tools"-step above.
#The smoke-test ensures that Xvfb can actually start in this container: a broken xvfb-install must let the image-build
#fail instead of letting every full-app-screenshot-testrun of every consuming repository fail.
RUN apt-get update && \
    apt-get install -y xvfb && \
    rm -rf /var/lib/apt/lists/* && \
    xvfb-run -a -- true

#install go
RUN curl -fsSL https://go.dev/dl/go${GoVersion}.linux-${PlatformForGoVersion}.tar.gz -o /tmp/go.tar.gz \
    && rm -rf /usr/local/go \
    && tar -C /usr/local -xzf /tmp/go.tar.gz \
    && rm /tmp/go.tar.gz
ENV PATH="/usr/local/go/bin:${PATH}"

#install scriptcollection
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir ${PipIndexUrlArguments} scriptcollection==${ScriptCollectionVersion}

# install ai-related things. Every tool is pinned via the corresponding Other/Resources/Dependencies/<Tool>/Version.txt-file,
# analog to the other tools of this image.
RUN npm install -g @anthropic-ai/claude-code@${ClaudeCodeVersion} && \
    npm install -g @openai/codex@${CodexVersion} && \
    npm install -g @github/copilot@${CopilotVersion} && \
    npm install -g @google/gemini-cli@${GeminiCliVersion} && \
    npm install -g @fission-ai/openspec@${OpenSpecVersion} && \
    npm install -g opencode-ai@${OpenCodeVersion} && \
    pip install mistral-vibe==${MistralVibeVersion}

# install cursor-cli. Cursor does not publish it as npm- or pip-package, its official installer (https://cursor.com/install) only
# downloads the release-artifact of the version which is the newest one at that time. Therefore the release-artifact of the pinned
# version is downloaded directly from the same location the installer uses. The architecture-token is the one which the installer
# uses (x64/arm64). Both commands which the installer creates ("cursor-agent" and "agent") are linked into the path.
RUN case "$(uname -m)" in x86_64) ARCHITECTURE="x64";; aarch64) ARCHITECTURE="arm64";; *) echo "Unsupported architecture: $(uname -m)" && exit 1;; esac && \
    mkdir -p /opt/cursor-agent && \
    curl -fsSL "https://downloads.cursor.com/lab/${CursorCliVersion}/linux/${ARCHITECTURE}/agent-cli-package.tar.gz" -o /tmp/cursor-agent.tar.gz && \
    tar -C /opt/cursor-agent --strip-components=1 -xzf /tmp/cursor-agent.tar.gz && \
    rm /tmp/cursor-agent.tar.gz && \
    ln -s /opt/cursor-agent/cursor-agent /usr/local/bin/cursor-agent && \
    ln -s /opt/cursor-agent/cursor-agent /usr/local/bin/agent && \
    cursor-agent --version

# report the state of the coding-agents to scrais, which forwards it to herdr (see the article "RunAgentInSandbox" of ScriptCollection).
# Every agent reports through the same helper, only the hook-configuration differs. The configuration of an agent can be replaced by
# an initialization-script of scrais (for example "~/.claude/settings.json"), therefore the hooks are stored in the managed
# configuration of the agent or in an own file. The helper does nothing without the event-folder of scrais, so these hooks have no
# effect for builds or for an agent which is started in another way.
COPY SCBuilder/AgentStatus/scrais-agent-status /usr/local/bin/scrais-agent-status
COPY SCBuilder/AgentStatus/ClaudeManagedSettings.json /etc/claude-code/managed-settings.json
COPY SCBuilder/AgentStatus/CodexRequirements.toml /etc/codex/requirements.toml
COPY SCBuilder/AgentStatus/CopilotHooks.json /root/.copilot/hooks/scrais-agent-status.json
COPY SCBuilder/AgentStatus/OpenCodePlugin.js /root/.config/opencode/plugins/scrais-agent-status.js
COPY SCBuilder/AgentStatus/VibeHooks.toml /root/.vibe/hooks.toml
RUN chmod +x /usr/local/bin/scrais-agent-status && \
    mkdir -p /etc/codex/hooks && \
    ln -s /usr/local/bin/scrais-agent-status /etc/codex/hooks/scrais-agent-status
# The smoke-test ensures that the helper fulfills its contract and that every configuration is present, is valid and calls the helper:
# a broken configuration must let the image-build fail instead of breaking the start of an agent in a consuming repository.
RUN test -z "$(scrais-agent-status working)" && \
    mkdir -p /Workspace/Temp/AgentStatus && \
    scrais-agent-status working && \
    test "$(cat /Workspace/Temp/AgentStatus/events)" = "working" && \
    rm -rf /Workspace/Temp/AgentStatus && \
    jq -e . /etc/claude-code/managed-settings.json /root/.copilot/hooks/scrais-agent-status.json > /dev/null && \
    python3 -c "import tomllib; [tomllib.load(open(file, 'rb')) for file in ['/etc/codex/requirements.toml', '/root/.vibe/hooks.toml']]" && \
    node --check --input-type=module < /root/.config/opencode/plugins/scrais-agent-status.js && \
    grep -q scrais-agent-status /etc/claude-code/managed-settings.json /etc/codex/requirements.toml /root/.copilot/hooks/scrais-agent-status.json /root/.config/opencode/plugins/scrais-agent-status.js /root/.vibe/hooks.toml

# download common tools that can be used at runtime
RUN scdownloadcachabletools -v

ENTRYPOINT ["/usr/local/bin/EntryPoint.sh"]
