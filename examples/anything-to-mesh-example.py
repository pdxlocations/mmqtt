import time
import json
from meshtastic import BROADCAST_NUM
from paho.mqtt.client import MQTTMessage
from mmqtt import send_environment_metrics, send_nodeinfo, client


def handle_sensor_message(mqtt_client, userdata, msg: MQTTMessage):
    try:
        if not msg.payload.strip().startswith(b"{"):
            return  # Ignore non-JSON payloads

        payload = json.loads(msg.payload.decode("utf-8"))
        print()
        print(f"[MQTT] Received sensor data: {payload}")

        # Send any matching sensor data to the Mesh
        send_environment_metrics(
            temperature=payload.get("temperature"),
            relative_humidity=payload.get("humidity"),
            barometric_pressure=payload.get("pressure"),
        )
    except Exception as e:
        print(f"[ERROR] Failed to process incoming MQTT message: {e}")


def main():
    client.server = "mqtt.meshtastic.org"
    client.port = 1883
    client.user = "meshdev"
    client.password = "large4cats"
    client.root_topic = "msh/US"
    client.channel = "LongFast"
    client.key = "AQ=="
    client.node_id = "!1ceface1"
    client.destination_id = BROADCAST_NUM
    client.enable_verbose(True)
    client.connect()
    client.client.on_message = handle_sensor_message

    # Subscribe to external sensor topic, publish to preset topic
    subscribe_topic = "home/sensors/#"
    client.client.subscribe(subscribe_topic)
    print(f"[MQTT] Subscribed to custom topic: {subscribe_topic}")

    send_nodeinfo(client.node_id, "Temperature Sensor", "temp")
    time.sleep(1)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDisconnecting...")
        client.disconnect()


if __name__ == "__main__":
    main()
