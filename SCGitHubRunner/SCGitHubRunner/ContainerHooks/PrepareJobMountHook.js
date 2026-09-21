#!/usr/bin/env node
"use strict";

// ACTIONS_RUNNER_CONTAINER_HOOKS-entrypoint of SCGitHubRunner (see the Dockerfile and Usage.md).
//
// The runner-agent invokes this script (with its own bundled node20, not a node installed separately in this
// image) once per hook-command ("prepare_job", "run_container_step", "run_script_step", "cleanup_job"), passing a
// single JSON line on stdin (fields: command, args, state, responseFile) and expecting the process to exit 0 on
// success. This wrapper only inspects the "prepare_job"-command: if SCRIPTCOLLECTION_CONFIGURATION_FOLDER is set,
// it adds one more read-only bind-mount to the job-container - the ScriptCollection-configuration-folder of this
// runner-host - and then delegates unchanged to the official docker-hook (bundled next to this file, see
// Dockerfile) for the actual container-handling. This makes a build running inside the job-container (usually
// SCBuilder) resolve its required environment-variables from TFCPS/EnvironmentVariables.csv exactly like a build
// on the host (see BuildRunnerConfiguration.md in the ScriptCollection-repository), without every repository
// which is built on this runner having to add that mount to its own workflow.
//
// SCRIPTCOLLECTION_CONFIGURATION_FOLDER must be an absolute path that exists on the runner-HOST (the machine
// running the docker-daemon), not inside this runner-container: the job-container is created through the
// host-mounted docker.sock, so the mount-source is resolved on the host - the same rule RUNNER_HOME already
// follows (see Usage.md). If SCRIPTCOLLECTION_CONFIGURATION_FOLDER is not set, this hook behaves exactly like the
// wrapped hook, i.e. it is a no-op passthrough.

const { spawn } = require("child_process");
const path = require("path");

const REAL_HOOK = path.join(__dirname, "docker", "index.js");
const MOUNT_SOURCE = process.env.SCRIPTCOLLECTION_CONFIGURATION_FOLDER;
const MOUNT_TARGET = process.env.SCRIPTCOLLECTION_CONFIGURATION_FOLDER_TARGET || "/root/.ScriptCollection";

function readStdin() {
    return new Promise((resolve, reject) => {
        const chunks = [];
        process.stdin.on("data", (chunk) => chunks.push(chunk));
        process.stdin.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
        process.stdin.on("error", reject);
    });
}

// Adds the configuration-folder-mount to a "prepare_job"-request. Every other command (and a "prepare_job" without
// a job-container, for example a workflow which does not use jobs.<id>.container) is returned unchanged, so this
// wrapper never has to know about the many other fields of the hook-protocol it does not touch.
function addConfigurationFolderMount(rawInput) {
    if (!MOUNT_SOURCE) {
        return rawInput;
    }
    let hookRequest;
    try {
        hookRequest = JSON.parse(rawInput);
    } catch (error) {
        throw new Error(`PrepareJobMountHook: could not parse the hook-input from stdin as JSON: ${error.message}`);
    }
    if (hookRequest.command !== "prepare_job" || !hookRequest.args || !hookRequest.args.container) {
        return rawInput;
    }
    const container = hookRequest.args.container;
    container.systemMountVolumes = container.systemMountVolumes || [];
    container.systemMountVolumes.push({
        sourceVolumePath: MOUNT_SOURCE,
        targetVolumePath: MOUNT_TARGET,
        readOnly: true,
    });
    return JSON.stringify(hookRequest);
}

async function main() {
    const rawInput = await readStdin();
    const hookInput = addConfigurationFolderMount(rawInput);
    const child = spawn(process.execPath, [REAL_HOOK], { stdio: ["pipe", "inherit", "inherit"] });
    child.stdin.end(hookInput);
    const exitCode = await new Promise((resolve, reject) => {
        child.on("error", reject);
        child.on("exit", (code, signal) => resolve(signal ? 1 : (code === null ? 1 : code)));
    });
    process.exit(exitCode);
}

main().catch((error) => {
    console.error(error.stack || String(error));
    process.exit(1);
});
