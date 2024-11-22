import argparse
import time

from load_config import node_id, channel, key, root_topic, destination_id
from utils import validate_lat_lon_alt
from tx_message_handler import create_position_payload, create_text_payload

def get_args():
    """Define and parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Meshtastic MQTT client")
    parser.add_argument('--config', type=str, default='config.json', help='Path to the config file')
    parser.add_argument('--message', type=str, help='The message to send')
    parser.add_argument('--lat', type=float, help='Latitude coordinate')
    parser.add_argument('--lon', type=float, help='Longitude coordinate')
    parser.add_argument('--alt', type=float, help='Altitude')
    args = parser.parse_args()
    return parser, args





