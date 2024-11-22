import argparse
import time

from load_config import node_id, channel, key, root_topic, destination_id
from utils import validate_lat_lon_alt
from tx_message_handler import create_position_payload, create_text_payload, publish_message

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



def handle_args(client, args):
    
    if args.message:
        publish_message(
            create_text_payload,
            client=client,
            node_id=node_id,
            destination_id=destination_id,
            channel=channel,
            key=key,
            message_text=args.message
        )
        time.sleep(3)

    # Handle position arguments
    if args.lat or args.lon:
        parser, args = get_args()
        validate_lat_lon_alt(parser, args)
        lat = args.lat
        lon = args.lon
        alt = args.alt if args.alt else 0

        publish_message(
            create_position_payload,
            client=client,
            node_id=node_id,
            destination_id=destination_id,
            channel=channel,
            key=key,
            lat=lat,
            lon=lon,
            alt=alt
        )
        print(f"Sending Position Packet to {str(destination_id)}")
        time.sleep(3)

