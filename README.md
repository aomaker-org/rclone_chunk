# rclone_chunk
# 20250523 fekerr & gemini (attribution pending?)
# ***NOTE***: gemini and copilot both have issues outputting "nested markdown". :)

```markdown
# Chunked Rclone Runner (`chunk_rclone.py`)

## Overview

`chunk_rclone.py` is a Python utility designed to manage large `rclone copy` (or potentially `sync`) operations by breaking them into timed, resumable chunks. This approach is beneficial for:

* Running very long transfers without needing continuous supervision.
* Allowing for graceful pauses and resumption of the overall operation.
* Being a "good citizen" with cloud provider API limits by potentially spacing out operations.
* Detailed logging for each chunk of the operation.

The script is configured using TOML files, allowing for a base configuration and run-specific overrides.

## Features

* **Chunked Transfers:** Executes `rclone` for a configurable duration per chunk.
* **Resumable:** Simply re-run the script with the same configuration to continue where the last chunk left off. `rclone` handles the differential copying.
* **Flexible Configuration:**
    * `config.toml`: For base/default `rclone` settings, global logging preferences, etc.
    * `control_X.toml`: For specific job definitions (source, destination, duration overrides), passed as a command-line argument. A default `control.toml` can also be used if no argument is supplied.
* **Detailed Logging:**
    * Each chunk run generates a local, timestamped log file containing `rclone`'s verbose output.
    * Optional: Uploads these chunk logs to a specified location on your `rclone` remote.
* **Dry Run Support:** Can run `rclone` with `--dry-run` to simulate the operation without making actual changes.
* **Graceful Termination:** Handles timeouts and Ctrl+C interruptions, allowing `rclone` to attempt a clean exit.
* **Environment Aware:** Checks if running in a Python virtual environment and warns if not (though does not prevent execution).

## Prerequisites

1.  **Python 3:** Version 3.11 or newer is recommended (uses `tomllib` from the standard library). For older Python 3 versions (e.g., 3.7-3.10), you would need to install the `toml` package (`pip install toml`) and modify `modules/config_handler.py` to `import toml` instead of `import tomllib`. (Your target is 3.12.3, so built-in `tomllib` is fine).
2.  **`rclone`:** Must be installed, configured with your desired cloud remotes (e.g., Google Drive), and accessible in your system's PATH. Verify with `rclone version` and `rclone listremotes`.

## Project Structure (Example)

```
chunk_rclone/
├── chunk_rclone.py         # The main Python script (orchestrator)
├── config.toml             # Base configuration (YOU MUST CREATE AND CONFIGURE THIS)
├── control.toml            # Optional: Default control file for parameter overrides
├── control_example.toml    # Example of a job-specific control file
├── requirements.txt        # (Can be empty if using Python 3.11+ for tomllib)
├── quickstart.md           # Concise guide to get started quickly
└── README.md               # This detailed documentation file
└── modules/
    ├── __init__.py         # Makes 'modules' a Python package
    ├── config_handler.py   # Loads and merges TOML configurations
    └── rclone_exec.py      # Executes rclone commands
```
*(You will also have a local log directory, e.g., `rclone_chunk_logs_py/`, created when the script runs)*

## Installation / Setup

1.  **Obtain Files:**
    * Ensure all project files (`chunk_rclone.py`, `modules/__init__.py`, `modules/config_handler.py`, `modules/rclone_exec.py`) are in your project directory.
    * Create `requirements.txt` (can be empty or just a comment if Python 3.11+ and no other external libs are used).

2.  **Python Environment (Highly Recommended):**
    It's best practice to use a Python virtual environment.
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    # venv\Scripts\activate    # On Windows
    ```

3.  **Install Dependencies (if any are listed in `requirements.txt`):**
    If `requirements.txt` were to list `toml` (for older Python), you would run:
    ```bash
    pip install -r requirements.txt
    ```
    For Python 3.11+, `tomllib` is built-in, so `requirements.txt` may be empty.

4.  **Configure `rclone`:**
    Make sure `rclone` is already configured with the cloud remote(s) you intend to use. You can check your configured remotes with `rclone listremotes`.

