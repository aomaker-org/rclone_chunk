## dir1parse Environment Setup (setenv.sh)
This document describes the setenv.sh script located in the fek_wip directory of the dir1parse project. This script helps in configuring your shell environment for working with the dir1parse utility.

Location
The script is located at: /home/fekerr/src/dir1parse/fek_wip/setenv.sh

Purpose
The setenv.sh script is designed to:

Define the project's root directory (DIR1PARSE_PROJECT_ROOT) for easy referencing.
Add the project's root directory to your system's PATH, allowing the dir1parse script (assumed to be in the project root) to be called more easily.
Provide a convenient alias (dir1parse) to run the main project script.
How to Use
To activate the environment settings, you need to source the script in your current shell session. Do not execute it directly.

If you are in the project's root directory (/home/fekerr/src/dir1parse/), run:bash
source fek_wip/setenv.sh

