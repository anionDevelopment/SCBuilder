# SCGitHubRunner

![Development-state](https://img.shields.io/badge/development--state-active%20development-brightgreen)
![License](https://img.shields.io/badge/license-GPLv3-blue)

## General

SCGitHubRunner is a slim, self-hosted GitHub-Actions-runner image.

It is designed for the "GitLab-style" model: one permanently running runner-container that waits for jobs and starts a separate job-container (for example the `SCBuilder` image, configured via `jobs.<id>.container.image` in the workflow).

Unlike the common runner-images (which hardcode the runner-installation-path), SCGitHubRunner installs and runs the runner from a configurable `RUNNER_HOME`. When `RUNNER_HOME` is bind-mounted host-identically, the nested `/__e` mount (which provides node20 to JavaScript-actions like `actions/checkout`) resolves correctly on the host. This makes container-jobs work **and** allows multiple runners in parallel, each with its own directory.

See [Setup](./Other/Reference/ReferenceContent/Articles/Setup.md) for the step-by-step setup and [Usage](./Other/Reference/ReferenceContent/Articles/Usage.md) for the configuration-reference.

## Build

This product requires to use `scbuildcodeunits` implemented/provided by [ScriptCollection](https://github.com/anionDev/ScriptCollection) to build the project.

## Contribute

Contributions are always welcome.
