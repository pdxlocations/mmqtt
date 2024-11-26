import argparse
import time

from load_config import destination_id
from utils import validate_lat_lon_alt
from tx_message_handler import send_position, send_text_message

def get_args():
    """Define and parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Meshtastic MQTT client")
    parser.add_argument('--config', type=str, default='config.json', help='Path to the config file')
    parser.add_argument('--message', type=str, help='The message to send')
    parser.add_argument('--lat', type=float, help='Latitude coordinate')
    parser.add_argument('--lon', type=float, help='Longitude coordinate')
    parser.add_argument('--alt', type=float, help='Altitude')
    parser.add_argument('--pre', type=int, help='Position Precision')

    args = parser.parse_args()
    return parser, args

def handle_args(client):
    parser, args = get_args()

    if args == None:
        print ("no args")
        return None
    
    if args.message:
        send_text_message(client, args.message)
        print(f"Sending message Packet to {str(destination_id)}")
        time.sleep(3)
        return args

    if args.lat or args.lon:
        parser, args = get_args()
        validate_lat_lon_alt(parser, args)
        alt = args.alt if args.alt else 0
        pre = args.pre if args.pre else 16
        send_position(client, args.lat, args.lon, alt, pre)
        print(f"Sending Position Packet to {str(destination_id)}")
        time.sleep(3)
        return args