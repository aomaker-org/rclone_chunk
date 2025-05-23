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
#     python3 chunk_rclone.py
#
#   Specific job run (uses config.toml + specified_control_file.toml):
#     python3 chunk_rclone.py path/to/your_job_control_file.toml
#

import argparse
import sys
from pathlib import Path # For main script path if needed, though modules handle CWD

# Attempt to import functions from the 'modules' package
try:
    from modules.config_handler import load_effective_config
    from modules.rclone_exec import run_rclone_chunk
except ImportError as e:
    # Construct a helpful error message if modules are not found.
    # This can happen if the script is not run from the project root,
    # or if the 'modules' directory/package is missing.
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
    # Initialize argparse to handle an optional control file argument
    parser = argparse.ArgumentParser(
        description="Orchestrates chunked rclone copy operations using TOML configuration file(s).",
        epilog="To resume an incomplete operation or run the next chunk, simply re-run the exact same command."
    )
    parser.add_argument(
        "control_file",  # Name of the argument
        type=str,
        nargs='?',       # Makes the argument optional ('?' means 0 or 1 argument)
        default=None,    # Default value if no argument is provided
        help=(f"Optional: Path to a specific .toml control file for this run. "
              f"If not provided, uses '{Path(load_effective_config.__globals__.get('BASE_CONFIG_FILENAME', 'config.toml')).name}' " # Access constant from module
              f"and then '{Path(load_effective_config.__globals__.get('DEFAULT_CONTROL_FILENAME', 'control.toml')).name}' "
              f"if it exists to override base settings.")
    )
    args = parser.parse_args()

    print(f"--- Starting Chunked Rclone Copy Orchestrator (using Python) ---")

    try:
        # Load the effective configuration.
        # load_effective_config will handle finding config.toml and the appropriate control file.
        effective_configuration = load_effective_config(args.control_file)
        
        # Run a single chunk of the rclone operation
        run_status = run_rclone_chunk(effective_configuration)
        
        # Provide guidance to the user based on the outcome
        if run_status == 0: # Covers rclone success, timeout, or user interrupt (Ctrl+C)
            print("\n--- Chunk processing cycle finished as expected. ---")
            print("--- To continue copying remaining files (if any), "
                  "simply re-run this Python script with the same command/control setup. ---")
        else: 
            # This implies rclone itself reported an error (exit codes 1-9+),
            # or a critical script setup error occurred (e.g., rclone not found).
            print(f"\n--- Rclone (or script setup) reported an error (exit code: {run_status}). ---")
            print("--- Please check the rclone log file and console output for details. ---")
            print("--- You may still be able to re-run this script to retry after addressing issues. ---")
        
        sys.exit(run_status) # Exit with rclone's status or 0 if it was a "normal" chunk end

    except SystemExit as e:
        # Catch SystemExit if load_effective_config or other parts call sys.exit()
        # This allows the script to terminate with the intended exit code.
        # We don't want to print a generic "unexpected error" for planned exits.
        if e.code is None or e.code == 0: # Normal exit or no code specified by sys.exit()
            print("--- Script execution ended normally. ---")
        else:
            print(f"--- Script execution failed with exit code: {e.code}. ---")
        sys.exit(e.code if e.code is not None else 1) # Ensure a non-zero exit for actual errors
    except Exception as e:
        # Catch any other unexpected exceptions in the main flow
        print(f"\nCRITICAL ERROR: An unexpected error occurred in the main script: {e}", file=sys.stderr)
        print("--- Please review the error message and stack trace if available. ---", file=sys.stderr)
        sys.exit(1) # General error exit code

if __name__ == "__main__":
    main()
# end of chunk_rclone.py
