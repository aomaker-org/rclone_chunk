# modules/rclone_exec.py
"""
Handles the construction and execution of rclone commands for the chunk_rclone utility.

- Takes an effective configuration dictionary.
- Builds the rclone command list.
- Executes rclone as a subprocess with a specified timeout.
- Manages logging for the rclone process.
- Optionally uploads the rclone log file to a remote destination.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path
import shlex # For safely displaying the command string

def run_rclone_chunk(effective_cfg: dict) -> int:
    """
    Runs a single chunk of the rclone copy operation using the effective configuration.

    Args:
        effective_cfg (dict): The fully resolved configuration dictionary
                              containing all necessary parameters for the rclone job.

    Returns:
        int: Exit status.
             0 for normal operations (rclone success, timeout, or user Ctrl+C).
             1 for script's own critical errors (e.g., rclone not found, bad config).
             Other non-zero values are rclone's own error codes if it exited with an error.
    """
    
    # Extract necessary parameters from effective_cfg
    try:
        remote_name = effective_cfg['remote_name']
        source_rclone_path_on_remote = effective_cfg['source_rclone_path_on_remote']
        dest_parent_rclone_path_on_remote = effective_cfg['dest_parent_rclone_path_on_remote']
        backup_folder_name = effective_cfg['backup_folder_name']
        run_duration_seconds = effective_cfg['run_duration_seconds']
        log_dir_str = effective_cfg['log_dir'] # From config_handler, this has a default
        log_file_basename = effective_cfg['log_file_basename'] # From config_handler, this has a default
        rclone_flags_list = effective_cfg.get('rclone_flags', []) 
    except KeyError as e:
        print(f"ERROR: rclone_exec: Missing a critical configuration key in effective_cfg: {e}", file=sys.stderr)
        return 1

    # Construct full rclone paths
    full_source_rclone_path = f"{remote_name}:{source_rclone_path_on_remote}"
    # Pathlib handles joining correctly, even if dest_parent_rclone_path_on_remote is empty ("")
    # an empty Path() / "name" results in "name"
    # Path("parent") / "name" results in "parent/name"
    dest_path_part = Path(dest_parent_rclone_path_on_remote) / backup_folder_name
    full_destination_rclone_path = f"{remote_name}:{str(dest_path_part)}"

    # Prepare local log directory and file
    # Assume log_dir_str is relative to CWD (where chunk_rclone.py is run) or absolute
    log_dir = Path(log_dir_str)
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"ERROR: rclone_exec: Could not create local log directory '{log_dir}': {e}", file=sys.stderr)
        return 1 
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = log_dir / f"{log_file_basename}_{timestamp}.log"

    # Construct rclone command list
    # Default to "copy". Could make this configurable (e.g. "sync") in TOML if needed.
    rclone_base_command = "copy" 
    rclone_command = ["rclone", rclone_base_command]
    rclone_command.extend(rclone_flags_list)
    rclone_command.append(f"--log-file={str(log_file_path.resolve())}") # Use absolute path for log file
    rclone_command.append(full_source_rclone_path)
    rclone_command.append(full_destination_rclone_path)

    # Print pre-execution info
    print("=" * 70)
    print(f"Starting Rclone Chunk: {effective_cfg.get('run_description', 'N/A')} at {timestamp}")
    print(f"  Source:      {full_source_rclone_path}")
    print(f"  Destination: {full_destination_rclone_path}")
    print(f"  Max duration: {run_duration_seconds} seconds")
    print(f"  Rclone log:  {log_file_path.resolve()}")
    try:
        # Safely display the command for user understanding
        display_command = ' '.join(shlex.quote(str(arg)) for arg in rclone_command)
        print(f"  Executing:   {display_command}")
    except Exception: 
        # Fallback if shlex.quote fails (e.g., non-string arg, though unlikely here)
        print(f"  Executing (raw list):   {rclone_command}")
    print("-" * 70)

    exit_code = 0 # Default exit code
    try:
        print(f"\nINFO: rclone process started. Will run for up to {run_duration_seconds} seconds...")
        print(f"INFO: Monitor progress via rclone's output (if stats enabled) and in '{log_file_path}'.")
        print("INFO: Press Ctrl+C in this terminal to attempt graceful shutdown of rclone.")

        # Start the rclone process
        process = subprocess.run(
            rclone_command, 
            timeout=run_duration_seconds, 
            check=False # Check returncode manually to distinguish timeout from rclone errors
        )
        exit_code = process.returncode

    except subprocess.TimeoutExpired:
        print(f"\nINFO: Rclone process timed out after {run_duration_seconds} seconds (as scheduled).")
        exit_code = 124 # Mimic 'timeout' command's exit code for timeout
    except FileNotFoundError:
        print("ERROR: 'rclone' command not found. Is rclone installed and in your system PATH?", file=sys.stderr)
        return 1 # Critical error: rclone itself is missing
    except KeyboardInterrupt:
        print("\nINFO: Keyboard interrupt received by Python script. Rclone process (if started) should terminate gracefully.")
        # subprocess.run should propagate SIGINT to rclone.
        exit_code = 130 # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"\nERROR: An unexpected error occurred while preparing or running rclone: {e}", file=sys.stderr)
        exit_code = 1 # Generic script error

    # Post-execution messages
    print("-" * 70)
    if exit_code == 0:
        print("INFO: Rclone chunk completed successfully (or all work was done within the duration).")
    elif exit_code == 124:
        print("INFO: Rclone chunk was terminated due to timeout (as scheduled).")
    elif exit_code == 130:
        print("INFO: Rclone chunk was likely terminated by user (Ctrl+C via Python script).")
    else:
        # This covers rclone's own error codes (e.g., 1-9 are common for rclone errors)
        print(f"WARNING: Rclone process exited with code {exit_code}. This may indicate rclone errors.")
        print(f"         Refer to rclone documentation for exit code meanings (e.g., https://rclone.org/docs/#exit-code).")
        print(f"         Also check the detailed rclone log: {log_file_path.resolve()}")
    
    print(f"INFO: Log file for this run: {log_file_path.resolve()}")

    # Upload log file if configured
    if effective_cfg.get('upload_logs_to_remote', False):
        remote_log_upload_path_str = effective_cfg.get('remote_log_upload_path')
        # remote_name should be the same as used for the main operation
        
        if remote_log_upload_path_str and remote_name:
            # Ensure remote_log_upload_path_str is just the path part for Path object
            # Construct full remote path for the log file
            full_remote_log_dest = f"{remote_name}:{str(Path(remote_log_upload_path_str) / log_file_path.name)}"
            
            print(f"INFO: Attempting to upload log file to: {full_remote_log_dest}")
            # Using a simpler set of flags for log upload; could be configurable too
            upload_log_cmd = ["rclone", "copyto", str(log_file_path.resolve()), full_remote_log_dest, "--progress"] 
            try:
                upload_process = subprocess.run(
                    upload_log_cmd, 
                    capture_output=True, # Capture output to prevent clutter unless error
                    text=True, 
                    check=False, # Check returncode manually
                    timeout=120  # 2 minute timeout for log upload
                )
                if upload_process.returncode == 0:
                    print("INFO: Log file uploaded successfully.")
                else:
                    print(f"WARNING: Failed to upload log file '{log_file_path.name}'. Rclone exit code: {upload_process.returncode}", file=sys.stderr)
                    # Print rclone's output only if there was an error during upload
                    if upload_process.stdout: 
                        print(f"Rclone stdout (log upload):\n{upload_process.stdout.strip()}", file=sys.stderr)
                    if upload_process.stderr: 
                        print(f"Rclone stderr (log upload):\n{upload_process.stderr.strip()}", file=sys.stderr)
            except subprocess.TimeoutExpired:
                 print(f"WARNING: Timeout during log upload to {full_remote_log_dest}", file=sys.stderr)
            except FileNotFoundError: # Should have been caught by main rclone call
                print("ERROR: 'rclone' command not found for log upload.", file=sys.stderr)
            except Exception as e_upload_generic:
                 print(f"WARNING: An error occurred during log upload: {e_upload_generic}", file=sys.stderr)
        elif effective_cfg.get('upload_logs_to_remote'): 
            # This case means upload_logs_to_remote was true, but path or remote was missing
            print("WARNING: 'upload_logs_to_remote' is true but 'remote_log_upload_path' "
                  "and/or 'remote_name' is not specified sufficiently in config; cannot upload log.", file=sys.stderr)
            
    print("=" * 70)
    
    # For the main script's overall status:
    # Return 0 if the chunk operation itself (timeout, success, user interrupt) was 'normal'.
    # Return rclone's specific error code if rclone failed.
    # Return 1 if there was a script setup error (like rclone not found).
    if exit_code in [0, 124, 130]: # Normal terminations for a chunk
        return 0 
    return exit_code # Propagate rclone's error code or script's own critical error code (1)

if __name__ == '__main__':
    # This is a module, direct execution could be for testing with a dummy config.
    print("INFO: Testing rclone_exec.py module...")
    print("      This module is intended to be called by chunk_rclone.py with a full config.")
    
    # Example dummy config for rudimentary testing if run directly
    dummy_effective_cfg_for_test = {
        'remote_name': 'myremote', # Replace with a real remote if you want to test rclone calls
        'source_rclone_path_on_remote': 'test_source_folder',
        'dest_parent_rclone_path_on_remote': 'test_backup_area',
        'backup_folder_name': 'TestBackup_RcloneExec',
        'run_duration_seconds': 10, # Short duration for test
        'log_dir': 'rclone_exec_test_logs',
        'log_file_basename': 'test_chunk',
        'rclone_flags': ['-v', '--stats', '5s', '--dry-run'], # Use --dry-run for safety!
        'run_description': 'Direct Test of rclone_exec.py',
        'upload_logs_to_remote': False 
    }
    print(f"INFO: Using dummy config for test: {dummy_effective_cfg_for_test}")
    # To actually run rclone in this test, ensure dummy_effective_cfg_for_test paths are valid for 'myremote'
    # For now, it will likely fail if 'myremote:test_source_folder' doesn't exist or rclone isn't configured for 'myremote'.
    # Or it will print an error if rclone command is not found.
    # This test mainly checks if the function can be called and basic logic flows.
    
    # test_status = run_rclone_chunk(dummy_effective_cfg_for_test)
    # print(f"INFO: rclone_exec.py dummy test finished with status: {test_status}")
    print("INFO: To test thoroughly, run the main chunk_rclone.py script with proper TOML configurations.")
