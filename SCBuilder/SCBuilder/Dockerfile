ARG image_debian
FROM ${image_debian}
ARG CodeUnitVersion
ARG DotNetRuntime
ARG PipIndexUrlArguments
ARG GoVersion
ARG PlatformForGoVersion
ARG JavaVersion=21
# Exact Java-build installed as the system-JDK. Keep this in sync with ScriptCollection's __default_pinned_jre_version so
# the system-java matches the (pinned) JRE that ScriptCollection uses to render the PlantUML-diagrams.
ARG JavaBuildVersion=21.0.6+7
# Temurin-architecture-token for the platform the image is built for (x64 or aarch64).
ARG PlatformForJavaVersion=x64
ARG NodeVersion=22
# Exact debian-package-version of chromium (used for the headless browser-based frontend-tests). Pinned so that the image
# always contains a chromium-build which is known to work. Not every published build does: 150.0.7871.46-1~deb13u1 for
# example terminated with SIGTRAP directly during the startup, which made every karma-testrun fail with
# "Cannot start ChromeHeadless". Raise this value only to a build which passes the chromium-smoke-test below.
ARG ChromiumVersion=150.0.7871.100-1~deb13u1
ARG UpgradeScriptCollection=false
LABEL version=${CodeUnitVersion}
ENV SCBuilderVersion=${CodeUnitVersion}
ENV ISRUNNINGINCONTAINER="true"
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
    apt-get install -y dotnet-sdk-10.0 && \
    rm -rf /var/lib/apt/lists/*
ENV PATH="/root/.dotnet/tools:${PATH}"

#install epew
RUN wget https://github.com/anionDevelopment/Epew/releases/download/v5.0.23/Epew.v5.0.23.Artifacts.zip -O /tmp/epew.zip && \
    unzip /tmp/epew.zip -d /tmp/epew && \
    apt-get install -y /tmp/epew/BuildResult_Deb/Epew.deb && \
    rm -rf /tmp/epew.zip /tmp/epew

#install common tools
RUN dotnet tool install --global GitVersion.Tool --version 6.7.0 && ln -s /root/.dotnet/tools/dotnet-gitversion /root/.dotnet/tools/gitversion && \
    dotnet tool install --global dotnet-reportgenerator-globaltool --version 5.5.10 && \
    dotnet tool install --global docfx --version 2.78.5 && \
    dotnet tool install --global dotnet-t4 --version 3.0.0 && \
    dotnet tool install --global CycloneDX --version 6.2.0 && \
    dotnet tool install --global swashbuckle.aspnetcore.cli --version 10.2.1

# install rust
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
RUN /root/.cargo/bin/rustup toolchain install 1.88.0 && \
    /root/.cargo/bin/rustup default 1.88.0

#install node (version configurable via the NodeVersion build-arg; npm is included in the NodeSource nodejs-package)
RUN curl -fsSL https://deb.nodesource.com/setup_${NodeVersion}.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

#install angular-cli
RUN npm install -g @angular/cli@21.2.13 && \
    npm install -g @go-task/cli@3.51.1 && \
    npm install -g pnpm && \
    npm install -g typescript && \
    npm install -g eslint && \
    npm install -g prettier && \
    npm install -g vega && \
    npm install -g vega-cli && \
    npm install -g vega-lite && \
    npm install -g vega-embed && \
    npm install -g @cyclonedx/cyclonedx-npm

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

#install flutter
WORKDIR /Workspace/Tools
ENV PATH="/Workspace/Tools/flutter/bin:/Workspace/Tools/flutter/bin/cache/dart-sdk/bin:${PATH}"
RUN git clone https://github.com/flutter/flutter.git -b 3.44.4 --depth 1 && \
    dart --disable-analytics && \
    flutter precache && \
    flutter config --enable-linux-desktop && \
    flutter config --no-analytics && \
    flutter doctor -v

#install go
RUN curl -fsSL https://go.dev/dl/go${GoVersion}.linux-${PlatformForGoVersion}.tar.gz -o /tmp/go.tar.gz \
    && rm -rf /usr/local/go \
    && tar -C /usr/local -xzf /tmp/go.tar.gz \
    && rm /tmp/go.tar.gz
ENV PATH="/usr/local/go/bin:${PATH}"

#install scriptcollection
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir ${PipIndexUrlArguments} scriptcollection==4.3.50

# install ai-agents
RUN npm install -g @anthropic-ai/claude-code && \
    npm install -g @openai/codex && \
    npm install -g @github/copilot

# download common tools that can be used at runtime
RUN scdownloadcachabletools -v
