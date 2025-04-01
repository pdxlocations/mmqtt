import time
import re
import random

from meshtastic import portnums_pb2, mesh_pb2, mqtt_pb2, telemetry_pb2
from mmqtt.utils import generate_hash, get_message_id
from mmqtt.encryption import encrypt_packet
from mmqtt.load_config import ConfigLoader
from mmqtt.mqtt_handler import get_mqtt_client

_config = None

def _get_config():
    global _config
    if _config is None:
        _config = ConfigLoader.get_config()
    return _config

message_id = random.getrandbits(32)

def publish_message(payload_function, portnum, **kwargs):
    """Send a message of any type."""
    try:
        config = _get_config()
        client = get_mqtt_client()
        payload = payload_function(portnum=portnum, **kwargs)
        topic = f"{config.mqtt.root_topic}{config.channel.preset}/{config.nodeinfo.id}"
        client.publish(topic, payload)
    except Exception as e:
        print(f"Error while sending message: {e}")

def create_payload(data, portnum, want_response=False, bitfield=1):
    """Generalized function to create a payload."""
    encoded_message = mesh_pb2.Data()
    encoded_message.portnum = portnum
    encoded_message.payload = data.SerializeToString() if hasattr(data, "SerializeToString") else data
    encoded_message.want_response = want_response
    encoded_message.bitfield = bitfield
    return generate_mesh_packet(encoded_message)

def generate_mesh_packet(encoded_message):
    """Generate the final mesh packet."""
    config = _get_config()
    global message_id
    message_id = get_message_id(message_id)
    
    mesh_packet = mesh_pb2.MeshPacket()
    mesh_packet.id = message_id
    setattr(mesh_packet, "from", config.nodeinfo.number)
    mesh_packet.to = int(config.message.destination_id)
    mesh_packet.want_ack = False
    mesh_packet.channel = generate_hash(config.channel.preset, config.channel.key)
    mesh_packet.hop_limit = 3
    mesh_packet.hop_start = 3

    if config.channel.key == "":
        mesh_packet.decoded.CopyFrom(encoded_message)
    else:
        mesh_packet.encrypted = encrypt_packet(config.channel.preset, config.channel.key, mesh_packet, encoded_message)

    service_envelope = mqtt_pb2.ServiceEnvelope()
    service_envelope.packet.CopyFrom(mesh_packet)
    service_envelope.channel_id = config.channel.preset
    service_envelope.gateway_id = config.nodeinfo.id

    return service_envelope.SerializeToString()

########## Specific Message Handlers ##########

def send_text_message(message):
    """Send a text message."""
    def create_text_payload(portnum, message_text):
        data = message_text.encode("utf-8")
        return create_payload(data, portnum)
    
    publish_message(create_text_payload, portnums_pb2.TEXT_MESSAGE_APP, message_text=message)

def send_nodeinfo(long_name, short_name, hw_model):
    """Send node information."""
    def create_nodeinfo_payload(portnum, node_long_name, node_short_name, node_hw_model):
        config = _get_config()
        data = mesh_pb2.User(
            id=config.nodeinfo.id,
            long_name=node_long_name,
            short_name=node_short_name,
            hw_model=node_hw_model
        )
        return create_payload(data, portnum)
    
    publish_message(create_nodeinfo_payload, portnums_pb2.NODEINFO_APP, 
                 node_long_name=long_name, node_short_name=short_name, node_hw_model=hw_model)

def send_position(lat, lon, alt, pre):
    """Send position details."""
    def create_position_payload(portnum, lat, lon, alt, pre):
        pos_time = int(time.time())
        latitude = int(float(lat) * 1e7)
        longitude = int(float(lon) * 1e7)
        altitude_units = 1 / 3.28084 if 'ft' in str(alt) else 1.0
        altitude = int(altitude_units * float(re.sub('[^0-9.]', '', str(alt))))

        data = mesh_pb2.Position(
            latitude_i=latitude,
            longitude_i=longitude,
            altitude=altitude,
            time=pos_time,
            location_source="LOC_MANUAL",
            precision_bits=pre
        )
        return create_payload(data, portnum)

    publish_message(create_position_payload, portnums_pb2.POSITION_APP, lat=lat, lon=lon, alt=alt, pre=pre)

def send_device_telemetry(battery_level, voltage, chutil, airtxutil, uptime):
    """Send telemetry data."""
    def create_telemetry_payload(portnum, battery_level, voltage, chutil, airtxutil, uptime):
        data = telemetry_pb2.Telemetry(
            time=int(time.time()),
            device_metrics=telemetry_pb2.DeviceMetrics(
                battery_level=battery_level,
                voltage=voltage,
                channel_utilization=chutil,
                air_util_tx=airtxutil,
                uptime_seconds=uptime
            )
        )
        return create_payload(data, portnum)

    publish_message(create_telemetry_payload, portnums_pb2.TELEMETRY_APP, 
                 battery_level=battery_level, voltage=voltage, chutil=chutil, airtxutil=airtxutil, uptime=uptime)