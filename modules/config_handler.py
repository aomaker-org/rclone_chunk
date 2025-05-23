# modules/config_handler.py
"""
Handles loading and merging of TOML configuration files for the chunk_rclone utility.

- Loads a base configuration file (config.toml).
- Optionally loads a control file (either a default 'control.toml' or one specified
  via command line) whose settings override/merge with the base configuration.
- Validates that essential parameters for running a job are present in the
  final effective configuration.
"""

import tomllib # Using built-in tomllib for Python 3.11+ (you are on 3.12.3)
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
        control_file_to_load_path_obj = Path(control_file_arg) # Can be relative or absolute from CLI
        if not control_file_to_load_path_obj.is_file():
            # Try resolving relative to CWD if not absolute and not found
            if not control_file_to_load_path_obj.is_absolute():
                control_file_to_load_path_obj = current_working_dir / control_file_arg
            
            if not control_file_to_load_path_obj.is_file(): # Check again
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

            # Merge/Override logic:
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
    # This ensures critical parameters are present after merging.
    final_settings = {}
    final_settings['run_description'] = effective_config.get('run_description', "Chunked Rclone Run")

    # [rclone_paths] validation
    rclone_paths_cfg = effective_config.get('rclone_paths', {})
    final_settings['remote_name'] = rclone_paths_cfg.get('remote_name')
    final_settings['source_rclone_path_on_remote'] = rclone_paths_cfg.get('source_path')
    final_settings['dest_parent_rclone_path_on_remote'] = rclone_paths_cfg.get('destination_parent_path')
    final_settings['backup_folder_name'] = rclone_paths_cfg.get('backup_folder_name')

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

    # [rclone_options] validation
    rclone_options_cfg = effective_config.get('rclone_options', {})
    final_settings['rclone_flags'] = rclone_options_cfg.get('flags', []) # Defaults to empty list if not found

    # [chunking] validation
    chunking_cfg = effective_config.get('chunking', {})
    final_settings['run_duration_seconds'] = chunking_cfg.get('run_duration_seconds')
    if not isinstance(final_settings.get('run_duration_seconds'), int) or final_settings['run_duration_seconds'] <= 0:
        print(f"ERROR: Invalid or missing 'run_duration_seconds' ({final_settings.get('run_duration_seconds')}). "
              "Must be a positive integer defined in the effective config's [chunking] section.", file=sys.stderr)
        sys.exit(1)

    # [logging] settings (all optional with defaults)
    logging_cfg = effective_config.get('logging', {})
    final_settings['log_dir'] = logging_cfg.get('log_dir', 'rclone_chunk_logs_py')
    final_settings['log_file_basename'] = logging_cfg.get('log_file_basename', 'rclone_copy_chunk')
    final_settings['upload_logs_to_remote'] = logging_cfg.get('upload_logs_to_remote', False)
    final_settings['remote_log_upload_path'] = logging_cfg.get('remote_log_upload_path') 

    print("INFO: Effective configuration loaded and validated successfully.")
    return final_settings

if __name__ == '__main__':
    # This is a module, so direct execution could be for testing.
    print("INFO: Testing config_handler.py module...")
    print("INFO: Attempting to load 'config.toml' and 'control.toml' (if present).")
    
    # Create dummy config files for testing if they don't exist
    test_config_path = Path("config.toml")
    test_control_path = Path("control.toml")
    created_test_config = False
    created_test_control = False

    if not test_config_path.exists():
        print(f"INFO: Creating dummy '{test_config_path}' for testing...")
        with open(test_config_path, 'w') as f:
            f.write('title = "Test Base Config"\n')
            f.write('[rclone_paths]\nremote_name = "testremote"\n')
            f.write('source_path = "test_source"\ndestination_parent_path = "test_dest_parent"\n')
            f.write('backup_folder_name = "test_backup_name"\n')
            f.write('[chunking]\nrun_duration_seconds = 60\n')
        created_test_config = True
        
    if not test_control_path.exists():
        print(f"INFO: Creating dummy '{test_control_path}' for testing (will override source_path)...")
        with open(test_control_path, 'w') as f:
            f.write('run_description = "Test Run via Control"\n')
            f.write('[rclone_paths]\nsource_path = "override_source_from_control"\n') # Override one path
            f.write('[chunking]\nrun_duration_seconds = 30\n') # Override duration
        created_test_control = True

    # Test case 1: Load with default control.toml (if it exists or was created)
    print("\n--- Test Case 1: Loading with default control.toml (if present) ---")
    cfg1 = load_effective_config()
    # print("\nEffective Config 1:")
    # for k, v in cfg1.items():
    #     print(f"  {k}: {v}")

    # Test case 2: Specify a non-existent control file (should error and exit ideally)
    # print("\n--- Test Case 2: Specifying a non-existent control file ---")
    # try:
    #    load_effective_config("non_existent_control.toml")
    # except SystemExit as e:
    #    print(f"Caught SystemExit as expected: {e.code}")

    # Test case 3: No control file specified, and no default control.toml
    # Requires deleting control.toml first for this specific test.
    if test_control_path.exists() and created_test_control: # Only delete if we created it for test
        print(f"\n--- Test Case 3: Temporarily removing '{test_control_path}' to test base config only ---")
        test_control_path.unlink()
        cfg3 = load_effective_config()
        # print("\nEffective Config 3 (base only):")
        # for k, v in cfg3.items():
        #    print(f"  {k}: {v}")
        # Recreate for other potential tests or if user had one
        if created_test_control: # Recreate if it was a dummy
             with open(test_control_path, 'w') as f:
                f.write('run_description = "Test Run via Control (recreated)"\n')
                f.write('[rclone_paths]\nsource_path = "override_source_from_control_recreated"\n')


    print("\nINFO: config_handler.py module test complete.")

    # Clean up dummy files if they were created by this test
    if created_test_config and test_config_path.exists():
        print(f"INFO: Removing dummy '{test_config_path}' created for testing.")
        test_config_path.unlink()
    if created_test_control and test_control_path.exists(): # Check again in case it was recreated
        print(f"INFO: Removing dummy '{test_control_path}' created for testing.")
        test_control_path.unlink()
