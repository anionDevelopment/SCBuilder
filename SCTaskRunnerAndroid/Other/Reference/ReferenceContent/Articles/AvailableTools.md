# Available tools

This document lists the tools available in the SCTaskRunnerAndroid image, based on
[SCTaskRunnerAndroid/Dockerfile](../../../../SCTaskRunnerAndroid/Dockerfile).

Unlike SCBuilder (a general-purpose build-pipeline-image), this image contains only what is needed to build Android-apps
with flutter.

## Base packages (apt)

- ca-certificates
- curl
- git
- unzip
- python3
- python3-pip
- python3-venv

## Java

- Eclipse Temurin JDK, installed from the official Temurin-tarball (required by the Android-Gradle-Plugin).

## Flutter / Android

- Flutter SDK and Dart CLI tooling (only the `android`-precache is downloaded)
- Android command-line-tools, platform-tools, the pinned Android-platform, the pinned build-tools and the pinned NDK
  (see the `AndroidCmdlineTools`/`AndroidPlatform`/`AndroidBuildTools`/`AndroidNdk`-dependency-folders)

## Python tooling

- Python virtual environment at `/opt/venv`
- `scriptcollection` (installed via pip in `/opt/venv`), used to run the `SCTaskRunnerServer` this image's entrypoint
  starts (see [Running the runner](./RunningTheRunner.md))
