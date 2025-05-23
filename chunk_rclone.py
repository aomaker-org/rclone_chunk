#!/usr/bin/env python3
#
# chunk_rclone.py
#
# Orchestrates chunked rclone copy operations using TOML configuration file(s).
# This script is the main entry point for the utility.
#
# It loads a base configuration from 'config.toml' and can be further controlled
# by an optional 'control.toml' (if no command-line argument is given) or a
# specific control file passed as a command-line argument.
#
# Each run processes one "chunk" of the rclone operation, defined by a timeout.
# The script is designed to be re-run to continue the overall operation until
# rclone reports completion.
#
# Usage:
#   Default run (uses config.toml + control.toml if it exists):
#     python3 chunk_rclone.py [--dry-run]
#
#   Specific job run (uses config.toml + specified_control_file.toml):
#     python3 chunk_rclone.py path/to/your_job_control_file.toml [--dry-run]
#

import argparse
import sys
from pathlib import Path

# Attempt to import functions from the 'modules' package
try:
    from modules.config_handler import load_effective_config
    from modules.rclone_exec import run_rclone_chunk
except ImportError as e:
    current_dir = Path.cwd()
    modules_dir = current_dir / "modules"
    print(f"ERROR: Could not import necessary modules. Details: {e}", file=sys.stderr)
    print(f"       Please ensure that the 'modules' directory (expected at '{modules_dir}')", file=sys.stderr)
    print(f"       exists alongside '{Path(__file__).name}' and contains '__init__.py',", file=sys.stderr)
    print(f"       'config_handler.py', and 'rclone_exec.py'.", file=sys.stderr)
    print(f"       You may need to run this script from the project's root directory.", file=sys.stderr)
    sys.exit(1)
except Exception as e_import: # Catch any other unexpected import errors
    print(f"ERROR: An unexpected error occurred during module import: {e_import}", file=sys.stderr)
    sys.exit(1)

def main():
    """
    Main function to parse arguments, load configurations,
    and orchestrate the chunked rclone copy operation.
    """
    # Constants for config file names, useful for help text
    # These should ideally match what's in modules.config_handler
    # To avoid duplication, modules.config_handler could expose them if needed,
    # or we just ensure they are consistent.
    base_cfg_name = "config.toml" 
    default_ctrl_name = "control.toml"

    parser = argparse.ArgumentParser(
        description="Orchestrates chunked rclone copy operations using TOML configuration file(s).",
        epilog="To resume an incomplete operation or run the next chunk, simply re-run the exact same command."
    )
    parser.add_argument(
        "control_file",
        type=str,
        nargs='?',       # Makes the argument optional ('?' means 0 or 1 argument)
        default=None,    # Default value if no argument is provided
        help=(f"Optional: Path to a specific .toml control file for this run. "
              f"If not provided, uses '{base_cfg_name}' and then "
              f"'{default_ctrl_name}' (if it exists) to override base settings.")
    )
    parser.add_argument(
        "--dry-run",
        action="store_true", # Makes it a boolean flag, default is False
        help="Perform a dry run with rclone (adds --dry-run flag to rclone command "
             "and appends '_DRYRUN' to local log filenames)."
    )
    args = parser.parse_args()

    print(f"--- Starting Chunked Rclone Copy Orchestrator (using Python) ---")
    if args.dry_run:
        print("INFO: *** DRY RUN MODE ENABLED *** Rclone will simulate operations.")

    try:
        # Load the effective configuration.
        # load_effective_config will handle finding config.toml and the appropriate control file.
        effective_configuration = load_effective_config(args.control_file)
        
        # Add the dry_run status to the configuration dictionary to pass it down
        effective_configuration['is_dry_run'] = args.dry_run
        
        # Run a single chunk of the rclone operation
        run_status = run_rclone_chunk(effective_configuration)
        
        # Provide guidance to the user based on the outcome
        if run_status == 0: # Covers rclone success, timeout, or user interrupt (Ctrl+C)
            print("\n--- Chunk processing cycle finished as expected. ---")
            if effective_configuration.get('is_dry_run'):
                 print("--- (Dry run mode was active) ---")
            print("--- To continue copying remaining files (if any), "
                  "simply re-run this Python script with the same command/control setup. ---")
        else: 
            # This implies rclone itself reported an error (exit codes 1-9+),
            # or a critical script setup error occurred (e.g., rclone not found).
            print(f"\n--- Rclone (or script setup) reported an error (exit code: {run_status}). ---")
            print("--- Please check the rclone log file and console output for details. ---")
            print("--- You may still be able to re-run this script to retry after addressing issues. ---")
        
        sys.exit(run_status) 

    except SystemExit as e:
        # Catch SystemExit if load_effective_config or other parts call sys.exit()
        # This allows the script to terminate with the intended exit code.
        if e.code is None or e.code == 0: 
            print("--- Script execution ended normally. ---")
        else:
            print(f"--- Script execution failed with exit code: {e.code}. ---")
        sys.exit(e.code if e.code is not None else 1) 
    except Exception as e:
        # Catch any other unexpected exceptions in the main flow
        print(f"\nCRITICAL ERROR: An unexpected error occurred in the main script: {e}", file=sys.stderr)
        print("--- Please review the error message and stack trace if available. ---", file=sys.stderr)
        sys.exit(1) 

if __name__ == "__main__":
    main()
# end of chunk_rclone.py
