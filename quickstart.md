# Quick Start: Chunked Rclone Runner (`chunk_rclone.py`)

This script runs `rclone copy` in timed, resumable chunks, managed by Python.

## Prerequisites

1.  **Python 3**
2.  **`rclone`**: Installed, configured (e.g., with your cloud remote), and in PATH.
3.  **Project Dependencies**: Install from `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

## Setup

1.  **`chunk_rclone.py`**: The main Python script.
2.  **`requirements.txt`**: Lists Python package dependencies (e.g., `toml`).
3.  **`config.toml` (Required Base Config):**
    * Create this in the same directory as `chunk_rclone.py`.
    * **Must contain:** `[rclone_paths]` with `remote_name`.
    * **Should contain:** Default `[rclone_options].flags`, `[chunking].run_duration_seconds`, `[logging]` settings.
    * For a default run (no arguments to script), it also needs job paths:
      `rclone_paths.source_path`, `rclone_paths.destination_parent_path`, `rclone_paths.backup_folder_name`.

4.  **`control.toml` (Optional Override for Default Run):**
    * If present, its settings override `config.toml` for a default run.
    * Typically defines: `source_path_on_remote`, `destination_parent_on_remote`, `backup_folder_name_for_this_run`.

## Running the Script

Ensure your Python virtual environment (if using one) is activated *before* installing requirements and running.

**Option 1: Default Run (uses `config.toml` & optional `control.toml`)**
   ```bash
   python3 chunk_rclone.py
