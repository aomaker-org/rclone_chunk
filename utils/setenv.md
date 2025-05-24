# Project Environment Setup Script (`setenv.sh`)

## Overview

The `setenv.sh` script is a generic shell utility designed to quickly configure your terminal environment for working on a specific project. When sourced, it sets project-specific environment variables (like the project root path), modifies your system `PATH` for the current session to include project-specific script directories, and can create convenient command-line aliases.

This script is intended to be copied into a project (typically into a `utils/` or `scripts/` subdirectory) and then customized for that particular project.

## Location (Example for `chunk_rclone` project)

If used with the `chunk_rclone` project, you would typically place this script at:
`~/src/chunk_rclone/utils/setenv.sh`

## Purpose

The `setenv.sh` script aims to:

1.  **Dynamically Determine Project Root:** It intelligently finds the root directory of your project based on its own location.
2.  **Export Project Root Variable:** Sets an environment variable (e.g., `MYPROJECT_PROJECT_ROOT`) pointing to the project's root directory, making it easy for other scripts or commands to reference.
3.  **Update `PATH`:** Temporarily adds relevant project directories (like the project root, a `utils/` or `scripts/` folder) to your system `PATH` for the current shell session. This allows you to call project-specific scripts or utilities from any location within that session without specifying their full path.
4.  **Create Aliases:**
    * Sets up a main alias (e.g., `myproject`) to run the primary script of the project (e.g., `python3 /path/to/project/main_script.py`).
    * Sets up a `cdmyproject` alias to quickly navigate to the project's root directory.
5.  **Provide Feedback:** Outputs information about the environment variables and aliases it has set.

## How to Use

**IMPORTANT:** This script **MUST BE SOURCED**, not executed directly. Sourcing runs the commands in your current shell session, allowing it to modify your environment (like `PATH` and aliases). Direct execution runs it in a subshell, and any changes are lost when the subshell exits.

1.  **Copy `setenv.sh` to your project:**
    Place the generic `setenv.sh` script into a suitable subdirectory within your project, for example, `utils/` or `scripts/`.

2.  **Customize for Your Project:**
    Open the `setenv.sh` script in a text editor and modify the **`--- Customizable Project Variables ---`** section at the top:
    ```bash
    # --- Customizable Project Variables ---
    # !!! EDIT THESE FOR EACH NEW PROJECT !!!
    PROJECT_NAME_LOWER="myproject"         # e.g., "chunk_rclone"
    PROJECT_NAME_UPPER="MYPROJECT"         # e.g., "CHUNK_RCLONE"
    MAIN_SCRIPT_NAME="main_script.py"      # e.g., "chunk_rclone.py"
    MAIN_SCRIPT_SUBPATH=""                 # e.g., "" if main script is in project root, 
                                           #      or "bin/" if it's in project_root/bin/
    # --- End Customizable Project Variables ---
    ```
    * `PROJECT_NAME_LOWER`: A lowercase name for your project, used for creating aliases (e.g., `chunk_rclone` would create an alias `chunk_rclone` and `cdchunk_rclone`).
    * `PROJECT_NAME_UPPER`: An uppercase name used as a prefix for environment variables (e.g., `CHUNK_RCLONE_PROJECT_ROOT`).
    * `MAIN_SCRIPT_NAME`: The filename of the main script for your project.
    * `MAIN_SCRIPT_SUBPATH`: The path to your main script *relative to the project root*. If your main script is directly in the project root, leave this as `""` (empty string). If it's in `project_root/bin/`, set this to `"bin/"`.

3.  **Source the Script:**
    Open your terminal, navigate to your project's root directory, and then source the script.
    * If `setenv.sh` is in `~/your_project_root/utils/setenv.sh`:
        ```bash
        cd ~/your_project_root/
        source utils/setenv.sh
        ```
    * You can also source it using its full or relative path from any location:
        ```bash
        source /path/to/your_project/utils/setenv.sh
        ```

**After Sourcing:**

* The script will print information about the environment variables it has set (e.g., `CHUNK_RCLONE_PROJECT_ROOT`) and the aliases it has created.
* Your `PATH` will be updated for the current session.
* You can then use the defined aliases (e.g., `chunk_rclone` to run your main script, `cdchunk_rclone` to go to the project root).
* Remember to activate any Python virtual environment your project might require separately, as `setenv.sh` reminds you.

## Notes

* The environment changes (PATH, aliases, exported variables) made by sourcing `setenv.sh` are **temporary and apply only to the current shell session**. If you open a new terminal, you'll need to source it again.
* The script includes a guard to prevent accidental direct execution and will print an error if you try to run it like `bash utils/setenv.sh` instead of sourcing it.

This `setenv.sh` provides a convenient and consistent way to set up your workspace for different projects.
