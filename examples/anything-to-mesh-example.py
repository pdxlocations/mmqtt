import time
import json
from meshtastic import BROADCAST_NUM
from paho.mqtt.client import MQTTMessage
from mmqtt import send_environment_metrics, send_nodeinfo, client

# Subscribe to external sensor topic, publish to preset topic
subscribe_topic = "home/sensors/#"


def handle_sensor_message(mqtt_client, userdata, msg: MQTTMessage):
    try:
        if not msg.payload.strip().startswith(b"{"):
            return  # Ignore non-JSON payloads

        raw = json.loads(msg.payload.decode("utf-8"))

        payload = lowercase_keys(raw)
        print()
        print(f"[MQTT] Received sensor data: {payload}")

        # Convert temperature from Fahrenheit to Celsius if present
        temperature_f = find_first_key(payload, "temperature")
        temperature_c = (
            float(f"{(temperature_f - 32) * 5 / 9:.2f}")
            if temperature_f is not None
            else None
        )

        # Send any matching sensor data to the Mesh
        send_environment_metrics(
            temperature=temperature_c,
            relative_humidity=find_first_key(payload, "humidity"),
            barometric_pressure=find_first_key(payload, "pressure"),
        )
    except Exception as e:
        print(f"[ERROR] Failed to process incoming MQTT message: {e}")


def lowercase_keys(obj):
    if isinstance(obj, dict):
        return {k.lower(): lowercase_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [lowercase_keys(i) for i in obj]
    return obj


def find_first_key(obj, key):
    """
    Recursively search nested dictionaries and lists for the first occurrence of a given key.
    Returns the corresponding value if found, otherwise returns None.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                return v
            found = find_first_key(v, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_first_key(item, key)
            if found is not None:
                return found
    return None


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
