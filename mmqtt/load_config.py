import os
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Union

class ConfigLoader:
    _config: Union[SimpleNamespace, None] = None

    @staticmethod
    def load_config_file(filename: str) -> SimpleNamespace:
        if ConfigLoader._config is not None:
            return ConfigLoader._config

        script_dir = Path(__file__).resolve().parent
        config_path = script_dir / filename

        # Fallback logic
        if not os.path.exists(config_path):
            fallback_path = os.path.join(script_dir, "config-example.json")
            if os.path.exists(fallback_path):
                print(f"{filename} not found. Falling back to config-example.json.")
                config_path = fallback_path
            else:
                raise FileNotFoundError(f"Neither {filename} nor config-example.json found.")

        with open(config_path, 'r', encoding='utf-8') as f:
            conf: dict[str, Any] = json.load(f)

        # Expand channel key
        if conf.get("channel", {}).get("key") == "AQ==":
            conf["channel"]["key"] = "1PG7OiApB1nwvP+rz05pAQ=="

        # Generate node number if not present
        conf.setdefault("nodeinfo", {})
        conf["nodeinfo"]["number"] = int(conf["nodeinfo"]["id"].replace("!", ""), 16)

        # Normalize booleans
        conf.setdefault("mode", {})
        if isinstance(conf["mode"].get("listen"), str):
            conf["mode"]["listen"] = conf["mode"]["listen"].lower() == "true"

        ConfigLoader._config = ConfigLoader.dict_to_namespace(conf)
        return ConfigLoader._config
    
    @staticmethod
    def dict_to_namespace(data: Any) -> Any:
        if isinstance(data, dict):
            return SimpleNamespace(**{k: ConfigLoader.dict_to_namespace(v) for k, v in data.items()})
        return data
    
    @staticmethod
    def get_config(path: str = "config.json") -> SimpleNamespace:
        if ConfigLoader._config is None:
            ConfigLoader.load_config_file(path)
        return ConfigLoader._config

    @staticmethod
    def save_config_file(path: str = "config.json") -> None:
        if ConfigLoader._config:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(ConfigLoader._config, f, default=lambda o: o.__dict__, indent=4)

if __name__ == "__main__":
    config = ConfigLoader.load_config_file('config.json')
    print(json.dumps(config, default=lambda o: o.__dict__, indent=4))