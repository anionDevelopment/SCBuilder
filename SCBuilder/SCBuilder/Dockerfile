ARG image_debian
FROM ${image_debian}
ARG CodeUnitVersion
ARG DotNetRuntime
ARG PipIndexUrlArguments
ARG GoVersion
ARG PlatformForGoVersion
# System-JDK: the exact build (JavaBuildVersion, e.g. "21.0.6+7") and its major (JavaVersion, e.g. "21") are both passed in
# by Other/Build/Build.py from Other/Resources/Dependencies/JRE/Version.txt. That is the same JRE-pin ScriptCollection reads
# to render the PlantUML-diagrams, so the system-java matches that JRE automatically. Change it in that Version.txt.
ARG JavaVersion
ARG JavaBuildVersion
# Temurin-architecture-token for the platform the image is built for (x64 or aarch64).
ARG PlatformForJavaVersion=x64
# Node major-version, passed in from Other/Resources/Dependencies/Node/Version.txt.
ARG NodeVersion
# Exact debian-package-version of chromium (used for the headless browser-based frontend-tests), passed in from
# Other/Resources/Dependencies/Chromium/Version.txt. Pinned so that the image always contains a chromium-build which is
# known to work. Not every published build does: 150.0.7871.46-1~deb13u1 for example terminated with SIGTRAP directly
# during the startup, which made every karma-testrun fail with "Cannot start ChromeHeadless". Raise this value in that
# Version.txt only to a build which passes the chromium-smoke-test below.
ARG ChromiumVersion
# tool-versions: the values are passed in by the build (Other/Build/Build.py) from the corresponding
# Other/Resources/Dependencies/<Tool>/Version.txt-file, analog to GoVersion above. Change a version by editing that
# Version.txt-file, not here. DotNetSdkVersion is the dotnet feature-band (installed from the rolling microsoft-apt-repo),
# not an exact patch-pin.
ARG DotNetSdkVersion
ARG EpewVersion
ARG GitVersionToolVersion
ARG ReportGeneratorVersion
ARG DocFxVersion
ARG DotNetT4Version
ARG CycloneDxVersion
ARG SwashbuckleVersion
ARG RustVersion
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
#the exact build can be pinned. This is the system-JDK used by maven and other JVM-tooling; the PlantUML-diagram-rendering
#uses the (identical) JRE that ScriptCollection manages in its global cache. The build is pinned to match
#ScriptCollection's __default_pinned_jre_version.
RUN JAVA_ASSET_VERSION="$(echo "${JavaBuildVersion}" | tr '+' '_')" && \
    curl -fsSL "https://github.com/adoptium/temurin${JavaVersion}-binaries/releases/download/jdk-${JavaBuildVersion}/OpenJDK${JavaVersion}U-jdk_${PlatformForJavaVersion}_linux_hotspot_${JAVA_ASSET_VERSION}.tar.gz" -o /tmp/java.tar.gz && \
    mkdir -p /usr/local/java && \
    tar -C /usr/local/java --strip-components=1 -xzf /tmp/java.tar.gz && \
    rm /tmp/java.tar.gz
ENV JAVA_HOME="/usr/local/java"
ENV PATH="${JAVA_HOME}/bin:${PATH}"
ENV ISRUNNINGINBUILDCONTAINER="true"

#install dotnet
RUN wget https://packages.microsoft.com/config/debian/13/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    rm packages-microsoft-prod.deb && \
    apt-get update && \
    apt-get install -y dotnet-sdk-${DotNetSdkVersion} && \
    rm -rf /var/lib/apt/lists/*
ENV PATH="/root/.dotnet/tools:${PATH}"

#install epew
RUN wget https://github.com/anionDevelopment/Epew/releases/download/v${EpewVersion}/Epew.v${EpewVersion}.Artifacts.zip -O /tmp/epew.zip && \
    unzip /tmp/epew.zip -d /tmp/epew && \
    apt-get install -y /tmp/epew/BuildResult_Deb/Epew.deb && \
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

#install node (version configurable via the NodeVersion build-arg; npm is included in the NodeSource nodejs-package)
RUN curl -fsSL https://deb.nodesource.com/setup_${NodeVersion}.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

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

# download common tools that can be used at runtime
RUN scdownloadcachabletools -v

ENTRYPOINT ["/usr/local/bin/EntryPoint.sh"]
