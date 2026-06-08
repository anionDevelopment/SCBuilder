# Building codeunits locally

The SCBuilder image is used to run `scbuildcodeunits` (provided by [ScriptCollection](https://github.com/anionDev/ScriptCollection)) against a local repository without installing the toolchain on the host.

The image-address and the tag are not hardcoded but taken from the repository's image-definitions-file `.ScriptCollection/OCIImages/ImageDefinition.csv` (entry `SCBuilder`, for example `aniondev/scbuilder;v1.1.0`). Use the tag defined there in the command below.

## Command

```sh
docker run --rm `
  -v "C:\Projects\MyRepository:/Workspace/Repository" `
  -v "/var/run/docker.sock:/var/run/docker.sock" `
  -w /Workspace/Repository `
  aniondev/scbuilder:latest `
  scbuildcodeunits -r /Workspace/Repository -v 4
```

Adjust the host path (`C:\Projects\MyRepository`) to point to the repository you want to build.

## Explanation

- `--rm` removes the container after the run.
- `-v "<repo>:/Workspace/Repository"` mounts the repository into the container.
- `-v "/var/run/docker.sock:/var/run/docker.sock"` forwards the host Docker socket. Codeunit-builds often start containers (for example local test-services), so they need access to a Docker daemon. On Windows with Docker Desktop this exact path works.
- `-w /Workspace/Repository` sets the working directory.
- `scbuildcodeunits -r /Workspace/Repository -v 4` is the actual invocation (`-v 4` = debug log level).

## Useful additional arguments

`scbuildcodeunits` supports further options that can be appended:

- `-e <TargetEnvironment>` selects the target-environment.
- `-c` / `--nocache` builds without the build-cache.
- `-p` / `--ispremerge` runs a pre-merge-build.
- `-u` / `--assertnonewchanges` fails if the build produces changes.
