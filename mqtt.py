import time
import ssl
from load_config import root_topic, channel, node_number


def set_topic():
    print(f"set_topic: {root_topic}{channel}/")

    node_name = '!' + hex(node_number)[2:]
    subscribe_topic = root_topic + channel + "/#"
    publish_topic = root_topic + channel + "/" + node_name

    return subscribe_topic, publish_topic


def connect_mqtt(client, mqtt_broker, mqtt_port, mqtt_username, mqtt_password):

    if "tls_configured" not in connect_mqtt.__dict__:
        connect_mqtt.tls_configured = False

    if not client.is_connected():
        try:
            if ':' in mqtt_broker:
                mqtt_broker,mqtt_port = mqtt_broker.split(':')
                mqtt_port = int(mqtt_port)

            client.username_pw_set(mqtt_username, mqtt_password)
            if mqtt_port == 8883 and connect_mqtt.tls_configured == False:
                client.tls_set(ca_certs="cacert.pem", tls_version=ssl.PROTOCOL_TLSv1_2)
                client.tls_insecure_set(False)
                connect_mqtt.tls_configured = True
            client.connect(mqtt_broker, mqtt_port, 60)
        except Exception as e:
            print (e)
        

def on_disconnect(client, userdata, flags, reason_code, properties):
    global auto_reconnect
    global auto_reconnect_delay
    print("client is disconnected")
    if reason_code != 0:
        if auto_reconnect == True:
            print("attempting to reconnect in " + str(auto_reconnect_delay) + " second(s)")
            time.sleep(auto_reconnect_delay)
            connect_mqtt()

def on_connect(client, userdata, flags, reason_code, properties):

    if client.is_connected():
        print("client is connected")
    
    if reason_code == 0:
        subscribe_topic, publish_topic = set_topic()
        print(f"Publish Topic is: {publish_topic}")
        print(f"Subscribe Topic is: {subscribe_topic}")
        client.subscribe(subscribe_topic)
    else:
        print("Failed to connect, return code %d\n", reason_code)