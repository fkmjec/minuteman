#!/bin/bash
set -uoe pipefail

curl http://vps.kmjec.cz/minuteman/silero_vad.onnx --output transcription_worker/silero_vad.onnx
KEY=$(
    tr -dc A-Za-z0-9 </dev/urandom | head -c 40
    echo ''
)
echo -n $KEY >etherpad-lite/APIKEY.txt
echo -n $KEY >flask/APIKEY.txt
