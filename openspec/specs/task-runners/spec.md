# Task-runners Specification

## Purpose

Records what every task-runner of this repository has to guarantee towards the clients which use it. A task-runner
executes a build-step of a foreign repository on behalf of a remote client, so it holds the complete repository of that
client, including content which is not in git and which is not public. What it gives back and what it keeps is therefore
not an implementation-detail but a property the clients rely on.

This applies to every codeunit whose name starts with `SCTaskRunner` - currently `SCTaskRunnerAndroid`,
`SCTaskRunnerIOS`, `SCTaskRunnerMacOS` and `SCTaskRunnerWindows` - regardless of whether it runs as a container or
natively on a host. They share their server-implementation (`SCTaskRunnerServer` of ScriptCollection), so a change to
that implementation has to keep these requirements for all of them at once.

## Requirements

### Requirement: A task-runner returns only the build-artifact of a job

A task-runner SHALL transfer back only the artifact which the build-step it executed produced - for example the
aab-file of an android-app-build or the folder with the binaries of a desktop-build. It SHALL NOT transfer back the
repository it received, its workspace, or anything else which exists on the runner.

Which folder contains that artifact is stated by the client when it submits the job, because only the client knows what
the build-step it delegates produces.

#### Scenario: A client fetches the result of a finished job

- **WHEN** a job has finished and its client fetches the result
- **THEN** only the content of the folder which that client stated as the result of the job is transferred

#### Scenario: The build changed something outside of the artifact

- **WHEN** the build-step changed something in the workspace outside of that folder - for example a
  toolchain-configuration containing paths of the runner, a cache, or an intermediate file of the build
- **THEN** that stays on the runner and does not reach the client, because it is not a result and is wrong in the
  repository of a client

#### Scenario: A client states a folder outside of its workspace

- **WHEN** a client states a result-folder which is not inside the workspace of its job
- **THEN** the request is refused, so that a job can never transfer content of the runner which does not belong to it

### Requirement: A task-runner keeps nothing of a build after the job

A task-runner SHALL delete everything which belongs to a job as soon as that job is over: the repository it received,
the workspace with everything the build produced, the artifact it transferred, and every temporary file which was
created for that job. After that, nothing of the repository of that client SHALL remain on the runner.

This SHALL NOT depend on the client doing anything: a client which loses its connection, is interrupted or crashes must
not be able to leave content of a repository behind on the runner.

#### Scenario: A job is over

- **WHEN** a job is over - regardless of whether its build succeeded or failed
- **THEN** its workspace, the archive of the repository it received and the archive of the artifact which was
  transferred are removed from the runner

#### Scenario: The client of a job never comes back

- **WHEN** the client of a job never fetches its result and never deletes the job, for example because its connection
  broke or because it was interrupted
- **THEN** the runner removes that job and everything which belongs to it on its own

#### Scenario: A runner is restarted

- **WHEN** a runner is started
- **THEN** nothing of an earlier job is present any more
