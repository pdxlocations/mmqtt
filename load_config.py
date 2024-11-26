import os
import json
from types import SimpleNamespace
from meshtastic import BROADCAST_NUM


def load_config(filename="config.json"):
    """
    Load and return all configuration variables from the config.json file,
    accessible via dot notation (e.g., config.mqtt.broker).
    
    Returns:
        SimpleNamespace: A nested namespace representing the configuration.
    """

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, filename)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    
    config["channel"]["key"] = "1PG7OiApB1nwvP+rz05pAQ==" if config["channel"]["key"] == "AQ==" else config["channel"]["key"]
    config["node"]["number"] = int(config["node"]["id"].replace("!", ""), 16)
    config["destination_id"] = BROADCAST_NUM

    # Convert to nested SimpleNamespace for dot notation
    def dict_to_namespace(data):
        if isinstance(data, dict):
            return SimpleNamespace(**{k: dict_to_namespace(v) for k, v in data.items()})
        return data

    return dict_to_namespace(config)

config = load_config()

if __name__ == "__main__":
    print(json.dumps(config, default=lambda o: o.__dict__, indent=4))