5.  **Create and Configure `config.toml`:**
    * This file is **required** and must be in the same directory as `chunk_rclone.py`.
    * You can use `config.toml.example` (if provided) as a template or create `config.toml` from scratch.
    * **Edit `config.toml`:**
        * **Crucial:** Set `rclone_paths.remote_name` to your `rclone` remote (e.g., `"gaom"`).
        * Define default `rclone_options.flags` (e.g., `["-v", "--tpslimit", "8"]`). `"-vv"` provides more detail.
        * Set a default `chunking.run_duration_seconds` (e.g., `3600` for 1 hour).
        * Configure `logging` parameters like `log_dir`, `log_file_basename`, `upload_logs_to_remote`, and `remote_log_upload_path`.
        * **Important for Default Run:** If you plan to run `python3 chunk_rclone.py` without any arguments and *without* a `control.toml` file present, then `config.toml` must also fully define a default job by setting `rclone_paths.source_path`, `destination_parent_path`, and `backup_folder_name`.

6.  **Prepare Control Files (Optional, but Recommended for Specific Jobs):**
    * To run a specific backup or copy job, create a `<your_job_name>.toml` file (see `control_example.toml` for structure).
    * This file primarily defines job-specific paths under an `[rclone_paths]` section:
        * `source_path`: Source path on the remote (e.g., `"My Drive/PhotosArchive"`).
        * `destination_parent_path`: Parent directory on the remote for the backup (e.g., `"My Drive/Backups"`, or `""` for the remote's root).
        * `backup_folder_name`: Name of the folder to create/use under `destination_parent_path` (e.g., `"Photos_Archive_2025"`).
    * It can also override other settings from `config.toml` such as `run_description`, `[chunking].run_duration_seconds`, or `[logging]` settings for that specific job.
    * If you want a default job to run when `chunk_rclone.py` is called without arguments, create `control.toml` and configure its job paths and any desired overrides.

## Usage

Ensure your Python virtual environment (if using one) is activated. The script should be run from its root directory (where `config.toml` is located).

### Command-Line Arguments

```bash
python3 chunk_rclone.py [control_file_path] [--dry-run]
```

* `control_file_path` (optional positional argument):
    * Path to a specific `.toml` control file for the job.
    * If omitted, the script uses `config.toml` as the base and then merges settings from `control.toml` (if `control.toml` exists in the same directory).
* `--dry-run` (optional flag):
    * If present, adds `rclone`'s `--dry-run` flag to the executed command. This simulates the `rclone copy` operation, showing what would be transferred or changed, without actually modifying any files on the source or destination.
    * When `--dry-run` is active, `_DRYRUN` is also appended to the local log file name for easy identification.

### Examples

1.  **Run a default job** (defined in `config.toml` and/or overridden by `control.toml` if it exists):
    ```bash
    python3 chunk_rclone.py
    ```

2.  **Run a specific job defined in `my_backup_job.toml`:**
    ```bash
    python3 chunk_rclone.py my_backup_job.toml
    ```

3.  **Perform a dry run of a specific job:**
    ```bash
    python3 chunk_rclone.py my_backup_job.toml --dry-run
    ```

4.  **Perform a dry run of the default job:**
    ```bash
    python3 chunk_rclone.py --dry-run
    ```

### Script Behavior

* The script will print the source, destination, maximum duration for the chunk, and the local log file location.
* It then executes the `rclone copy` command. `rclone`'s own progress (if `--stats` is enabled in flags) and verbose output (if `-v` or `-vv` is in flags) will be displayed on the console and also saved to the chunk-specific log file.
* If the `run_duration_seconds` is reached, the `rclone` process will be terminated by a timeout. The script will report this. `rclone` typically attempts to finish any currently transferring files before exiting if it receives a graceful signal (SIGINT/SIGTERM).
* **To resume an incomplete copy operation (e.g., after a timeout or manual interruption via Ctrl+C), simply re-run the exact same command.** `rclone copy` is designed to check the destination and will only transfer missing or changed files.

### Log Files

* Each chunk run creates a timestamped log file locally in the directory specified by `logging.log_dir` in the effective configuration (default: `rclone_chunk_logs_py/`).
* If `--dry-run` is used, `_DRYRUN` is appended to the local log file name.
* If `logging.upload_logs_to_remote` is set to `true` in the effective configuration, the script will attempt to upload the local chunk log to the `rclone` remote path specified by `logging.remote_log_upload_path` after each chunk.

## Configuration Details (`config.toml` and `control_X.toml`)

These files use the TOML format.

### `config.toml` (Base Configuration)

This file sets global defaults for `rclone` behavior and script operation. It **must** exist.

**Example `config.toml` Structure:**
```toml
title = "Base Rclone Chunk Config"

[rclone_paths]
# MANDATORY: Your rclone remote name (e.g., "gaom")
remote_name = "your_configured_rclone_remote_name" 

# These are ONLY needed if running chunk_rclone.py without arguments 
# AND without a 'control.toml' file. Otherwise, the control file provides them.
# source_path = "My Drive/DEFAULT_SOURCE_PATH"
# destination_parent_path = "My Drive/DEFAULT_DESTINATION_PARENT" # Can be "" for remote root
# backup_folder_name = "Default_Backup_Job_Folder_Name"

[rclone_options]
# Default flags passed to rclone copy/sync command as a list of strings.
# Each flag and its value (if any) are separate list items.
flags = [
    "-v",             # Verbose output from rclone (-vv for even more)
    "--tpslimit", "8",  # Limit API transactions per second
    "--stats", "30s",   # Print stats every 30 seconds
    "--stats-one-line"  # Compact stats display
    # Add other common rclone flags like --retries, --checkers, --transfers, etc.
]

[chunking]
# Default duration for each rclone chunk in seconds.
run_duration_seconds = 3600 # Example: 1 hour

[logging]
# Local directory for rclone chunk logs (can be relative to script or absolute).
log_dir = "rclone_chunk_logs_py"
# Base name for local chunk log files (timestamp and _DRYRUN if applicable will be added).
log_file_basename = "rclone_chunk"
# Whether to upload logs to the rclone remote after each chunk (true/false).
upload_logs_to_remote = false
# Path on rclone remote to store log files (if upload_logs_to_remote is true).
# Example: remote_log_upload_path = "My Drive/RcloneAppLogs/ChunkCopyLogs" 
```

### Control Files (`control.toml` or `<job_name>.toml`)

These files define specific jobs or override default settings from `config.toml`. When a control file is used, its settings take precedence.

**A control file typically *must* define the job paths within an `[rclone_paths]` section:**
* `source_path`: Source path on the remote (e.g., `"My Drive/Photos/2024"`).
* `destination_parent_path`: Parent directory on the remote for the backup (e.g., `"My Drive/BackupArchive"`, or `""` if `backup_folder_name` is a full path from the remote root or if the backup folder should be in the remote root).
* `backup_folder_name`: Name of the folder to create/use under `destination_parent_path` (e.g., `"Photos_2024_Backup"`). The final destination for `rclone copy` will be `remote:destination_parent_path/backup_folder_name`.

**Optional overrides in a control file:**
* `run_description`: A string describing this specific job, printed by the script.
* `[chunking].run_duration_seconds`: Override default chunk duration for this job.
* `[logging]`: Override any logging settings (`log_dir`, `log_file_basename`, `upload_logs_to_remote`, `remote_log_upload_path`) for this job.
* `[rclone_options].flags`: To use a completely different set of `rclone` flags for this job (this *replaces* the flags from `config.toml`).

**See `control_example.toml` for a structural example.**

## Troubleshooting

* **`rclone` not found:** Ensure `rclone` is installed and its location is in your system's PATH environment variable.
* **TOML parsing errors:** Check your `.toml` files for correct syntax. Online TOML validators can be helpful.
* **Path issues:** Verify that `remote_name` in `config.toml` is correct. Ensure all paths in `config.toml` and your control files accurately reflect your `rclone` remote structure. Paths on the remote are usually case-sensitive.
* **Permissions:** Check that your `rclone` remote has write permissions to the destination path and read permissions from the source. Ensure the script has permissions to create the local `log_dir`.
* **Examine Logs:** The Python script's console output provides a high-level view. For detailed `rclone` activity, always check the timestamped log files created in your local `log_dir`. If `rclone` exits with an error code, these logs are essential for diagnosis.

```
