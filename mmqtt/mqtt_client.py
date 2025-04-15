import paho.mqtt.client as mqtt

class Client:
    def __init__(self):
        self.server = None
        self.port = 1883
        self.user = None
        self.password = None
        self.root_topic = None
        self.channel = None
        self.key = None
        self.node_id = None
        self.destination_id = None
        
        self.client = mqtt.Client()
        self.connected = False
        self.verbose = False

    def enable_verbose(self, enabled: bool = True):
        self.verbose = enabled

    def configure(self, config):
        self.server = config.mqtt.broker
        self.port = getattr(config.mqtt, "port", 1883)
        self.user = getattr(config.mqtt, "user", None)
        self.password = getattr(config.mqtt, "password", None)
        self.root_topic = getattr(config.mqtt, "root_topic", "")
        self.channel = getattr(config.channel, "preset", None)
        self.node_id = getattr(config.nodeinfo, "id", None)
        self.destination_id = getattr(config.message, "destination_id", None)

    def connect(self):
        if self.user and self.password:
            self.client.username_pw_set(self.user, self.password)

        if self.verbose:
            from mmqtt.rx_message_handler import on_message
            self.client.on_message = on_message
            
        self.client.connect_async(self.server, self.port, 60)

        print(f"[MQTT] Connecting to {self.server}:{self.port}")
        if self.user:
            print(f"[MQTT] Username: {self.user}")
        print(f"[MQTT] Topic: {self.root_topic}/2/e/{self.channel}")
        self.client.loop_start()
        
        # Wait for connection confirmation (up to 10 seconds)
        import time
        max_wait = 10
        waited = 0
        while not self.client.is_connected() and waited < max_wait:
            time.sleep(0.5)
            waited += 0.5

        if self.client.is_connected():
            print("[MQTT] Connection successful")
            self.client.subscribe(f"{self.root_topic}/2/e/{self.channel}/#")
            print(f"[MQTT] Subscribed to topic: {self.root_topic}/2/e/{self.channel}/#")
        else:
            print("[MQTT] Connection failed after retrying for 10 seconds.")
        self.connected = True
        
    def subscribe(self):
        if self.root_topic:
            self.client.subscribe(f"{self.root_topic}/2/e/{self.channel}")

    def publish(self, topic, payload):
        if self.connected:
            self.client.publish(topic, payload)

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        self.connected = False
