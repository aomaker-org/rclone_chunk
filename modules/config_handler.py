# modules/config_handler.py
"""
Handles loading and merging of TOML configuration files for the chunk_rclone utility.

- Loads a base configuration file (config.toml).
- Optionally loads a control file (either a default 'control.toml' or one specified
  via command line) whose settings override/merge with the base configuration.
- Validates that essential parameters for running a job are present in the
  final effective configuration.
"""

import tomllib # Using built-in tomllib for Python 3.11+
import sys
from pathlib import Path

# Constants for default configuration file names, relative to script execution dir
BASE_CONFIG_FILENAME = "config.toml"
DEFAULT_CONTROL_FILENAME = "control.toml"

def load_effective_config(control_file_arg: str = None) -> dict:
    """
    Loads base configuration and an optional control configuration, merging them.

    The base configuration is loaded from BASE_CONFIG_FILENAME (expected in the
    current working directory from where the main script is run).
    If control_file_arg is provided (as a path string), that specific control file is loaded.
    Otherwise, if DEFAULT_CONTROL_FILENAME exists in the current working directory, it is loaded.
    Settings from the control file override/merge with corresponding settings 
    in the base config.

    Args:
        control_file_arg (str, optional): Path to a specific control file
                                          passed via command line.

    Returns:
        dict: The final, effective configuration dictionary.

    Raises:
        SystemExit: If critical configurations are missing or files cannot be loaded/parsed.
    """
    effective_config = {}
    # Assume config files are in the current working directory from where main script is launched
    current_working_dir = Path.cwd() 

    # 1. Load BASE_CONFIG_FILE (mandatory)
    base_config_path = current_working_dir / BASE_CONFIG_FILENAME
    try:
        if not base_config_path.is_file():
            print(f"ERROR: Base configuration file '{BASE_CONFIG_FILENAME}' not found in '{current_working_dir}'.", file=sys.stderr)
            sys.exit(1)
        with open(base_config_path, 'rb') as f: # tomllib needs binary mode
            effective_config = tomllib.load(f) # Start with base config
        print(f"INFO: Loaded base configuration from '{base_config_path.resolve()}'")
    except tomllib.TOMLDecodeError as e:
        print(f"ERROR: Could not parse base config '{BASE_CONFIG_FILENAME}': {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred loading base config '{BASE_CONFIG_FILENAME}': {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Determine which control file to load
    control_file_to_load_path_obj = None 
    if control_file_arg:
        control_file_to_load_path_obj = Path(control_file_arg) 
        if not control_file_to_load_path_obj.is_file():
            if not control_file_to_load_path_obj.is_absolute():
                control_file_to_load_path_obj = current_working_dir / control_file_arg
            if not control_file_to_load_path_obj.is_file(): 
                print(f"ERROR: Specified control file '{control_file_arg}' not found.", file=sys.stderr)
                sys.exit(1)
        print(f"INFO: Custom control file specified: '{control_file_to_load_path_obj.resolve()}'")
    else:
        default_control_path = current_working_dir / DEFAULT_CONTROL_FILENAME
        if default_control_path.is_file():
            control_file_to_load_path_obj = default_control_path
            print(f"INFO: Using default control file: '{default_control_path.resolve()}'")
        else:
            print(f"INFO: No custom control file specified and default '{DEFAULT_CONTROL_FILENAME}' not found in '{current_working_dir}'.")
            print(f"INFO: Proceeding with settings from '{BASE_CONFIG_FILENAME}' only.")

    # 3. Load and merge control file if one was identified
    if control_file_to_load_path_obj:
        try:
            with open(control_file_to_load_path_obj, 'rb') as f: # tomllib needs binary mode
                control_cfg_data = tomllib.load(f)
            print(f"INFO: Loaded control settings from '{control_file_to_load_path_obj.resolve()}'")

            # Merge/Override logic: Iterate through top-level keys from control file.
            for key, control_value in control_cfg_data.items():
                if isinstance(control_value, dict) and isinstance(effective_config.get(key), dict):
                    # If both base and control have this section as a dictionary, merge them.
                    # Control's sub-keys override base's sub-keys within this section.
                    effective_config.setdefault(key, {}).update(control_value)
                else:
                    # Otherwise, control's value for the key replaces base's value entirely.
                    effective_config[key] = control_value
            print(f"INFO: Settings from '{control_file_to_load_path_obj.resolve()}' have been merged/overridden.")

        except tomllib.TOMLDecodeError as e:
            print(f"ERROR: Could not parse control file '{control_file_to_load_path_obj}': {e}", file=sys.stderr)
            sys.exit(1) 
        except Exception as e:
            print(f"ERROR: An unexpected error occurred loading/merging control file '{control_file_to_load_path_obj}': {e}", file=sys.stderr)
            sys.exit(1)

    # --- Extract and Validate final effective settings for the rclone job ---
    final_settings = {}
    final_settings['run_description'] = effective_config.get('run_description', "Chunked Rclone Run")

    rclone_paths_cfg = effective_config.get('rclone_paths', {})
    final_settings['remote_name'] = rclone_paths_cfg.get('remote_name')
    final_settings['source_rclone_path_on_remote'] = rclone_paths_cfg.get('source_path')
    final_settings['dest_parent_rclone_path_on_remote'] = rclone_paths_cfg.get('destination_parent_path')
    final_settings['backup_folder_name'] = rclone_paths_cfg.get('backup_folder_name')

    # Validate essential paths after merging
    if not final_settings.get('remote_name'):
        print("ERROR: 'rclone_paths.remote_name' must be defined in the effective configuration.", file=sys.stderr)
        sys.exit(1)
    if not all([
            final_settings.get('source_rclone_path_on_remote'),
            final_settings.get('dest_parent_rclone_path_on_remote') is not None, # Can be "" for root
            final_settings.get('backup_folder_name')
        ]):
        print("ERROR: Job-specific rclone path information must be defined in [rclone_paths] section:", file=sys.stderr)
        print("       - 'source_path', 'destination_parent_path', 'backup_folder_name'", file=sys.stderr)
        print("       These must be fully resolved after merging 'config.toml' and any control file.", file=sys.stderr)
        sys.exit(1)

    rclone_options_cfg = effective_config.get('rclone_options', {})
    final_settings['rclone_flags'] = rclone_options_cfg.get('flags', [])

    chunking_cfg = effective_config.get('chunking', {})
    final_settings['run_duration_seconds'] = chunking_cfg.get('run_duration_seconds')
    if not isinstance(final_settings.get('run_duration_seconds'), int) or final_settings['run_duration_seconds'] <= 0:
        print(f"ERROR: Invalid or missing 'run_duration_seconds' ({final_settings.get('run_duration_seconds')}). "
              "Must be a positive integer defined in the effective config's [chunking] section.", file=sys.stderr)
        sys.exit(1)

    logging_cfg = effective_config.get('logging', {})
    final_settings['log_dir'] = logging_cfg.get('log_dir', 'rclone_chunk_logs_py')
    final_settings['log_file_basename'] = logging_cfg.get('log_file_basename', 'rclone_copy_chunk')
    final_settings['upload_logs_to_remote'] = logging_cfg.get('upload_logs_to_remote', False)
    final_settings['remote_log_upload_path'] = logging_cfg.get('remote_log_upload_path') 

    print("INFO: Effective configuration loaded and validated successfully.")
    return final_settings

if __name__ == '__main__':
    # Basic test harness for direct execution of this module
    print("INFO: Testing modules/config_handler.py module...")
    print("INFO: This test will attempt to load 'config.toml' and 'control.toml' (if present).")
    print("      Create dummy versions of these files in the script's root for a full test.")
    
    # For this test to run without erroring out immediately, ensure a minimal
    # config.toml exists or provide more robust dummy file creation.
    # The current dummy creation logic below is illustrative.
    
    test_config_path = Path.cwd() / BASE_CONFIG_FILENAME
    test_control_path = Path.cwd() / DEFAULT_CONTROL_FILENAME
    created_dummy_config = False
    created_dummy_control = False

    if not test_config_path.exists():
        print(f"INFO: Creating dummy '{test_config_path.name}' for testing...")
        with open(test_config_path, 'w', encoding='utf-8') as f: # tomllib loads binary, but basic toml can be written as text
            f.write('title = "Test Base Config"\n')
            f.write('[rclone_paths]\nremote_name = "testremote"\n')
            f.write('source_path = "test_source"\ndestination_parent_path = ""\n') # Assuming root
            f.write('backup_folder_name = "test_backup_name"\n')
            f.write('[chunking]\nrun_duration_seconds = 10\n')
        created_dummy_config = True
        
    if not test_control_path.exists():
        # Only create dummy control if no CLI arg would be passed in a real test
        pass # Let load_effective_config handle its absence or presence

    print("\n--- Test Case: Loading with default control.toml (if it exists) or base config only ---")
    try:
        cfg_test = load_effective_config() # Test with no CLI argument
        print("\nEffective Config from test:")
        for k_test, v_test in cfg_test.items():
            if isinstance(v_test, dict):
                print(f"  {k_test}:")
                for sub_k, sub_v in v_test.items():
                    print(f"    {sub_k}: {sub_v}")
            else:
                print(f"  {k_test}: {v_test}")
    except SystemExit as e:
        print(f"Test run exited as expected due to config validation: code {e.code}")
    except Exception as e_test:
        print(f"Error during module test: {e_test}")


    print("\nINFO: config_handler.py module test block complete.")

    # Clean up dummy files if they were created by this test
    if created_dummy_config and test_config_path.exists():
        print(f"INFO: Removing dummy '{test_config_path.name}' created for testing.")
        test_config_path.unlink()
    # if created_dummy_control and test_control_path.exists(): # Control file not created in this example test
    #     print(f"INFO: Removing dummy '{test_control_path.name}' created for testing.")
    #     test_control_path.unlink()

# end of modules/config_handler.py
