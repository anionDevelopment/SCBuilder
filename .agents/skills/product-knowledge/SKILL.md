---
name: product-knowledge
description: What SCBuilder is, which code-units it contains and how they relate to ScriptCollection. Use this before fixing a defect or developing a feature in this repository, to know where things belong and how to verify a change.
---

# SCBuilder

SCBuilder delivers the runners of [ScriptCollection](https://github.com/anionDev/ScriptCollection): the
environments in which builds of other products are executed. The repository contains almost no application-
logic of its own — what it maintains are images and the toolchains inside them, so its typical change is a
version, a package or a build-step, not a feature.

## Structure of the repository

The repository follows the "common project structure". Use the `work-with-common-project-structure`-skill when
you need the details. There are six code-units, in two groups:

**Build-environments:**

- **`SCBuilder`** — the builder-image which is used with ScriptCollection. This is the code-unit the repository
  is named after.
- **`SCGitHubRunner`** — a slim, self-hosted GitHub-Actions-runner-image which starts job-containers and keeps
  their externals host-identical.

**Task-runners for builds which are bound to an operating-system.** They all serve the same purpose: they
provide an http-server which executes build-steps on behalf of remote clients. Their counterpart on the calling
side is `TFCPS_RemoteBuild` in ScriptCollection.

- **`SCTaskRunnerAndroid`** — a container-image with the Android-SDK/NDK- and flutter-toolchain.
- **`SCTaskRunnerIOS`** — runs natively on a macOS-host, for ios-builds.
- **`SCTaskRunnerMacOS`** — runs natively on a macOS-host, for macos-desktop-builds. Ios-builds are delegated to
  `SCTaskRunnerIOS` and do not belong here.
- **`SCTaskRunnerWindows`** — runs natively on a Windows-host, for windows-builds.

The three native runners are python-code-units and not container-images, which is why they have no
`Dockerfile`: they have to run on the operating-system whose builds they produce. `SCBuilder`, `SCGitHubRunner`
and `SCTaskRunnerAndroid` do have one.

## Building

`scbuildcodeunits` builds everything. Use the `automation-using-scriptcollection`-skill for the details.
