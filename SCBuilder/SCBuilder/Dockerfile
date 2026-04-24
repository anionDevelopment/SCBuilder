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
RUN apt-get install -y curl git wget nano python3 python3-pip python3-venv openjdk-21-jdk nodejs npm unzip xz-utils zip libglu1-mesa clang cmake ninja-build pkg-config libgtk-3-dev ca-certificates 
RUN npm i -g @angular/cli
#TODO install epew

#install scriptcollection
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
#TODO RUN pip install ${PipIndexUrlArguments} scriptcollection
ADD scriptcollection-4.2.70-py3-none-any.whl /Workspace/scriptcollection-4.2.70-py3-none-any.whl
RUN pip install /Workspace/scriptcollection-4.2.70-py3-none-any.whl

#install flutter
WORKDIR /Workspace/Tools
RUN git clone https://github.com/flutter/flutter.git -b stable --depth 1
ENV PATH="/Workspace/Tools/flutter/bin:/Workspace/Tools/flutter/bin/cache/dart-sdk/bin:${PATH}"
RUN flutter doctor -v && \
    flutter precache && \
    flutter config --enable-linux-desktop

#install dotnet
RUN wget https://packages.microsoft.com/config/debian/13/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    rm packages-microsoft-prod.deb && \
    apt-get update && \
    apt-get install -y dotnet-sdk-10.0
ENV PATH="$PATH:/root/.dotnet/tools"

#install go
RUN curl -fsSL https://go.dev/dl/go${GoVersion}.linux-${PlatformForGoVersion}.tar.gz -o /tmp/go.tar.gz \
    && rm -rf /usr/local/go \
    && tar -C /usr/local -xzf /tmp/go.tar.gz \
    && rm /tmp/go.tar.gz
ENV PATH="/usr/local/go/bin:${PATH}"

#install common tools
RUN dotnet tool install --global GitVersion.Tool && \
    ln -s /root/.dotnet/tools/dotnet-gitversion /root/.dotnet/tools/gitversion && \
    dotnet tool install --global dotnet-reportgenerator-globaltool && \
    dotnet tool install --global docfx && \
    dotnet tool install --global dotnet-t4

#install docker
RUN curl -fsSL https://get.docker.com -o get-docker.sh && \
    sh ./get-docker.sh && \
    rm get-docker.sh

#cleanup
RUN rm -rf /var/lib/apt/lists/*
