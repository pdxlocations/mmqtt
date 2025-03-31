import os
import json
from types import SimpleNamespace
from meshtastic import BROADCAST_NUM

class ConfigLoader:
    _config = None

    @staticmethod
    def load_config_file(filename):
        if ConfigLoader._config is not None:
            return ConfigLoader._config  # Return already loaded config

        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, filename)

        # Fallback to config-example.json if config.json is missing
        if not os.path.exists(config_path):
            fallback_path = os.path.join(script_dir, "config-example.json")
            if os.path.exists(fallback_path):
                print(f"{filename} not found. Falling back to config-example.json.")
                config_path = fallback_path
            else:
                raise FileNotFoundError(f"Neither {filename} nor config-example.json found.")

        with open(config_path, 'r') as config_file:
            conf = json.load(config_file)

        # Expand default key
        conf["channel"]["key"] = "1PG7OiApB1nwvP+rz05pAQ==" if conf["channel"]["key"] == "AQ==" else conf["channel"]["key"]
        # Create keys not in config

        # Generate a random hexadecimal ID with a prefixed "!"
        import random
        random_hex_id = f"!{random.randint(0x100000, 0xFFFFFF):X}"


        conf["node"]["number"] = int(random_hex_id.replace("!", ""), 16)
        conf["destination_id"] = 4204600028
        print (f"my id is {conf['node']['number']}")
        # Convert to nested SimpleNamespace
        def dict_to_namespace(data):
            if isinstance(data, dict):
                return SimpleNamespace(**{k: dict_to_namespace(v) for k, v in data.items()})
            return data

        ConfigLoader._config = dict_to_namespace(conf)
        return ConfigLoader._config

    @staticmethod
    def get_config():
        if ConfigLoader._config is None:
            raise ValueError("Config has not been loaded yet.")
        return ConfigLoader._config


if __name__ == "__main__":
    config = ConfigLoader.load_config_file('config.json')
    print(json.dumps(config, default=lambda o: o.__dict__, indent=4))