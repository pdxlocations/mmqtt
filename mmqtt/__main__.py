#!/usr/bin/env python3
"""
Powered by Meshtastic™ https://meshtastic.org/
"""

import time
from mmqtt.load_config import ConfigLoader
from mmqtt.argument_parser import handle_args, get_args
from mmqtt import configure, connect, disconnect, enable_verbose

stay_connected = False

def main() -> None:
    """Entrypoint for the mmqtt client. Parses args, loads config, and starts the client."""
    _, args = get_args()
    config_file = args.config
    config = ConfigLoader.load_config_file(config_file)
    configure(config)


    enable_verbose(True)
    config.listen_mode = True
    
    connect()
    handle_args() 
    
    if not config.mode.listen:
        disconnect()
    else:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            disconnect()
            print("Disconnected cleanly on exit.")
            
if __name__ == "__main__":
    main()