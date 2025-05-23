#!/bin/bash
#
# doit.sh
#
# Performs an ACTUAL run of a specific rclone job using chunk_rclone.py
# and a specified control file.
# THIS WILL TRANSFER/MODIFY FILES.
#

# --- Configuration ---
CONTROL_FILE="control_20250523.toml" # Specify the control file for the job
PYTHON_CMD="python3"
SCRIPT_NAME="chunk_rclone.py"
# --- End Configuration ---

echo "--- Starting ACTUAL RUN for job defined in '${CONTROL_FILE}' ---"
echo "--- WARNING: This will transfer/modify files on your rclone remote! ---"
read -p "Are you sure you want to continue? (yes/no): " confirmation
if [[ "${confirmation}" != "yes" ]]; then
    echo "Operation cancelled by user."
    exit 0
fi

if [ ! -f "${CONTROL_FILE}" ]; then
    echo "ERROR: Control file '${CONTROL_FILE}' not found!"
    exit 1
fi
if [ ! -f "${SCRIPT_NAME}" ]; then
    echo "ERROR: Python script '${SCRIPT_NAME}' not found!"
    exit 1
fi

${PYTHON_CMD} "${SCRIPT_NAME}" "${CONTROL_FILE}"

EXIT_CODE=$?
echo ""
if [ ${EXIT_CODE} -eq 0 ]; then
    echo "--- ACTUAL RUN chunk cycle finished as expected. ---"
    echo "--- Re-run this script if the operation was chunked and not yet complete. ---"
else
    echo "--- ACTUAL RUN exited with code ${EXIT_CODE}. Check logs. ---"
fi
