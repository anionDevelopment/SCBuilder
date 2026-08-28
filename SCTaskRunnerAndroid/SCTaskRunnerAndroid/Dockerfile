ARG image_debian
FROM ${image_debian}
ARG CodeUnitVersion
ARG PipIndexUrlArguments
# System-JDK: required by the Android-Gradle-Plugin (the toolchain flutter's "appbundle"-build uses). Pinned the same way
# as SCBuilder used to pin it (see Other/Resources/Dependencies/JRE/Version.txt): the exact build (JavaBuildVersion, e.g.
# "21.0.6+7") and its major (JavaVersion, e.g. "21") are both passed in by Other/Build/Build.py.
ARG JavaVersion
ARG JavaBuildVersion
# Temurin-architecture-token for the platform the image is built for (x64 or aarch64).
ARG PlatformForJavaVersion=x64
# tool-versions: the values are passed in by the build (Other/Build/Build.py) from the corresponding
# Other/Resources/Dependencies/<Tool>/Version.txt-file, same convention as in SCBuilder.
ARG FlutterVersion
ARG AndroidCmdlineToolsVersion
ARG AndroidPlatformVersion
ARG AndroidBuildToolsVersion
ARG AndroidNdkVersion
ARG ScriptCollectionVersion
LABEL version=${CodeUnitVersion}
ENV ISRUNNINGINCONTAINER="true"

#install essential tools. This image only contains what is required to run flutter's "appbundle" (Android)-build on
#behalf of a remote client (see ScriptCollection's TFCPS_RemoteBuild). Unlike SCBuilder it is not a general-purpose
#build-pipeline-image, so it deliberately does not install dotnet, node, rust, go, docker, the ai-clis etc.
RUN mkdir /Workspace && \
    mkdir /Workspace/Tools && \
    apt-get update && \
    apt-get install -y ca-certificates curl git unzip python3 python3-pip python3-venv && \
    rm -rf /var/lib/apt/lists/*

#install java (Eclipse-Temurin), required by the Android-Gradle-Plugin. Installed from the Temurin-tarball, same
#mechanism/pin as SCBuilder used to install it.
RUN JAVA_ASSET_VERSION="$(echo "${JavaBuildVersion}" | tr '+' '_')" && \
    curl -fsSL "https://github.com/adoptium/temurin${JavaVersion}-binaries/releases/download/jdk-${JavaBuildVersion}/OpenJDK${JavaVersion}U-jdk_${PlatformForJavaVersion}_linux_hotspot_${JAVA_ASSET_VERSION}.tar.gz" -o /tmp/java.tar.gz && \
    mkdir -p /usr/local/java && \
    tar -C /usr/local/java --strip-components=1 -xzf /tmp/java.tar.gz && \
    rm /tmp/java.tar.gz
ENV JAVA_HOME="/usr/local/java"
ENV PATH="${JAVA_HOME}/bin:${PATH}"

#install flutter (same mechanism SCBuilder used). Only the android-artifacts are precached (this runner never builds
#the web-/windows-/linux-desktop-targets).
WORKDIR /Workspace/Tools
ENV PATH="/Workspace/Tools/flutter/bin:/Workspace/Tools/flutter/bin/cache/dart-sdk/bin:${PATH}"
RUN git clone https://github.com/flutter/flutter.git -b ${FlutterVersion} --depth 1 && \
    dart --disable-analytics && \
    flutter precache --android && \
    flutter config --no-analytics && \
    flutter doctor -v

#install the android-sdk (required for "flutter build appbundle"). The command-line-tools are pinned via
#AndroidCmdlineToolsVersion (see Other/Resources/Dependencies/AndroidCmdlineTools/Version.txt); the platform-,
#build-tools- and ndk-versions (AndroidPlatformVersion/AndroidBuildToolsVersion/AndroidNdkVersion, see the sibling
#Dependencies-folders) are pre-installed too, so a build does not have to download them (several hundred MB to a few GB)
#on every job. They were determined empirically by running a Flutter-android-build with the pinned FlutterVersion and
#reading which packages the Flutter-Gradle-plugin then auto-downloaded - they have to be re-determined the same way and
#re-pinned here whenever FlutterVersion is bumped, because the Flutter-Gradle-plugin picks its
#compileSdkVersion/targetSdkVersion/ndkVersion itself and changes them with (nearly) every Flutter-release.
#The SDK-licenses are accepted regardless (accepting them otherwise needs an interactive confirmation) and
#$ANDROID_HOME stays writable, so the Android-Gradle-Plugin's own SDK-auto-download still covers any further package a
#future Flutter-bump needs before this pin is updated - the pre-install here is a cache, not a hard requirement.
ENV ANDROID_HOME="/Workspace/Tools/android-sdk"
ENV ANDROID_SDK_ROOT="${ANDROID_HOME}"
ENV PATH="${ANDROID_HOME}/cmdline-tools/latest/bin:${ANDROID_HOME}/platform-tools:${PATH}"
RUN mkdir -p "${ANDROID_HOME}/cmdline-tools" && \
    curl -fsSL "https://dl.google.com/android/repository/commandlinetools-linux-${AndroidCmdlineToolsVersion}_latest.zip" -o /tmp/android-cmdline-tools.zip && \
    unzip -q /tmp/android-cmdline-tools.zip -d "${ANDROID_HOME}/cmdline-tools" && \
    mv "${ANDROID_HOME}/cmdline-tools/cmdline-tools" "${ANDROID_HOME}/cmdline-tools/latest" && \
    rm /tmp/android-cmdline-tools.zip && \
    yes | sdkmanager --licenses > /dev/null && \
    sdkmanager --install "platform-tools" "platforms;android-${AndroidPlatformVersion}" "build-tools;${AndroidBuildToolsVersion}" "ndk;${AndroidNdkVersion}" && \
    sdkmanager --version && \
    flutter doctor -v

#install scriptcollection. Needed here for the SCTaskRunnerServer this image's entrypoint runs (see
#EntryPoint.sh/SCTaskRunnerAndroidCore.py) - unlike SCBuilder, this image never runs the build-pipeline of another
#repository, so scriptcollection is only used as the server-library.
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir ${PipIndexUrlArguments} scriptcollection==${ScriptCollectionVersion}

#copy the entrypoint and the server-launcher. See EntryPoint.sh/SCTaskRunnerAndroidCore.py for the runtime-behaviour and
#the SCTaskRunner_*-environment-variables it reads.
COPY SCTaskRunnerAndroid/EntryPoint.sh /usr/local/bin/EntryPoint.sh
COPY SCTaskRunnerAndroid/SCTaskRunnerAndroidCore.py /usr/local/bin/SCTaskRunnerAndroidCore.py
RUN chmod +x /usr/local/bin/EntryPoint.sh

ENTRYPOINT ["/usr/local/bin/EntryPoint.sh"]
