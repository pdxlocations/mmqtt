#!/usr/bin/env python3
"""
Powered by Meshtastic™ https://meshtastic.org/
"""

import time
from mmqtt.load_config import ConfigLoader
from mmqtt.mqtt_handler import get_mqtt_client
from mmqtt.argument_parser import handle_args, get_args

stay_connected = False

def main() -> None:
    """Entrypoint for the mmqtt client. Parses args, loads config, and starts the client."""
    _, args = get_args()
    config_file = args.config
    config = ConfigLoader.load_config_file(config_file)
    client = get_mqtt_client()
    handle_args() 
    
    if not config.mode.listen:
        client.disconnect()
    else:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            client.disconnect()
            print("Disconnected cleanly on exit.")
            
if __name__ == "__main__":
    main()