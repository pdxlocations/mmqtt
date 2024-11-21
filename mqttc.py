#!/usr/bin/env python3
"""
Powered by Meshtastic™ https://meshtastic.org/
"""

from meshtastic import BROADCAST_NUM
import paho.mqtt.client as mqtt
import random
import time
import ssl
import argparse

from tx_message_handler import create_nodeinfo_payload, create_position_payload, create_text_payload
from utils import validate_lat_lon_alt
from rx_message_handler import on_message
from load_config import (
    mqtt_broker, mqtt_port, mqtt_username, mqtt_password,
    root_topic, channel, key, node_id, node_short_name,
    node_long_name, lat, lon, alt, node_hw_model, node_number
)

#### Debug Options
debug = True
auto_reconnect = True
auto_reconnect_delay = 1 # seconds
stay_connected = False

message_id = random.getrandbits(32)

#### Parser Arguments
parser = argparse.ArgumentParser(add_help=True)
parser.add_argument('--config', type=str, default='config.py', help='Path to the config file')
parser.add_argument('--message', type=str, help='The message to send')
parser.add_argument('--lat', type=float, help='Latitude coordinate')
parser.add_argument('--lon', type=float, help='Longitude coordinate')
parser.add_argument('--alt', type=float, help='Altitude')
args = parser.parse_args()


#################################
# Program Base Functions
    
def set_topic():
    if debug: print(f"set_topic: {root_topic}{channel}/")

    node_name = '!' + hex(node_number)[2:]
    subscribe_topic = root_topic + channel + "/#"
    publish_topic = root_topic + channel + "/" + node_name

    return subscribe_topic, publish_topic



#################################
# MQTT Server 
    
def connect_mqtt():

    if "tls_configured" not in connect_mqtt.__dict__:
        connect_mqtt.tls_configured = False

    global mqtt_broker, mqtt_port, mqtt_username, mqtt_password, root_topic, channel, node_number, key
    if not client.is_connected():
        if debug: print("connect_mqtt")
        try:
            if ':' in mqtt_broker:
                mqtt_broker,mqtt_port = mqtt_broker.split(':')
                mqtt_port = int(mqtt_port)

            padded_key = key.ljust(len(key) + ((4 - (len(key) % 4)) % 4), '=')
            replaced_key = padded_key.replace('-', '+').replace('_', '/')
            key = replaced_key

            client.username_pw_set(mqtt_username, mqtt_password)
            if mqtt_port == 8883 and connect_mqtt.tls_configured == False:
                client.tls_set(ca_certs="cacert.pem", tls_version=ssl.PROTOCOL_TLSv1_2)
                client.tls_insecure_set(False)
                connect_mqtt.tls_configured = True
            client.connect(mqtt_broker, mqtt_port, 60)
        except Exception as e:
            print (e)
        

def on_disconnect(client, userdata, flags, reason_code, properties):
    if debug: print("client is disconnected")
    if reason_code != 0:
        if auto_reconnect == True:
            print("attempting to reconnect in " + str(auto_reconnect_delay) + " second(s)")
            time.sleep(auto_reconnect_delay)
            connect_mqtt()

def on_connect(client, userdata, flags, reason_code, properties):
    set_topic()
    if client.is_connected():
        print("client is connected")
    
    if reason_code == 0:
        subscribe_topic, publish_topic = set_topic()
        if debug: print(f"Publish Topic is: {publish_topic}")
        if debug: print(f"Subscribe Topic is: {subscribe_topic}")
        client.subscribe(subscribe_topic)
    else:
        print("Failed to connect, return code %d\n", reason_code)

############################
# Main 


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="", clean_session=True, userdata=None)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

connect_mqtt()
client.loop_start()
time.sleep(1)

print (node_long_name)

destination_id = BROADCAST_NUM
payload = create_nodeinfo_payload(node_id, destination_id, node_long_name, node_short_name, node_hw_model, message_id, channel, key, want_response=False)
client.publish(root_topic + channel + "/" + node_id, payload)
if debug: print("create_nodeinfo_payload")

time.sleep(3)

if args.message:
    destination_id = BROADCAST_NUM
    payload = create_text_payload(node_id, destination_id, channel, key, args.message)
    client.publish(root_topic + channel + "/" + node_id, payload)
    if debug: print("create_text_payload")
    time.sleep(3)

if args.lat:
    validate_lat_lon_alt(parser, args)
    lat = args.lat
    lon = args.lon
    if args.alt:
        alt = args.alt

    destination_id = BROADCAST_NUM
    payload = create_position_payload(node_id, destination_id, message_id, channel, key, lat, lon, alt=0)
    client.publish(root_topic + channel + "/" + node_id, payload)

    if debug: print(f"Sending Position Packet to {str(destination_id)}")

    time.sleep(3)

if not stay_connected:
    client.disconnect()
else:
    while True:
        time.sleep(1)
    