#!/usr/bin/env bash

set -o pipefail
set -x
echo "============== START ===========================" >> logs
echo "=    $(date)" >> logs
echo "================================================" >> logs
time make -f Makefile "$@" 2>&1 | tee -a logs
