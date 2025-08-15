#!/bin/bash
# Wrapper script for transcribe with environment variables

# Source the .env file properly
if [ -f .env ]; then
    set -a  # automatically export all variables
    source .env
    set +a  # turn off automatic export
fi

# Run transcribe with all arguments
# Use -u flag to force unbuffered output (critical for piping!)
python3 -u -m src.transcribe "$@"