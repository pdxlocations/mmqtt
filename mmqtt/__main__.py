#!/usr/bin/env python3
"""
mmqtt - An MQTT library for Meshtastic by http://github.com/pdxlocations
Powered by Meshtastic.org

Meshtastic® is a registered trademark of Meshtastic LLC.
Meshtastic software components are released under various licenses—see GitHub for details.
No warranty is provided. Use at your own risk.
"""

import time
from mmqtt.load_config import ConfigLoader
from mmqtt.argument_parser import handle_args, get_args
from mmqtt import configure, connect, disconnect, enable_verbose

def main() -> None:
    """Entrypoint for the mmqtt client. Parses args, loads config, and starts the client."""
    _, args = get_args()
    config = ConfigLoader.load_config_file(args.config)
    configure(config)

    if args.listen:
        enable_verbose(True)

    connect()
    handle_args()

    if config.mode.listen:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Disconnected cleanly on exit.")
    disconnect()
            
if __name__ == "__main__":
    main()