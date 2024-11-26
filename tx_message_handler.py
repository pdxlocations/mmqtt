import time
import re
import random

from meshtastic import portnums_pb2, mesh_pb2, mqtt_pb2, telemetry_pb2

from utils import generate_hash, get_message_id
from encryption import encrypt_packet
from load_config import config

message_id = random.getrandbits(32)

########## TEXT MESSAGE ##########
def send_text_message(client, message):
    """Send a text message."""
    message_content = {
        "message_text": message
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
def send_nodeinfo(client, long, short, hw):
    """Send node information."""
    message_content = {
        "node_long_name": long,
        "node_short_name": short,
        "node_hw_model": hw,
        "want_response": False
    }
    publish_message(create_nodeinfo_data, client, **message_content)

def create_nodeinfo_data(node_long_name, node_short_name, node_hw_model, want_response):
    """Create a node information payload."""
    nodeinfo_data = mesh_pb2.User()
    nodeinfo_data.id = config.node.id
    nodeinfo_data.long_name = node_long_name
    nodeinfo_data.short_name = node_short_name
    nodeinfo_data.hw_model = node_hw_model

    nodeinfo_data = nodeinfo_data.SerializeToString()

    encoded_message = mesh_pb2.Data()
    encoded_message.portnum = portnums_pb2.NODEINFO_APP
    encoded_message.payload = nodeinfo_data
    encoded_message.want_response = want_response
    encoded_message.bitfield = 1

    payload = generate_mesh_packet(encoded_message)
    return payload


########## POSITION ##########
def send_position(client, lat, lon, alt, pre):
    """Send position details."""
    message_content = {
        "lat": lat,
        "lon": lon,
        "alt": alt,
        "pre": pre
    }
    publish_message(create_position_data, client, **message_content)

def create_position_data(lat, lon, alt, pre):
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

    position_data = mesh_pb2.Position()

    position_data.latitude_i = latitude_i
    position_data.longitude_i = longitude_i
    position_data.altitude = altitude_i
    position_data.time = pos_time
    position_data.location_source = "LOC_MANUAL"
    position_data.precision_bits = pre

    position_data = position_data.SerializeToString()

    encoded_message = mesh_pb2.Data()
    encoded_message.portnum = portnums_pb2.POSITION_APP
    encoded_message.payload = position_data
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
    publish_message(create_telemetry_device_data, client, **message_content)

def create_telemetry_device_data(battery_level, voltage, chutil, airtxutil, uptime):
    """Create a telemetry payload."""
    telemetry_data = telemetry_pb2.Telemetry()

    telemetry_data.time = (int(time.time()))
    telemetry_data.device_metrics.battery_level = battery_level
    telemetry_data.device_metrics.voltage = voltage
    telemetry_data.device_metrics.channel_utilization = chutil
    telemetry_data.device_metrics.air_util_tx = airtxutil
    telemetry_data.device_metrics.uptime_seconds = uptime

    telemetry_data = telemetry_data.SerializeToString()

    encoded_message = mesh_pb2.Data()
    encoded_message.portnum = portnums_pb2.TELEMETRY_APP
    encoded_message.payload = telemetry_data
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
        topic = f"{config.mqtt.root_topic}{config.channel.preset}/{config.node.id}"
        client.publish(topic, payload)
    except Exception as e:
        print(f"Error while sending message: {e}")

def generate_mesh_packet(encoded_message):
    """Generate the final mesh packet."""
    global message_id
    message_id = get_message_id(message_id)

    node_number = int(config.node.id.replace("!", ""), 16)
    mesh_packet = mesh_pb2.MeshPacket()
    mesh_packet.id = message_id

    setattr(mesh_packet, "from", node_number)
    mesh_packet.to = config.destination_id
    # mesh_packet.rx_time = time.time()
    # mesh_packet.rx_snr = 0.0
    mesh_packet.want_ack = False
    mesh_packet.channel = generate_hash(config.channel.preset, config.channel.key)
    # mesh_packet.priority = "BACKGROUND"
    mesh_packet.hop_limit = 3
    # mesh_packet.rx_rssi = 0
    mesh_packet.hop_start = 3

    if config.channel.key == "":
        mesh_packet.decoded.CopyFrom(encoded_message)
    else:
        mesh_packet.encrypted = encrypt_packet(config.channel.preset, config.channel.key, mesh_packet, encoded_message)

    service_envelope = mqtt_pb2.ServiceEnvelope()
    service_envelope.packet.CopyFrom(mesh_packet)
    service_envelope.channel_id = config.channel.preset
    service_envelope.gateway_id = config.node.id

    payload = service_envelope.SerializeToString()
    return payload