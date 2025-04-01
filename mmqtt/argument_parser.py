import argparse
import time

from mmqtt.load_config import ConfigLoader
from mmqtt.utils import validate_lat_lon_alt
from mmqtt.tx_message_handler import (
    send_position,
    send_text_message,
    send_nodeinfo,
    send_device_telemetry,
)

def get_args():
    """Define and parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Meshtastic MQTT client")
    parser.add_argument('--config', type=str, default='config.json', help='Path to the config file')
    parser.add_argument('--message', type=str, help='The message to send')
    parser.add_argument('--nodeinfo', action='store_true', help='Send NodeInfo from my config')
    parser.add_argument('--telemetry', action='store_true', help='Send telemetry from my config')
    parser.add_argument('--lat', type=float, help='Latitude coordinate')
    parser.add_argument('--lon', type=float, help='Longitude coordinate')
    parser.add_argument('--alt', type=float, help='Altitude')
    parser.add_argument('--precision', type=int, help='Position Precision')
    parser.add_argument('--position', action='store_true', help='Send position from config unless overridden by --lat/lon/alt')

    args = parser.parse_args()
    return parser, args

def handle_args():
    parser, args = get_args()
    config = ConfigLoader.get_config()

    if args.message:
        send_text_message(args.message)
        print(f"Sending Message Packet to {config.message.destination_id}")
        time.sleep(3)
        return args

    if args.position:
        position = config.position

        lat = args.lat if args.lat is not None else position.lat
        lon = args.lon if args.lon is not None else position.lon
        alt = args.alt if args.alt is not None else position.alt
        precision = args.precision if args.precision is not None else position.precision

        validate_lat_lon_alt(parser, argparse.Namespace(lat=lat, lon=lon, alt=alt))

        send_position(lat, lon, alt, precision)
        print(f"Sending Position Packet to {config.message.destination_id}")
        time.sleep(3)
        return args

    if args.nodeinfo:
        node = config.nodeinfo
        send_nodeinfo(node.short_name, node.long_name, node.hw_model)
        print(
            "Sending NodeInfo:\n"
            f"  Short Name: {node.short_name}\n"
            f"  Long Name:  {node.long_name}\n"
            f"  Hardware Model: {node.hw_model}"
        )
        time.sleep(3)

    if args.telemetry:
        telemetry = config.telemetry
        send_device_telemetry(
            battery_level=telemetry.battery_level,
            voltage=telemetry.voltage,
            chutil=telemetry.chutil,
            airtxutil=telemetry.airtxutil,
            uptime=telemetry.uptime
        )
        print(
            "Sending Telemetry:\n"
            f"  Battery Level:        {telemetry.battery_level}%\n"
            f"  Voltage:              {telemetry.voltage}V\n"
            f"  Channel Utilization:  {telemetry.chutil}%\n"
            f"  Air Tx Utilization:   {telemetry.airtxutil}%\n"
            f"  Uptime:               {telemetry.uptime}s"
        )
        time.sleep(3)

    return args