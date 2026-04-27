from exceptions import InvalidConfigError

import sys


def validate_config(config):
    required = ["nb_drones", "start_hub", "end_hub", "connection"]

    missing_keys = []
    for key in required:
        if key not in config:
            missing_keys.append(key)

    if missing_keys:
        raise InvalidConfigError(f"Missing mandatoty keys: {missing_keys}")
    if not config['connection']:
        raise InvalidConfigError("At least one connection is required")
    try:
        config['nb_drones'] = int(config['nb_drones'])
        if (config['nb_drones'] <= 0):
            raise InvalidConfigError("Number of drones cannot be 0 or less")
    except InvalidConfigError as e:
        print(f"Error: {e}")


def parse_setting(file_path: str):
    config = {
        'nb_drones': 0,
        'start_hub': None,
        'end_hub': None,
        'hubs': [],
        'connections': []
    }
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if ':' not in line:
                    raise InvalidConfigError(f"Invalid line format: {line}")
                key, value = line.split(':', 1)
                config[key.strip().lower()] = value.strip()
        return validate_config(config)
    except InvalidConfigError as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
