import os
import json

### Load Config
# Get the directory where the script is located to build the path for the config file
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.json')

# Load configuration from the config.py file
config = {}
if os.path.exists(config_path):
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
else:
    raise FileNotFoundError(f"Configuration file not found: {config_path}")

# Extract MQTT settings
mqtt_broker = config["mqtt"]["broker"]
mqtt_port = config["mqtt"]["port"]
mqtt_username = config["mqtt"]["user"]
mqtt_password = config["mqtt"]["pass"]
root_topic = config["mqtt"]["root_topic"]

# Extract channel settings
channel = config["channel"]["preset"]
key = config["channel"]["key"]

# Extract node settings
node_name = config["node"]["id"]
node_short_name = config["node"]["short_name"]
node_long_name = config["node"]["long_name"]
lat = config["node"]["lat"]
lon = config["node"]["lon"]
alt = config["node"]["alt"]
node_hw_model = config["node"]["hw_model"]

# Calculate node_number from node_name
node_number = int(node_name.replace("!", ""), 16)

# Get the full default key
key = "1PG7OiApB1nwvP+rz05pAQ==" if key == "AQ==" else key