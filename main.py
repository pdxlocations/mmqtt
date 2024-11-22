#!/usr/bin/env python3
"""
Powered by Meshtastic™ https://meshtastic.org/
"""

import time
import paho.mqtt.client as mqtt
from meshtastic import BROADCAST_NUM

from tx_message_handler import create_nodeinfo_payload, create_position_payload, create_text_payload, publish_message
from rx_message_handler import on_message
from load_config import (
    mqtt_broker, mqtt_port, mqtt_username, mqtt_password, channel, 
    key, node_id, node_short_name,
    node_long_name, lat, lon, alt, node_hw_model, destination_id
)
from mqtt import connect_mqtt, on_connect, on_disconnect
from argument_parser import get_args, handle_args

# Configuration
auto_reconnect = True
auto_reconnect_delay = 1  # seconds
stay_connected = False

parser, args = get_args()

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="", clean_session=True, userdata=None)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

connect_mqtt(client, mqtt_broker, mqtt_port, mqtt_username, mqtt_password)
client.loop_start()
time.sleep(1)


# Send initial node info payload
publish_message(
    create_nodeinfo_payload,
    client=client,
    node_id=node_id,
    destination_id=destination_id,
    node_long_name=node_long_name,
    node_short_name=node_short_name,
    node_hw_model=node_hw_model,
    channel=channel,
    key=key,
    want_response=False
)

time.sleep(3)

handle_args(client, args)

if not stay_connected:
    client.disconnect()
else:
    while True:
        time.sleep(1)