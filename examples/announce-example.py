from meshtastic import BROADCAST_NUM
from mmqtt import (
    send_nodeinfo,
    send_position,
    send_device_telemetry,
    send_text_message,
    client,
)
import time


def main():
    client.server = "mqtt.meshtastic.org"
    client.user = "meshdev"
    client.password = "large4cats"
    client.port = 1883
    client.root_topic = "msh/US"
    client.channel = "LongFast"
    client.key = "AQ=="
    client.node_id = "!deadbee2"
    client.destination_id = BROADCAST_NUM

    # client.enable_verbose(True)
    client.connect()
    client.subscribe()

    # NodeInfo: node_id, long_name, short_name, hw_model
    send_nodeinfo(client.node_id, "My Long Name", "shor")
    time.sleep(1)

    # Position: lat, lon, altitude, precision
    send_position(latitude=37.7749, longitude=-122.4194, altitude=10, precision=3)
    time.sleep(1)

    # Telemetry: battery_level, voltage, chutil, airtxutil, uptime
    send_device_telemetry(
        battery_level=50, voltage=3.7, chutil=25, airtxutil=15, uptime=123456
    )
    time.sleep(1)

    # Simple text message
    send_text_message("Hello, Meshtastic!", to=182032979)

    if not client.verbose:
        client.disconnect()
        return

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDisconnecting...")
        client.disconnect()


if __name__ == "__main__":
    main()
