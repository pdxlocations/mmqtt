import argparse
import time
import sys
from types import SimpleNamespace
from typing import Tuple

from mmqtt.load_config import ConfigLoader
from mmqtt.utils import validate_lat_lon_alt
from mmqtt.tx_message_handler import (
    send_position,
    send_text_message,
    send_nodeinfo,
    send_device_telemetry,
)


def get_args() -> Tuple[argparse.ArgumentParser, argparse.Namespace]:
    """Define and parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Meshtastic MQTT client")

    parser.add_argument('--config', type=str, default='config.json', help='Path to the config file')
    parser.add_argument('--message', action='append', help='Message(s) to send. You can use this multiple times.')
    parser.add_argument('--message-file', type=str, help='Path to a file containing messages, one per line')
    parser.add_argument('--nodeinfo', action='store_true', help='Send NodeInfo from my config')
    parser.add_argument('--telemetry', action='store_true', help='Send telemetry from my config')
    parser.add_argument('--lat', type=float, help='Latitude coordinate')
    parser.add_argument('--lon', type=float, help='Longitude coordinate')
    parser.add_argument('--alt', type=float, help='Altitude')
    parser.add_argument('--precision', type=int, help='Position Precision')
    parser.add_argument('--position', action='store_true', help='Send position from config or overridden by --lat/lon/alt')
    parser.add_argument('--listen', action='store_true', help='Enable listening for incoming MQTT messages')
    # parser.add_argument('--use-args', action='store_true', help='Use values from config.json instead of client attributes')

    args = parser.parse_args()
    return parser, args


def handle_args() -> argparse.Namespace:
    """
    Process and handle CLI arguments to trigger various MQTT message actions.
    Returns:
        argparse.Namespace: Parsed argument namespace
    """
    parser, args = get_args()
    config: SimpleNamespace = ConfigLoader.get_config(args.config)

    arg_order = sys.argv[1:]

    messages = args.message or []

    for arg in arg_order:
        if arg == "--nodeinfo" and args.nodeinfo:
            node = config.nodeinfo
            send_nodeinfo(node.id, node.long_name, node.short_name, use_args=True)
            time.sleep(3)
            
        elif arg == "--message" and messages:
            for msg in messages:
                send_text_message(msg, use_args=True)
                time.sleep(3)
            messages = []  # prevent duplicate sending

        elif arg == "--message-file" and args.message_file:
            try:
                with open(args.message_file, 'r', encoding='utf-8') as f:
                    file_lines = [line.strip() for line in f if line.strip()]
                    for msg in file_lines:
                        send_text_message(msg, use_args=True)
                        time.sleep(3)
            except FileNotFoundError:
                print(f"Message file '{args.message_file}' not found.")

        elif arg == "--position" and args.position:
            position = config.position
            lat = args.lat if args.lat is not None else position.lat
            lon = args.lon if args.lon is not None else position.lon
            alt = args.alt if args.alt is not None else position.alt
            precision = args.precision if args.precision is not None else position.precision
            validate_lat_lon_alt(parser, argparse.Namespace(lat=lat, lon=lon, alt=alt))
            send_position(lat, lon, alt, precision, use_args=True)
            time.sleep(3)

        elif arg == "--telemetry" and args.telemetry:
            telemetry = config.telemetry
            send_device_telemetry(
                battery_level=telemetry.battery_level,
                voltage=telemetry.voltage,
                chutil=telemetry.chutil,
                airtxutil=telemetry.airtxutil,
                uptime=telemetry.uptime,
                use_args=True
            )
            time.sleep(3)

    # Listen Mode
    if args.listen:
        from mmqtt import client
        client.enable_verbose(True)
        config.listen_mode = True
        
        print("Starting MQTT listener (press Ctrl+C to stop)...")

        client.subscribe()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Exiting listener.")
            client.disconnect()

    return args