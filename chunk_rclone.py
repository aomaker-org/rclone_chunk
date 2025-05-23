#!/usr/bin/env python3

import toml
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import shlex # For displaying the command string safely

CONFIG_FILE = "config.toml"

def load_config():
    """Loads configuration from CONFIG_FILE."""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = toml.load(f)
        print(f"INFO: Successfully loaded configuration from '{CONFIG_FILE}'")
        return config
    except FileNotFoundError:
        print(f"ERROR: Configuration file '{CONFIG_FILE}' not found.", file=sys.stderr)
    except toml.TomlDecodeError as e:
        print(f"ERROR: Could not parse configuration file '{CONFIG_FILE}': {e}", file=sys.stderr)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while loading configuration: {e}", file=sys.stderr)
    sys.exit(1)

def run_rclone_chunk(config):
    """Runs a single chunk of the rclone copy operation."""
    cfg_paths = config.get('rclone_paths', {})
    cfg_opts = config.get('rclone_options', {})
    cfg_chunking = config.get('chunking', {})
    cfg_logging = config.get('logging', {})

    remote_name = cfg_paths.get('remote_name')
    source_path_on_remote = cfg_paths.get('source_path')
    dest_parent_on_remote = cfg_paths.get('destination_parent_path')
    backup_folder_name = cfg_paths.get('backup_folder_name')

    if not all([remote_name, source_path_on_remote, dest_parent_on_remote is not None, backup_folder_name]):
        print("ERROR: Missing critical rclone path configurations in config.toml "
              "(remote_name, source_path, destination_parent_path, backup_folder_name).", file=sys.stderr)
        return 1

    # Construct full rclone paths
    # Pathlib helps join paths correctly, even if dest_parent_on_remote is empty (for root)
    # or doesn't end with a slash.
    full_source_rclone_path = f"{remote_name}:{source_path_on_remote}"
    
    # Ensure correct joining for destination path, Path objects handle this nicely.
    # If dest_parent_on_remote is empty, Path() treats it as relative, so it works.
    # If backup_folder_name is absolute path on remote (e.g. starts with '/'), it overrides dest_parent.
    # Assuming backup_folder_name is just a name, not a full path.
    if not dest_parent_on_remote: # If parent is root of remote
        full_destination_rclone_path = f"{remote_name}:{backup_folder_name}"
    else:
        full_destination_rclone_path = f"{remote_name}:{str(Path(dest_parent_on_remote) / backup_folder_name)}"


    run_duration_seconds = cfg_chunking.get('run_duration_seconds')
    if not isinstance(run_duration_seconds, int) or run_duration_seconds <= 0:
        print(f"ERROR: Invalid 'run_duration_seconds' ({run_duration_seconds}) in config.toml. "
              "Must be a positive integer.", file=sys.stderr)
        return 1

    # Prepare local log directory and file
    log_dir_path_str = cfg_logging.get('log_dir', 'rclone_chunk_logs_py')
    log_dir = Path(log_dir_path_str)
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"ERROR: Could not create local log directory '{log_dir}': {e}", file=sys.stderr)
        return 1
        
    log_file_basename = cfg_logging.get('log_file_basename', 'rclone_copy_chunk')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = log_dir / f"{log_file_basename}_{timestamp}.log"

    # Construct rclone command list
    rclone_command = ["rclone", "copy"]
    rclone_command.extend(cfg_opts.get('flags', []))
    rclone_command.append(f"--log-file={str(log_file_path)}") # Add log file option
    rclone_command.append(full_source_rclone_path)
    rclone_command.append(full_destination_rclone_path)

    print("=" * 70)
    print(f"Starting Rclone Copy Chunk: {timestamp}")
    print(f"  Source:      {full_source_rclone_path}")
    print(f"  Destination: {full_destination_rclone_path}")
    print(f"  Max duration: {run_duration_seconds} seconds")
    print(f"  Rclone log:  {log_file_path.resolve()}")
    # Safely display the command for user understanding
    display_command = ' '.join(shlex.quote(str(arg)) for arg in rclone_command)
    print(f"  Executing:   {display_command}")
    print("-" * 70)

    exit_code = 0
    try:
        # Start the rclone process
        print(f"\nINFO: rclone process started. Will run for up to {run_duration_seconds} seconds...")
        print(f"INFO: You can monitor progress via rclone's output and in '{log_file_path}'.")
        print("INFO: Press Ctrl+C in this terminal to attempt graceful shutdown of rclone before timeout.")

        process = subprocess.run(rclone_command, timeout=run_duration_seconds, check=False)
        exit_code = process.returncode

    except subprocess.TimeoutExpired:
        print(f"\nINFO: Rclone process timed out after {run_duration_seconds} seconds, as scheduled.")
        exit_code = 124 # Standard exit code for timeout
    except FileNotFoundError:
        print("ERROR: 'rclone' command not found. Is rclone installed and in your system PATH?", file=sys.stderr)
        return 1 # Critical error
    except KeyboardInterrupt:
        print("\nINFO: Keyboard interrupt received. Rclone process should be terminating.")
        # subprocess.run should propagate SIGINT to rclone if it's the direct child.
        # rclone typically handles SIGINT gracefully.
        exit_code = 130 # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"\nERROR: An unexpected error occurred while running rclone: {e}", file=sys.stderr)
        exit_code = 1 # Generic error

    print("-" * 70)
    if exit_code == 0:
        print("INFO: Rclone chunk completed successfully (or all work was done within the duration).")
    elif exit_code == 124:
        print("INFO: Rclone chunk was terminated due to timeout.")
    elif exit_code == 130:
        print("INFO: Rclone chunk was terminated by user (Ctrl+C).")
    else:
        print(f"WARNING: Rclone chunk exited with code {exit_code}.")
    
    print(f"INFO: Log file for this run: {log_file_path.resolve()}")

    # Upload log file if configured
    if cfg_logging.get('upload_logs_to_remote', False):
        remote_log_path_str = cfg_logging.get('remote_log_upload_path')
        if remote_log_path_str:
            full_remote_log_dest = f"{remote_name}:{Path(remote_log_path_str) / log_file_path.name}"
            print(f"INFO: Attempting to upload log file to: {full_remote_log_dest}")
            upload_log_cmd = ["rclone", "copyto", str(log_file_path.resolve()), full_remote_log_dest]
            # Add --progress or other flags to this rclone call if desired
            try:
                subprocess.run(upload_log_cmd, check=True, capture_output=True) # capture_output to suppress its stdout unless error
                print("INFO: Log file uploaded successfully.")
            except subprocess.CalledProcessError as e_upload:
                print(f"WARNING: Failed to upload log file. Rclone stderr:\n{e_upload.stderr.decode()}", file=sys.stderr)
            except FileNotFoundError:
                print("ERROR: 'rclone' command not found for log upload.", file=sys.stderr)
            except Exception as e_upload_generic:
                 print(f"WARNING: An error occurred during log upload: {e_upload_generic}", file=sys.stderr)
        else:
            print("WARNING: 'remote_log_upload_path' not specified in config; cannot upload log.", file=sys.stderr)
            
    print("=" * 70)
    
    if exit_code not in [0, 124, 130]: # If it's an actual rclone error code (other than known terminations)
        return exit_code
    return 0 # Indicate that this chunk management script ran as expected (even if rclone timed out)

def main():
    config = load_config()
    if not config:
        sys.exit(1)

    print(f"--- Starting Chunked Rclone Copy Orchestrator (using '{CONFIG_FILE}') ---")
    
    run_status = run_rclone_chunk(config)
    
    if run_status == 0: # Covers successful rclone completion, timeout, or Ctrl+C
        print("\n--- Chunk processing cycle finished. ---")
        print("--- To continue copying remaining files, simply re-run this Python script. ---")
    else: # This means rclone itself reported an error, or script had critical issue
        print(f"\n--- Rclone reported an error (exit code: {run_status}). Please check logs. ---")
        print("--- You may still be able to re-run this script to retry. ---")
    
    sys.exit(run_status)

if __name__ == "__main__":
    main()
