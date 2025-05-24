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
                              Expected keys include: 'remote_name', 
                              'source_rclone_path_on_remote', 
                              'dest_parent_rclone_path_on_remote', 
                              'backup_folder_name', 'run_duration_seconds', 
                              'log_dir', 'log_file_basename', 
                              'rclone_flags' (list), 'is_dry_run' (bool),
                              'upload_logs_to_remote' (bool, optional),
                              'remote_log_upload_path' (str, optional if upload is true).

    Returns:
        int: Exit status.
             0 for normal operations (rclone success, timeout, or user Ctrl+C).
             1 for script's own critical errors (e.g., rclone not found, bad config key).
             Other non-zero values are rclone's own error codes if it exited with an error.
    """
    
    # Extract necessary parameters from effective_cfg
    try:
        remote_name = effective_cfg['remote_name']
        source_rclone_path_on_remote = effective_cfg['source_rclone_path_on_remote']
        dest_parent_rclone_path_on_remote = effective_cfg['dest_parent_rclone_path_on_remote']
        backup_folder_name = effective_cfg['backup_folder_name']
        run_duration_seconds = effective_cfg['run_duration_seconds']
        log_dir_str = effective_cfg['log_dir'] 
        log_file_basename = effective_cfg['log_file_basename'] 
        rclone_flags_list = effective_cfg.get('rclone_flags', []) 
        is_dry_run = effective_cfg.get('is_dry_run', False)
    except KeyError as e:
        print(f"ERROR: rclone_exec: Missing a critical configuration key in effective_cfg: {e}", file=sys.stderr)
        return 1 

    # Construct full rclone paths
    full_source_rclone_path = f"{remote_name}:{source_rclone_path_on_remote}"
    # Pathlib handles joining correctly, even if dest_parent_rclone_path_on_remote is empty ("")
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
    log_file_name_itself = f"{log_file_basename}_{timestamp}"
    if is_dry_run:
        log_file_name_itself += "_DRYRUN"
    log_file_name_itself += ".log"
    log_file_path = log_dir / log_file_name_itself

    # Construct rclone command list
    rclone_base_command = "copy" 
    rclone_command = ["rclone", rclone_base_command]
    rclone_command.extend(rclone_flags_list)
    
    if is_dry_run:
        rclone_command.append("--dry-run") 
    
    rclone_command.append(f"--log-file={str(log_file_path.resolve())}") 
    rclone_command.append(full_source_rclone_path)
    rclone_command.append(full_destination_rclone_path)

    # Print pre-execution info
    print("=" * 70)
    run_description = effective_cfg.get('run_description', 'N/A') # Get run_description
    print(f"Starting Rclone Copy Chunk: {run_description} at {timestamp}")
    if is_dry_run:
        print("  Mode:        *** DRY RUN *** (Rclone will simulate transfers)")
    print(f"  Source:      {full_source_rclone_path}")
    print(f"  Destination: {full_destination_rclone_path}")
    print(f"  Max duration: {run_duration_seconds} seconds")
    print(f"  Rclone log:  {log_file_path.resolve()}")
    try:
        display_command = ' '.join(shlex.quote(str(arg)) for arg in rclone_command)
        print(f"  Executing:   {display_command}")
    except Exception: 
        print(f"  Executing (raw list):   {rclone_command}")
    print("-" * 70)

    exit_code = 0 
    try:
        print(f"\nINFO: rclone process started. Will run for up to {run_duration_seconds} seconds...")
        print(f"INFO: Monitor progress via rclone's output (if stats enabled in flags) and in '{log_file_path}'.")
        print("INFO: Press Ctrl+C in this terminal to attempt graceful shutdown of rclone.")

        process = subprocess.run(
            rclone_command, 
            timeout=run_duration_seconds, 
            check=False 
        )
        exit_code = process.returncode

    except subprocess.TimeoutExpired:
        print(f"\nINFO: Rclone process timed out after {run_duration_seconds} seconds (as scheduled).")
        exit_code = 124 
    except FileNotFoundError:
        print("ERROR: 'rclone' command not found. Is rclone installed and in your system PATH?", file=sys.stderr)
        return 1 
    except KeyboardInterrupt:
        print("\nINFO: Keyboard interrupt received by Python script. Rclone process (if started) should terminate gracefully.")
        exit_code = 130 
    except Exception as e:
        print(f"\nERROR: An unexpected error occurred while preparing or running rclone: {e}", file=sys.stderr)
        exit_code = 1 

    # Post-execution messages
    print("-" * 70)
    if exit_code == 0:
        print("INFO: Rclone chunk completed successfully (or all work was done within the duration).")
    elif exit_code == 124:
        print("INFO: Rclone chunk was terminated due to timeout (as scheduled).")
    elif exit_code == 130:
        print("INFO: Rclone chunk was likely terminated by user (Ctrl+C via Python script).")
    else:
        print(f"WARNING: Rclone process exited with code {exit_code}. This may indicate rclone errors.")
        print(f"         Refer to rclone documentation for exit code meanings (e.g., https://rclone.org/docs/#exit-code).")
        print(f"         Also check the detailed rclone log: {log_file_path.resolve()}")
    
    current_run_log_path_str = str(log_file_path.resolve())
    print(f"INFO: Log file for this run: {current_run_log_path_str}")

    # Upload log file if configured
    if effective_cfg.get('upload_logs_to_remote', False):
        remote_log_upload_path_str = effective_cfg.get('remote_log_upload_path')
        current_remote_name_for_log_upload = effective_cfg.get('remote_name') # Use the job's remote_name
   
        if remote_log_upload_path_str and current_remote_name_for_log_upload:
            full_remote_log_dest = f"{current_remote_name_for_log_upload}:{str(Path(remote_log_upload_path_str) / log_file_path.name)}"
            
            print(f"INFO: Attempting to upload log file '{log_file_path.name}' to: {full_remote_log_dest}")
            upload_log_cmd = ["rclone", "copyto", current_run_log_path_str, full_remote_log_dest, "--progress"] 
            try:
                upload_process = subprocess.run(
                    upload_log_cmd, 
                    capture_output=True, 
                    text=True, 
                    check=False, 
                    timeout=120  # 2 minute timeout for log upload
                )
                if upload_process.returncode == 0:
                    print("INFO: Log file uploaded successfully.")
                else:
                    print(f"WARNING: Failed to upload log file '{log_file_path.name}'. Rclone exit code: {upload_process.returncode}", file=sys.stderr)
                    if upload_process.stdout and upload_process.returncode !=0 : # Show stdout only on error for brevity
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
    
    if exit_code in [0, 124, 130]: # Normal terminations for a chunk
        return 0 
    return exit_code # Propagate rclone's error code or script's own critical error code (1)

if __name__ == '__main__':
    # This section is for testing the module directly, which is less common once integrated.
    # It's better to test via the main chunk_rclone.py script.
    print("INFO: rclone_exec.py module - direct execution for basic check.")
    print("      This module is intended to be called by chunk_rclone.py with a full config.")
    print("      To test thoroughly, run the main chunk_rclone.py script with proper TOML configurations.")
# end of modules/rclone_exec.py
