#!/bin/bash
#
# doit_dryrun.sh
#
# Performs a dry run of a specific rclone job using chunk_rclone.py
# and a specified control file.
#

# --- Configuration ---
CONTROL_FILE="control_20250523.toml" # Specify the control file for the job
PYTHON_CMD="python3"
SCRIPT_NAME="chunk_rclone.py"
# --- End Configuration ---

echo "--- Starting DRY RUN for job defined in '${CONTROL_FILE}' ---"
echo "--- Rclone will simulate operations. No files will be changed. ---"

if [ ! -f "${CONTROL_FILE}" ]; then
    echo "ERROR: Control file '${CONTROL_FILE}' not found!"
    exit 1
fi
if [ ! -f "${SCRIPT_NAME}" ]; then
    echo "ERROR: Python script '${SCRIPT_NAME}' not found!"
    exit 1
fi

${PYTHON_CMD} "${SCRIPT_NAME}" "${CONTROL_FILE}" --dry-run

EXIT_CODE=$?
echo ""
if [ ${EXIT_CODE} -eq 0 ]; then
    echo "--- DRY RUN chunk cycle finished as expected. ---"
else
    echo "--- DRY RUN exited with code ${EXIT_CODE}. Check logs. ---"
fi
