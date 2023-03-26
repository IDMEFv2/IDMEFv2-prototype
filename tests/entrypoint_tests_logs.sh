#!/usr/bin/env bash

set -u
set -o pipefail

cat /logs | nc -N logstash 6514

echo "Logs sent"
