#!/bin/bash
# setenv.sh for the dir1parse project
# Purpose: Sets up the environment for developing and running dir1parse.
# To be sourced, not executed: source./setenv.sh (if in fek_wip) or source fek_wip/setenv.sh (if in project root)
# Created: 2025-05-19

# Determine the absolute path to the directory containing this script (fek_wip),
# then go up one level to get the project root.
# This makes the script sourceable robustly.
_SETENV_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE}")" && pwd)"
export DIR1PARSE_PROJECT_ROOT="$(cd "${_SETENV_SCRIPT_DIR}/.." && pwd)"

export DIR1PARSE_ONEDRIVE_INFO="/mnt/g/My Drive/dir1parse"

# Add the project root directory to PATH so the 'dir1parse' executable in the root can be called directly.
# Note: If 'dir1parse' script is not directly in DIR1PARSE_PROJECT_ROOT, adjust this or the alias.
# Based on your ls output, 'dir1parse' is in the project root.
export PATH="${DIR1PARSE_PROJECT_ROOT}:${PATH}"

# Alias to run the main dir1parse script
# This ensures you run the script from your project root.
alias dir1parse="${DIR1PARSE_PROJECT_ROOT}/dir1parse"
alias catclip="${DIR1PARSE_PROJECT_ROOT}/fek_wip/catclip"

# Example of other useful aliases (uncomment and modify as needed):
# alias dpconfig="code ${DIR1PARSE_PROJECT_ROOT}/config.toml"
# alias dplogs="tail -f ${DIR1PARSE_PROJECT_ROOT}/rclone_extracted_logs.jsonl" # Assuming default log output from your script
# alias dproot="cd ${DIR1PARSE_PROJECT_ROOT}"

echo "dir1parse environment set:"
echo "  DIR1PARSE_PROJECT_ROOT=${DIR1PARSE_PROJECT_ROOT}"
echo "  PATH extended with: ${DIR1PARSE_PROJECT_ROOT}"
echo "  Alias 'dir1parse' created for: ${DIR1PARSE_PROJECT_ROOT}/dir1parse"
echo ""
echo "  DIR1PARSE_ONEDRIVE_INFO=${DIR1PARSE_ONEDRIVE_INFO}"
echo ""

echo "To use, run commands like: dir1parse --config config.toml"
echo "Remember to activate your Python virtual environment if you use one for this project."
