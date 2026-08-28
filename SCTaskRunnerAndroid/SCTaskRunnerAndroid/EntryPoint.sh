#!/bin/bash

# Entrypoint for the SCTaskRunnerAndroid image: runs the SCTaskRunnerServer (see SCTaskRunnerAndroidCore.py), which
# listens permanently for remote-build-jobs sent by ScriptCollection's TFCPS_RemoteBuild (see the remote-build-article
# in ScriptCollection's reference). Configuration is read from environment-variables by SCTaskRunnerAndroidCore.py
# itself (SCTaskRunner_Username/_Password/_Port/_CertificateFile/_CertificateKeyFile, see the ReadMe).
exec python3 /usr/local/bin/SCTaskRunnerAndroidCore.py
