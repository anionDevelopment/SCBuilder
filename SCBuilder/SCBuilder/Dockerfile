ARG image_debian
FROM ${image_debian}
ARG CodeUnitVersion
ARG DotNetRuntime
ARG PipIndexUrlArguments
ARG GoVersion
ARG PlatformForGoVersion
LABEL version=${CodeUnitVersion}
ENV ISRUNNINGINCONTAINER="true"
#TODO make it possible to have an own apt-server for apt-packages to get rid of rate limits

#basic
RUN mkdir /Workspace && \
    mkdir /Workspace/Tools && \
    apt-get update

#install essential tools
RUN apt-get install -y curl git wget nano gnupg python3 python3-pip python3-venv openjdk-21-jdk nodejs npm unzip xz-utils zip libglu1-mesa clang cmake ninja-build pkg-config libgtk-3-dev ca-certificates 
#TODO set java-version to install via env-variable
#TODO set node-version to install via env-variable
#TODO install ffmpeg

#install angular-cli
RUN npm i -g @angular/cli@21.2.13

#install epew
#TODO install epew

#install scriptcollection
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install ${PipIndexUrlArguments} scriptcollection==4.2.99

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
#RUN git clone https://github.com/flutter/flutter.git -b stable --depth 1
#ENV PATH="/Workspace/Tools/flutter/bin:/Workspace/Tools/flutter/bin/cache/dart-sdk/bin:${PATH}"
#RUN flutter doctor -v && \
#    flutter precache && \
#    flutter config --enable-linux-desktop

#install dotnet
RUN wget https://packages.microsoft.com/config/debian/13/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    rm packages-microsoft-prod.deb && \
    apt-get update && \
    apt-get install -y dotnet-sdk-10.0
ENV PATH="/root/.dotnet/tools:${PATH}"

#install go
#RUN curl -fsSL https://go.dev/dl/go${GoVersion}.linux-${PlatformForGoVersion}.tar.gz -o /tmp/go.tar.gz \
#    && rm -rf /usr/local/go \
#    && tar -C /usr/local -xzf /tmp/go.tar.gz \
#    && rm /tmp/go.tar.gz
#ENV PATH="/usr/local/go/bin:${PATH}"

#install common tools
RUN dotnet tool install --global GitVersion.Tool --version 6.7.0 && ln -s /root/.dotnet/tools/dotnet-gitversion /root/.dotnet/tools/gitversion && \
    dotnet tool install --global dotnet-reportgenerator-globaltool --version 5.5.10 && \
    dotnet tool install --global docfx --version 2.78.5 && \
    dotnet tool install --global dotnet-t4 --version 3.0.0 && \
    dotnet tool install --global CycloneDX --version 6.2.0 && \
    dotnet tool install --global swashbuckle.aspnetcore.cli --version 10.2.1

RUN scdownloadcachabletools

#cleanup
RUN rm -rf /var/lib/apt/lists/*

#set commands
ENV ISRUNNINGINBUILDCONTAINER="true"
