#!/bin/bash

# Install the trusted root-CA-certificates which the host declared via the TrustedRootCA_<name>_*-mechanism, so that every tool run
# inside this container trusts them. Three sources are considered, in that order:
#   1. /Workspace/RootCAs/*.crt - files which the host mounted into the container via TrustedRootCA_<name>_Path.
#   2. TrustedRootCA_<name>_Content-environment-variables - inline PEM-content.
#   3. TrustedRootCA_<name>_ContentBase64-environment-variables - inline PEM-content, base64-encoded (intended for CI-secret-stores
#      which can not carry multiline values).
# The <name>-part becomes the filename inside /usr/local/share/ca-certificates/, uniqueness across the three forms is enforced on the
# host-side (see ScriptCollection.TFCPS.TFCPS_CodeUnit_BuildCodeUnits.__collect_trusted_root_ca_arguments). After writing the files
# update-ca-certificates refreshes the system-wide trust-store at /etc/ssl/certs/ca-certificates.crt, and the ca-certificates-java-hook
# installed in the Dockerfile mirrors them into the JVM trust-store (which ${JAVA_HOME}/lib/security/cacerts is symlinked to). This way
# git/curl/.NET/python-via-env/JVM all trust the injected CAs for every build-step that follows.
trusted_root_ca_target="/usr/local/share/ca-certificates"
trusted_root_ca_source="/Workspace/RootCAs"
trusted_root_ca_installed_names=""
if [ -d "${trusted_root_ca_source}" ]; then
    for crt_file in "${trusted_root_ca_source}"/*.crt; do
        [ -e "${crt_file}" ] || continue
        cp "${crt_file}" "${trusted_root_ca_target}/"
        trusted_root_ca_installed_names="${trusted_root_ca_installed_names} $(basename "${crt_file}" .crt)"
    done
fi
# ${!PREFIX@} lists all shell-variables (which include env-vars inherited from docker) whose names start with PREFIX. Multiline values
# are handled correctly this way, which "env | while read" is not: a raw PEM-value (TrustedRootCA_*_Content) legitimately contains
# newlines and "env" would print each line as if it were a separate variable.
for env_name in "${!TrustedRootCA_@}"; do
    env_value="${!env_name}"
    [ -z "${env_value}" ] && continue
    case "${env_name}" in
        TrustedRootCA_*_ContentBase64)
            ca_name="${env_name#TrustedRootCA_}"
            ca_name="${ca_name%_ContentBase64}"
            printf '%s' "${env_value}" | base64 -d > "${trusted_root_ca_target}/${ca_name}.crt"
            trusted_root_ca_installed_names="${trusted_root_ca_installed_names} ${ca_name}"
            ;;
        TrustedRootCA_*_Content)
            ca_name="${env_name#TrustedRootCA_}"
            ca_name="${ca_name%_Content}"
            printf '%s' "${env_value}" > "${trusted_root_ca_target}/${ca_name}.crt"
            # ensure a trailing newline (PEM-parsers of some tools - notably Java keytool - require it):
            if [ -n "$(tail -c1 "${trusted_root_ca_target}/${ca_name}.crt")" ]; then
                printf '\n' >> "${trusted_root_ca_target}/${ca_name}.crt"
            fi
            trusted_root_ca_installed_names="${trusted_root_ca_installed_names} ${ca_name}"
            ;;
    esac
done
if [ -n "${trusted_root_ca_installed_names}" ]; then
    echo "[SCBuilder/EntryPoint] Installing trusted root-CA-certificate(s):${trusted_root_ca_installed_names}"
    if ! update-ca-certificates; then
        echo "[SCBuilder/EntryPoint] update-ca-certificates failed. Aborting container-start - the build would otherwise run without the trust-anchors the host declared." >&2
        exit 1
    fi
fi

# Make tools which carry their own CA-bundle use the system trust-store, so the TrustedRootCA-injection above is honored by them too.
# Without these the python-requests-library (used by scriptcollection itself), pip, curl and node fall back to certifi/their builtin
# bundle, which does not know about the injected CAs. Setting them unconditionally is safe: the system-bundle is a strict superset of
# the vendored bundles (it contains every Mozilla CA plus the injected ones).
export SSL_CERT_FILE="/etc/ssl/certs/ca-certificates.crt"
export REQUESTS_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"
export CURL_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"
export PIP_CERT="/etc/ssl/certs/ca-certificates.crt"
export NODE_EXTRA_CA_CERTS="/etc/ssl/certs/ca-certificates.crt"

# Ensure a multi-platform-capable buildx builder ("docker-container" driver) is selected before the actual
# command runs. Without this, containers started from this image fall back to whatever buildx builder is
# selected on the host docker-daemon that this image's docker.sock is mounted from (usually "default"/
# "desktop-linux", the classic "docker" driver), which needs the host-daemon to have QEMU/binfmt handlers
# registered for the target platform. The "docker-container" driver bundles/bootstraps its own emulation and
# does not depend on that host-state. The builder can not be created at image-build-time (docker buildx create
# needs a reachable docker-daemon, which is not available during "docker build"), so this happens here instead,
# once per container-start.
docker buildx inspect scbuilder >/dev/null 2>&1 || docker buildx create --name scbuilder --driver docker-container --use >/dev/null 2>&1
docker buildx use scbuilder >/dev/null 2>&1

# Run the script which the environment-variable "CustomScriptPath" states, if it states one. This is the hook with
# which the start of a container can be extended (a registry-login, a certificate, a mounted tool) without building an
# own image on top of this one. It runs before the actual command, so that command already sees what the script set up.
# A stated path which does not exist and a script which fails are both a defect of the setup of the container and not
# something this image can compensate: the command would run in an environment which was not prepared, without anybody
# noticing it. The container-start therefore fails instead of continuing. A failed script ends the container-start with
# its own exit-code, so the reason why it failed stays visible to whoever started the container.
# The script is run by bash and not executed directly, because the file which this variable states is usually
# bind-mounted into the container and a bind-mounted file does not necessarily carry the executable-bit; executing it
# directly would let a file which exists (which is the condition stated here) fail with "Permission denied".
if [ -n "${CustomScriptPath}" ]; then
  if [ -f "${CustomScriptPath}" ]; then
    echo "Running the custom-script \"${CustomScriptPath}\"."
    bash "${CustomScriptPath}"
    CustomScriptExitCode=$?
    if [ "${CustomScriptExitCode}" -ne 0 ]; then
      echo "The custom-script \"${CustomScriptPath}\" failed with exit-code ${CustomScriptExitCode}." >&2
      exit "${CustomScriptExitCode}"
    fi
  else
    echo "The environment-variable \"CustomScriptPath\" states the file \"${CustomScriptPath}\", but that file does not exist." >&2
    exit 1
  fi
fi

exec "$@"
