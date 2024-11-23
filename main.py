#!/usr/bin/env python3
"""
Powered by Meshtastic™ https://meshtastic.org/
"""

import time
import paho.mqtt.client as mqtt
from meshtastic import BROADCAST_NUM

from tx_message_handler import send_nodeinfo
from rx_message_handler import on_message
from load_config import (
    mqtt_broker, mqtt_port, mqtt_username, mqtt_password
)
from mqtt import connect_mqtt, on_connect, on_disconnect
from argument_parser import get_args, handle_args

stay_connected = False

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="", clean_session=True, userdata=None)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

connect_mqtt(client, mqtt_broker, mqtt_port, mqtt_username, mqtt_password)
client.loop_start()
time.sleep(1)

send_nodeinfo(client)
time.sleep(3)

parser, args = get_args()
handle_args(client, args)

if not stay_connected:
    client.disconnect()
else:
    while True:
        time.sleep(1)