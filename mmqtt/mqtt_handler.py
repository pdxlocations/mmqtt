import time
import ssl
import paho.mqtt.client as mqtt
from mmqtt.rx_message_handler import on_message
from mmqtt.load_config import ConfigLoader

_client_instance = None

auto_reconnect = True
auto_reconnect_delay = 1

def set_topic():
    config = ConfigLoader.get_config()
    print(f"set_topic: {config.mqtt.root_topic}{config.channel.preset}/")
    node_name = '!' + hex(config.nodeinfo.number)[2:]
    subscribe_topic = config.mqtt.root_topic + config.channel.preset + "/#"
    publish_topic = config.mqtt.root_topic + config.channel.preset + "/" + node_name
    return subscribe_topic, publish_topic

def get_mqtt_client():
    """Get or create the MQTT client instance."""
    global _client_instance

    if _client_instance is None:
        _client_instance = connect_mqtt()

    return _client_instance


def connect_mqtt():
    """Create and connect the MQTT client."""
    config = ConfigLoader.get_config()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="", clean_session=True, userdata=None)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    if "tls_configured" not in connect_mqtt.__dict__:
        connect_mqtt.tls_configured = False

    if not client.is_connected():
        try:
            if ':' in config.mqtt.broker:
                config.mqtt.broker, config.mqtt.port = config.mqtt.broker.split(':')
                config.mqtt.port = int(config.mqtt.port)
            client.username_pw_set(config.mqtt.user, config.mqtt.password)
            if config.mqtt.port == 8883 and not connect_mqtt.tls_configured:
                client.tls_set(ca_certs="cacert.pem", tls_version=ssl.PROTOCOL_TLSv1_2)
                client.tls_insecure_set(False)
                connect_mqtt.tls_configured = True
            client.connect(config.mqtt.broker, config.mqtt.port, 60)
        except Exception as e:
            print(e)

        client.loop_start()
        time.sleep(1)
    return client


def on_disconnect(client, userdata, flags, reason_code, properties=None):
    print("client is disconnected")
    if reason_code != 0:
        if auto_reconnect:
            print("attempting to reconnect in " + str(auto_reconnect_delay) + " second(s)")
            time.sleep(auto_reconnect_delay)
            connect_mqtt()


def on_connect(client, userdata, flags, reason_code, properties=None):
    if client.is_connected():
        print("client is connected")

    if reason_code == 0:
        subscribe_topic, publish_topic = set_topic()
        print(f"Publish Topic is: {publish_topic}")
        print(f"Subscribe Topic is: {subscribe_topic}")
        client.subscribe(subscribe_topic)
    else:
        print("Failed to connect, return code %d\n", reason_code)