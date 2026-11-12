#!/bin/bash
set -o errexit

# Protocol and port are determined the same way as SCTaskRunnerAndroidCore.py determines them (see there).
protocol="http"
if [[ -n "${SCTaskRunner_CertificateFile}" ]]; then
    protocol="https"
fi
port="${SCTaskRunner_Port:-8080}"

# The server requires basic-auth-credentials for every request. Therefore "--fail" is intentionally not used:
# every HTTP-response (also 401) proves that the SCTaskRunnerServer is running and answers requests.
healthcheckcommand="curl --silent --output /dev/null -v"
if [ "$protocol" == "https" ]; then
    healthcheckcommand="$healthcheckcommand --insecure"
fi
healthcheckcommand="$healthcheckcommand \"$protocol://127.0.0.1:$port/\""
echo "health-check-command: $healthcheckcommand"
eval $healthcheckcommand
