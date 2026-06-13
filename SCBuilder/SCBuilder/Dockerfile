ARG image_debian
FROM ${image_debian}
ARG CodeUnitVersion
ARG DotNetRuntime
ARG PipIndexUrlArguments
ARG GoVersion
ARG PlatformForGoVersion
ARG JavaVersion=21
ARG NodeVersion=22
ARG UpgradeScriptCollection=false
LABEL version=${CodeUnitVersion}
ENV ISRUNNINGINCONTAINER="true"
#TODO make it possible to have an own apt-server for apt-/npm-/pip-packages etc. to get rid of rate limits

#basic
RUN mkdir /Workspace && \
    mkdir /Workspace/Tools && \
    apt-get update

#install essential tools
RUN apt-get install -y ca-certificates curl git wget build-essential nano gnupg python3 python3-pip python3-venv openjdk-${JavaVersion}-jdk xz-utils zip unzip libglu1-mesa clang gcc g++ make cmake scons autoconf automake libtool pkg-config meson ninja-build libgtk-3-dev ffmpeg maven graphviz fonts-dejavu


#install dotnet
RUN wget https://packages.microsoft.com/config/debian/13/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    rm packages-microsoft-prod.deb && \
    apt-get update && \
    apt-get install -y dotnet-sdk-10.0
ENV PATH="/root/.dotnet/tools:${PATH}"

#install epew
RUN wget https://github.com/anionDev/Epew/releases/download/v5.0.18/Epew.v5.0.18.Productive.Artifacts.zip -O /tmp/epew.zip && \
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
    apt-get install -y nodejs

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
    npm install -g vega-embed

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

#install flutter
WORKDIR /Workspace/Tools
RUN git clone https://github.com/flutter/flutter.git -b stable --depth 1
ENV PATH="/Workspace/Tools/flutter/bin:/Workspace/Tools/flutter/bin/cache/dart-sdk/bin:${PATH}"
RUN flutter doctor -v && \
    flutter precache && \
    flutter config --enable-linux-desktop

#install go
RUN curl -fsSL https://go.dev/dl/go${GoVersion}.linux-${PlatformForGoVersion}.tar.gz -o /tmp/go.tar.gz \
    && rm -rf /usr/local/go \
    && tar -C /usr/local -xzf /tmp/go.tar.gz \
    && rm /tmp/go.tar.gz
ENV PATH="/usr/local/go/bin:${PATH}"

#install scriptcollection
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install ${PipIndexUrlArguments} scriptcollection==4.2.134
RUN if [ "${UpgradeScriptCollection}" = "true" ]; then \
        pip install ${PipIndexUrlArguments} scriptcollection --upgrade; \
    fi

# download common tools that can be used at runtime
RUN scdownloadcachabletools -v

#cleanup
RUN rm -rf /var/lib/apt/lists/*

#set commands
ENV ISRUNNINGINBUILDCONTAINER="true"
