# Available tools

This document lists the tools available in the SCBuilder image, based on [SCBuilder/Dockerfile](../../../../SCBuilder/Dockerfile).

## Base packages (apt)

The image installs the following Debian packages:

- curl
- git
- wget
- nano
- gnupg
- python3
- python3-pip
- python3-venv
- openjdk-21-jdk
- nodejs
- npm
- unzip
- xz-utils
- zip
- libglu1-mesa
- clang
- cmake
- ninja-build
- pkg-config
- libgtk-3-dev
- ca-certificates

## Node tooling

- @angular/cli (global npm install)

## Python tooling

- Python virtual environment at /opt/venv
- scriptcollection (installed via pip in /opt/venv)

## Container tooling

Installed from Docker's Debian repository:

- docker-ce
- docker-ce-cli
- containerd.io
- docker-buildx-plugin
- docker-compose-plugin

## .NET tooling

- dotnet-sdk

Global dotnet tools:

- GitVersion.Tool (also linked as gitversion)
- dotnet-reportgenerator-globaltool
- docfx
- dotnet-t4
- CycloneDX
- swashbuckle.aspnetcore.cli

## ScriptCollection cached tools

The Dockerfile runs `scdownloadcachabletools`.
This installs additional cacheable tools provided by ScriptCollection. The exact set depends on the ScriptCollection implementation/version.
See [according documentation in ScriptCollection](https://github.com/anionDev/ScriptCollection/blob/main/ScriptCollection/Other/Reference/ReferenceContent/Articles/DownloadableTools.md).

## Additional language tooling

The image also includes:

- Flutter SDK and Dart CLI tooling
- Go toolchain
