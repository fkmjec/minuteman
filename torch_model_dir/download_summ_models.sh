#!/bin/bash
echo "Downloading the FLAN base model..."
curl vps.kmjec.cz/minuteman/flan-t5-base-samsum.mar --output ./flan-t5-base-samsum.mar
echo "Downloading the BART large model..."
curl vps.kmjec.cz/minuteman/lidiya-bart.mar --output ./lidiya-bart.mar
