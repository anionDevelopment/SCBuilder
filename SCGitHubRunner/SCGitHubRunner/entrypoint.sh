#!/usr/bin/env bash
# Entrypoint for the SCGitHubRunner image.
# Installs (on first start) and runs the GitHub-Actions-runner from RUNNER_HOME.
# RUNNER_HOME must be bind-mounted host-identically so that the nested /__e mount
# (node20 for JavaScript-actions in container-jobs) resolves on the host.
set -euo pipefail

RUNNER_HOME="${RUNNER_HOME:-/home/runner}"
RUNNER_NAME="${RUNNER_NAME:-$(hostname)}"
LABELS="${LABELS:-self-hosted}"
# Work-directory relative to RUNNER_HOME by default (kept inside the host-mounted directory).
WORKDIR="${RUNNER_WORKDIR:-_work}"

if [ -z "${ORG_NAME:-}" ]; then
  echo "ERROR: ORG_NAME must be set (the GitHub-organization the runner registers to)." >&2
  exit 1
fi
RUNNER_URL="https://github.com/${ORG_NAME}"

mkdir -p "${RUNNER_HOME}"

# Provide the runner-binaries in RUNNER_HOME (the host-mounted directory may be empty on first start).
if [ ! -f "${RUNNER_HOME}/config.sh" ]; then
  echo "Populating runner-binaries into ${RUNNER_HOME} ..."
  cp -a /opt/runner-template/. "${RUNNER_HOME}/"
fi

cd "${RUNNER_HOME}"

get_registration_token() {
  # A registration-token can be provided directly (RUNNER_TOKEN, expires after ~1h)
  # or fetched on demand from a personal-access-token (ACCESS_TOKEN, recommended for permanent runners).
  if [ -n "${RUNNER_TOKEN:-}" ]; then
    echo "${RUNNER_TOKEN}"
    return
  fi
  if [ -n "${ACCESS_TOKEN:-}" ]; then
    curl -fsSL -X POST \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      -H "Accept: application/vnd.github+json" \
      "https://api.github.com/orgs/${ORG_NAME}/actions/runners/registration-token" \
      | jq -r '.token'
    return
  fi
  echo "ERROR: Either RUNNER_TOKEN or ACCESS_TOKEN must be set." >&2
  exit 1
}

if [ ! -f "${RUNNER_HOME}/.runner" ]; then
  echo "Configuring runner '${RUNNER_NAME}' for ${RUNNER_URL} ..."
  EPHEMERAL_FLAG=""
  if [ "${EPHEMERAL:-false}" = "true" ]; then
    EPHEMERAL_FLAG="--ephemeral"
  fi
  ./config.sh --unattended \
    --url "${RUNNER_URL}" \
    --token "$(get_registration_token)" \
    --name "${RUNNER_NAME}" \
    --labels "${LABELS}" \
    --work "${WORKDIR}" \
    --replace ${EPHEMERAL_FLAG}
fi

deregister() {
  # Only deregister when explicitly requested; a permanent runner keeps its registration across restarts.
  if [ "${EPHEMERAL:-false}" = "true" ] || [ "${REMOVE_ON_EXIT:-false}" = "true" ]; then
    echo "Removing runner-registration ..."
    ./config.sh remove --token "$(get_registration_token)" || true
  fi
}
trap 'deregister; exit 0' INT TERM

# run.sh handles graceful shutdown of a running job on SIGTERM/SIGINT itself.
./run.sh &
RUNNER_PID=$!
wait "${RUNNER_PID}"
