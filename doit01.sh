#!/bin/bash
#
# doit.sh
#
# Performs an ACTUAL run of a specific rclone job using chunk_rclone.py
# and a specified control file.
# THIS WILL TRANSFER/MODIFY FILES ON YOUR RCLONE REMOTE.
# This script is an example; customize CONTROL_FILE as needed.
#

# --- Configuration ---
# !!! EDIT THIS to point to the control file for the job you want to run !!!
CONTROL_FILE="control_20250523.toml" 

PYTHON_CMD="python3"
SCRIPT_NAME="chunk_rclone.py"
# --- End Configuration ---

echo "--- Starting ACTUAL RUN for job defined in '${CONTROL_FILE}' ---"
echo "--- WARNING: This will transfer/modify files on your rclone remote! ---"

if [ ! -f "${CONTROL_FILE}" ]; then
    echo "ERROR: Control file '${CONTROL_FILE}' not found!"
    echo "       Please create it or correct the CONTROL_FILE variable in this script."
    exit 1
fi
if [ ! -f "${SCRIPT_NAME}" ]; then
    echo "ERROR: Python script '${SCRIPT_NAME}' not found!"
    echo "       Ensure it's in the same directory or update SCRIPT_NAME."
    exit 1
fi

# Confirmation prompt
read -p "Are you sure you want to continue with the ACTUAL run using '${CONTROL_FILE}'? (yes/no): " confirmation
if [[ "${confirmation}" != "yes" ]]; then
    echo "Operation cancelled by user."
    exit 0
fi


${PYTHON_CMD} "${SCRIPT_NAME}" "${CONTROL_FILE}"

EXIT_CODE=$?
echo ""
if [ ${EXIT_CODE} -eq 0 ]; then
    echo "--- ACTUAL RUN chunk cycle finished as expected. ---"
    echo "--- Re-run this script if the operation was chunked and not yet complete. ---"
else
    echo "--- ACTUAL RUN exited with code ${EXIT_CODE}. Check logs and script output. ---"
fi
