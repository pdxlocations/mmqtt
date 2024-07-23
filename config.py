#!/usr/bin/env python3

### Broker Settings
mqtt_broker = "mqtt.meshtastic.org"
mqtt_port = 1883
mqtt_username = "meshdev"
mqtt_password = "large4cats"
root_topic = "msh/US/2/e/"

### Channel & PSK Settings
channel = "LongFast"
key = "AQ=="

### Node Settings
node_name = '!deadbeef'
node_number = int(node_name.replace("!", ""), 16) # Convert hex to int and remove '!'
client_short_name = "MMC"
client_long_name = "MQTTastic"
lat = None
lon = None
alt = None
client_hw_model = 255
