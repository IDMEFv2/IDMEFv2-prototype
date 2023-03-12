#!/usr/bin/env bash

set -eu
set -o pipefail

state_file=/state/.done
if [[ -e "$state_file" ]]; then
    echo "Setup has already run successfully. Skipping"
    exit 0
fi

echo "Running setup"

echo "Setup ended"

mkdir -p "${state_file%/*}"
touch "$state_file"
