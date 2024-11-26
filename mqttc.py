#!/usr/bin/env python3
"""
Powered by Meshtastic™ https://meshtastic.org/
"""

import time
from load_config import ConfigLoader
from tx_message_handler import send_nodeinfo, send_position, send_device_telemetry, send_text_message
from mqtt_handler import connect_mqtt
# from argument_parser import handle_args, get_args

stay_connected = False

def main():
    config = ConfigLoader.load_config_file('config.json')
    

    client = connect_mqtt()

    # if handle_args(client) == None:

    send_nodeinfo(client, config.node.short_name, config.node.long_name, config.node.hw_model)
    time.sleep(3)

    send_position(client, config.node.lat, config.node.lon, config.node.alt, config.node.precision)
    time.sleep(3)

    send_device_telemetry(client, battery_level=99, voltage=4.0, chutil=3, airtxutil=1, uptime=420)
    time.sleep(3)

    send_text_message(client, "Happy New Year!")
    time.sleep(3)


    if not stay_connected:
        client.disconnect()
    else:
        while True:
            time.sleep(1)

if __name__ == "__main__":
    main()