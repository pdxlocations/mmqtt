import time
import re
import random

from meshtastic import portnums_pb2, mesh_pb2, mqtt_pb2, telemetry_pb2

from utils import generate_hash
from encryption import encrypt_packet
from load_config import root_topic, channel, node_id, destination_id, node_long_name, node_short_name, node_hw_model, node_number, key

message_id = random.getrandbits(32)

########## TEXT MESSAGE ##########
def send_text_message(client, message):
    """Send a text message."""
    message_content = {
        "message_text": message,
        "bitfield" : 1
    }
    publish_message(create_text_payload, client, **message_content)

def create_text_payload(message_text):
    """Create a text message payload."""
    encoded_message = mesh_pb2.Data()
    encoded_message.portnum = portnums_pb2.TEXT_MESSAGE_APP 
    encoded_message.payload = message_text.encode("utf-8")
    encoded_message.bitfield = 1
    payload = generate_mesh_packet(encoded_message)
    return payload

########## NODEINFO ##########
def send_nodeinfo(client):
    """Send node information."""
    message_content = {
        "node_long_name": node_long_name,
        "node_short_name": node_short_name,
        "node_hw_model": node_hw_model,
        "want_response": False
    }
    publish_message(create_nodeinfo_payload, client, **message_content)

def create_nodeinfo_payload(node_long_name, node_short_name, node_hw_model, want_response):
    """Create a node information payload."""
    nodeinfo_payload = mesh_pb2.User()
    setattr(nodeinfo_payload, "id", node_id)
    setattr(nodeinfo_payload, "long_name", node_long_name)
    setattr(nodeinfo_payload, "short_name", node_short_name)
    setattr(nodeinfo_payload, "hw_model", node_hw_model)

    nodeinfo_payload = nodeinfo_payload.SerializeToString()

    encoded_message = mesh_pb2.Data()
    encoded_message.portnum = portnums_pb2.NODEINFO_APP
    encoded_message.payload = nodeinfo_payload
    encoded_message.want_response = want_response
    encoded_message.bitfield = 1

    payload = generate_mesh_packet(encoded_message)
    return payload


########## POSITION ##########
def send_position(client, lat, lon, alt):
    """Send position details."""
    message_content = {
        "lat": lat,
        "lon": lon,
        "alt": alt
    }
    publish_message(create_position_payload, client, **message_content)

def create_position_payload(lat, lon, alt):
    """Create a position payload."""
    pos_time = int(time.time())
    latitude_str = str(lat)
    longitude_str = str(lon)

    try:
        latitude = float(latitude_str)
    except ValueError:
        latitude = 0.0
    try:
        longitude = float(longitude_str)
    except ValueError:
        longitude = 0.0

    latitude = latitude * 1e7
    longitude = longitude * 1e7

    latitude_i = int(latitude)
    longitude_i = int(longitude)

    altitude_str = str(alt)
    altitude_units = 1 / 3.28084 if 'ft' in altitude_str else 1.0
    altitude_number_of_units = float(re.sub('[^0-9.]','', altitude_str))
    altitude_i = int(altitude_units * altitude_number_of_units) # meters

    position_payload = mesh_pb2.Position()
    setattr(position_payload, "latitude_i", latitude_i)
    setattr(position_payload, "longitude_i", longitude_i)
    setattr(position_payload, "altitude", altitude_i)
    setattr(position_payload, "time", pos_time)
    setattr(position_payload, "location_source", "LOC_MANUAL")
    setattr(position_payload, "precision_bits", 32)

    position_payload = position_payload.SerializeToString()

    encoded_message = mesh_pb2.Data()
    encoded_message.portnum = portnums_pb2.POSITION_APP
    encoded_message.payload = position_payload
    encoded_message.want_response = False
    encoded_message.bitfield = 1

    payload = generate_mesh_packet(encoded_message)
    return payload

########## DEVICE TELEMETRY ##########
def send_device_telemetry(client, battery_level, voltage, chutil, airtxutil, uptime):
    """Send telemetry data."""
    message_content = {
        "battery_level": battery_level,
        "voltage": voltage,
        "chutil": chutil,
        "airtxutil": airtxutil,
        "uptime": uptime
    }
    publish_message(create_telemetry_device_payload, client, **message_content)

def create_telemetry_device_payload(battery_level, voltage, chutil, airtxutil, uptime):
    """Create a telemetry payload."""
    telemetry_payload = telemetry_pb2.Telemetry()
    setattr(telemetry_payload.device_metrics, "battery_level", battery_level)
    setattr(telemetry_payload.device_metrics, "voltage", voltage)
    setattr(telemetry_payload.device_metrics, "channel_utilization", chutil)
    setattr(telemetry_payload.device_metrics, "air_util_tx", airtxutil)
    setattr(telemetry_payload.device_metrics, "uptime_seconds", uptime)

    telemetry_payload = telemetry_payload.device_metrics.SerializeToString()

    encoded_message = mesh_pb2.Data()
    encoded_message.portnum = portnums_pb2.TELEMETRY_APP
    encoded_message.payload = telemetry_payload
    encoded_message.bitfield = 1

    payload = generate_mesh_packet(encoded_message)
    return payload

########## ACK ########## # UNUSED
def create_ack_payload():
    encoded_message = mesh_pb2.Data()
    encoded_message.portnum = portnums_pb2.ROUTING_APP
    encoded_message.request_id = message_id
    encoded_message.payload = b"\030\000"
    payload = generate_mesh_packet(encoded_message)
    return payload

####################
def publish_message(payload_function, client, **kwargs):
    """Publishes a message to the MQTT broker."""
    try:
        payload = payload_function(**kwargs)
        topic = f"{root_topic}{channel}/{node_id}"
        client.publish(topic, payload)
    except Exception as e:
        print(f"Error while sending message: {e}")

def generate_mesh_packet(encoded_message):
    """Generate the final mesh packet."""
    global message_id
    message_id += 1

    node_number = int(node_id.replace("!", ""), 16)
    mesh_packet = mesh_pb2.MeshPacket()
    mesh_packet.id = message_id

    setattr(mesh_packet, "from", node_number)
    mesh_packet.to = destination_id
    # mesh_packet.rx_time = time.time()
    # mesh_packet.rx_snr = 0.0
    mesh_packet.want_ack = False
    mesh_packet.channel = generate_hash(channel, key)
    # mesh_packet.priority = "BACKGROUND"
    mesh_packet.hop_limit = 3
    # mesh_packet.rx_rssi = 0
    mesh_packet.hop_start = 3

    if key == "":
        mesh_packet.decoded.CopyFrom(encoded_message)
    else:
        mesh_packet.encrypted = encrypt_packet(channel, key, mesh_packet, encoded_message)

    service_envelope = mqtt_pb2.ServiceEnvelope()
    service_envelope.packet.CopyFrom(mesh_packet)
    service_envelope.channel_id = channel
    service_envelope.gateway_id = node_id

    payload = service_envelope.SerializeToString()
    return payload