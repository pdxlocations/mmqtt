from meshtastic import BROADCAST_NUM
from mmqtt import (
    send_nodeinfo,
    send_position,
    send_device_telemetry,
    send_text_message,
    send_power_metrics,
    send_environment_metrics,
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

    # Power metrics: ch1_voltage, ch1_current, ch2_voltage, ch2_current, ch3_voltage, ch3_current
    send_power_metrics(
        ch1_voltage=18.744,
        ch1_current=11.2,
        ch2_voltage=2.792,
        ch2_current=18.4,
        ch3_voltage=0,
        ch3_current=0,
    )
    time.sleep(1)

    # Environment: temperature, relative_humidity, barometric_pressure, gas_resistance (keys are optional)
    send_environment_metrics(
        temperature=23.072298,
        relative_humidity=17.5602016,
        barometric_pressure=995.36261,
        gas_resistance=229.093369,
        voltage=5.816,
        current=-29.3,
        iaq=66,
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
