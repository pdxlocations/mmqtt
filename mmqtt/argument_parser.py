import argparse
import time

from mmqtt.load_config import ConfigLoader
from mmqtt.utils import validate_lat_lon_alt
from mmqtt.tx_message_handler import send_position, send_text_message, send_nodeinfo, send_device_telemetry

def get_args():
    """Define and parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Meshtastic MQTT client")
    parser.add_argument('--config', type=str, default='config.json', help='Path to the config file')
    parser.add_argument('--message', type=str, help='The message to send')
    parser.add_argument('--lat', type=float, help='Latitude coordinate')
    parser.add_argument('--lon', type=float, help='Longitude coordinate')
    parser.add_argument('--alt', type=float, help='Altitude')
    parser.add_argument('--precision', type=int, help='Position Precision')
    parser.add_argument('--nodeinfo', action='store_true', help='Send NodeInfo from my config')
    parser.add_argument('--telemetry', action='store_true', help='Send telemetry from my config')

    args = parser.parse_args()
    return parser, args

def handle_args():
    parser, args = get_args()
    
    if args.message:
        config = ConfigLoader.get_config()
        send_text_message(args.message)
        print(f"Sending message Packet to {str(config.message.destination_id)}")
        time.sleep(3)
        return args

    if args.lat or args.lon:
        config = ConfigLoader.get_config()
        parser, args = get_args()
        validate_lat_lon_alt(parser, args)
        alt = args.alt if args.alt else 0
        pre = args.precision if args.precision else 16
        send_position(args.lat, args.lon, alt, pre)
        print(f"Sending Position Packet to {str(config.message.destination_id)}")
        time.sleep(3)
        return args
    
    if args.nodeinfo:
        config = ConfigLoader.get_config()
        node = config.nodeinfo
        send_nodeinfo(node.short_name, node.long_name, node.hw_model)
        print(f"Sending NodeInfo:\n  Short Name: {node.short_name}\n  Long Name: {node.long_name}\n  Hardware Model: {node.hw_model}")
        time.sleep(3)

    if args.telemetry:
        config = ConfigLoader.get_config()
        telemetry = config.telemetry

        send_device_telemetry(
            battery_level=telemetry.battery_level,
            voltage=telemetry.voltage,
            chutil=telemetry.chutil,
            airtxutil=telemetry.airtxutil,
            uptime=telemetry.uptime
        )

        print(
            f"Sending Telemetry:\n"
            f"  Battery Level: {str(telemetry.battery_level)}%\n"
            f"  Voltage: {str(telemetry.voltage)}V\n"
            f"  Channel Utilization: {str(telemetry.chutil)}%\n"
            f"  Air Tx Utilization: {str(telemetry.airtxutil)}%\n"
            f"  Uptime: {str(telemetry.uptime)}s"
        )
        time.sleep(3)