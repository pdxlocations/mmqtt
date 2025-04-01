#!/usr/bin/env python3
"""
Powered by Meshtastic™ https://meshtastic.org/
"""

import time
from mmqtt.load_config import ConfigLoader
from mmqtt.mqtt_handler import get_mqtt_client
from mmqtt.argument_parser import handle_args, get_args

stay_connected = False

def main():
    _, args = get_args()
    config_file = args.config
    config = ConfigLoader.load_config_file(config_file)
    client = get_mqtt_client()
    handle_args() 
    
    if config.mode.listen == False:
        client.disconnect()
    else:
        while True:
            time.sleep(1)

if __name__ == "__main__":
    main()