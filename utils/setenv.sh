#
# setenv.sh - Generic Environment Setup Script
#
# Purpose:
#   Sets up common environment variables and aliases for the current project.
#   This script MUST BE SOURCED, not executed directly.
#
# How to Use:
#   1. Copy this file into your project (e.g., into a 'utils/' or 'scripts/' subdirectory).
#   2. Customize the '--- Customizable Project Variables ---' section below.
#   3. Source the script from your shell:
#      e.g., if in project root and script is in 'utils/': source utils/setenv.sh
#      e.g., from anywhere: source /path/to/your_project/utils/setenv.sh
#

# --- Guard against direct execution ---
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "ERROR: This script (setenv.sh) is designed to be sourced, not executed."
    echo "Please use: source \"${BASH_SOURCE[0]}\""
    exit 1
fi

# --- Customizable Project Variables ---
# !!! EDIT THESE FOR EACH NEW PROJECT !!!
PROJECT_NAME_LOWER="myproject"
PROJECT_NAME_UPPER="MYPROJECT"
MAIN_SCRIPT_NAME="main_script.py"
MAIN_SCRIPT_SUBPATH="" # e.g., "bin/" if main script is in project_root/bin/
# --- End Customizable Project Variables ---


# --- Dynamic Path Setup ---
_THIS_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Assume project root is one level above the directory containing this script (e.g., utils/)
PROJECT_ROOT_CANDIDATE="$(cd "${_THIS_SCRIPT_DIR}/.." && pwd)"
export "${PROJECT_NAME_UPPER}_PROJECT_ROOT"="${PROJECT_ROOT_CANDIDATE}"

PROJECT_ROOT_VAR_NAME="${PROJECT_NAME_UPPER}_PROJECT_ROOT"
PROJECT_ROOT_PATH="${!PROJECT_ROOT_VAR_NAME}"

# --- PATH Modification ---
MAIN_SCRIPT_EFFECTIVE_DIR="${PROJECT_ROOT_PATH}"
if [ -n "${MAIN_SCRIPT_SUBPATH}" ]; then
    CLEANED_SUBPATH="${MAIN_SCRIPT_SUBPATH%/}"
    MAIN_SCRIPT_EFFECTIVE_DIR="${PROJECT_ROOT_PATH}/${CLEANED_SUBPATH}"
fi

if [ -d "${MAIN_SCRIPT_EFFECTIVE_DIR}" ]; then
    if [[ ":${PATH}:" != *":${MAIN_SCRIPT_EFFECTIVE_DIR}:"* ]]; then
        export PATH="${MAIN_SCRIPT_EFFECTIVE_DIR}:${PATH}"
        echo "INFO: PATH extended with script directory: ${MAIN_SCRIPT_EFFECTIVE_DIR}"
    else
        echo "INFO: Script directory '${MAIN_SCRIPT_EFFECTIVE_DIR}' already in PATH."
    fi
elif [ -n "${MAIN_SCRIPT_SUBPATH}" ]; then # Only warn if a subpath was specified but not found
    echo "WARNING: Specified MAIN_SCRIPT_SUBPATH directory '${MAIN_SCRIPT_EFFECTIVE_DIR}' does not exist. Not added to PATH."
fi

# Add the directory containing this setenv.sh script (e.g., 'utils') to PATH
if [ "${_THIS_SCRIPT_DIR}" != "${MAIN_SCRIPT_EFFECTIVE_DIR}" ]; then # Avoid adding if it's the same as above
    if [ -d "${_THIS_SCRIPT_DIR}" ] && [[ ":${PATH}:" != *":${_THIS_SCRIPT_DIR}:"* ]]; then
        export PATH="${_THIS_SCRIPT_DIR}:${PATH}"
        echo "INFO: PATH extended with utils/tools directory: ${_THIS_SCRIPT_DIR}"
    elif [ -d "${_THIS_SCRIPT_DIR}" ] && [[ ":${PATH}:" == *":${_THIS_SCRIPT_DIR}:"* ]]; then
        echo "INFO: Utils/tools directory '${_THIS_SCRIPT_DIR}' already in PATH."
    fi
fi


# --- Aliases ---
FULL_MAIN_SCRIPT_PATH="${PROJECT_ROOT_PATH}/${MAIN_SCRIPT_SUBPATH}${MAIN_SCRIPT_NAME}"
if [ -f "${FULL_MAIN_SCRIPT_PATH}" ]; then
    INTERPRETER=""
    if [[ "${MAIN_SCRIPT_NAME}" == *.py ]]; then
        INTERPRETER="python3 "
    elif [[ "${MAIN_SCRIPT_NAME}" == *.sh ]]; then
        INTERPRETER="bash "
    fi
    alias "${PROJECT_NAME_LOWER}"="${INTERPRETER}\"${FULL_MAIN_SCRIPT_PATH}\""
    echo "INFO: Alias '${PROJECT_NAME_LOWER}' created for: ${INTERPRETER}${FULL_MAIN_SCRIPT_PATH}"
else
    echo "WARNING: Main script '${MAIN_SCRIPT_NAME}' not found at '${FULL_MAIN_SCRIPT_PATH}'. Main project alias not created."
fi

alias "cd${PROJECT_NAME_LOWER}"="cd \"${PROJECT_ROOT_PATH}\""
echo "INFO: Alias 'cd${PROJECT_NAME_LOWER}' created to navigate to project root."

# --- Feedback to User ---
echo ""
echo "${PROJECT_NAME_UPPER} project environment set:"
echo "  Project Root (${PROJECT_ROOT_VAR_NAME}): ${PROJECT_ROOT_PATH}"
echo ""
echo "To use the main script, you might run: '${PROJECT_NAME_LOWER}' <arguments_if_any>"
echo "Remember to activate your Python virtual environment if your project uses one for dependencies."

# end of setenv.sh (generic template)
