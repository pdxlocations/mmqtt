import random
import re
import time
import os
from typing import Callable

from meshtastic import portnums_pb2, mesh_pb2, mqtt_pb2, telemetry_pb2

from mmqtt.encryption import encrypt_packet
from mmqtt.load_config import ConfigLoader
from mmqtt.utils import generate_hash, get_message_id

_config = None
message_id = random.getrandbits(32)

def _get_config():
    global _config
    if _config is None:
        _config = ConfigLoader.get_config()
    return _config

def get_portnum_name(portnum: int) -> str:
    for name, number in portnums_pb2.PortNum.items():
        if number == portnum:
            return name
    return f"UNKNOWN_PORTNUM ({portnum})"

def get_destination_id(use_args: bool):
    if use_args:
        return _get_config().message.destination_id
    else:
        from mmqtt import client
        return client.destination_id

def publish_message(payload_function: Callable, portnum: int, **kwargs) -> None:
    """Send a message of any type, with logging."""

    from mmqtt import client
    use_args = kwargs.get("use_args", False)

    try:
        if use_args:
            config = _get_config()
            topic = f"{config.mqtt.root_topic}/2/e/{config.channel.preset}/{config.nodeinfo.id}"
        else:
            topic = f"{client.root_topic}/2/e/{client.channel}/{client.node_id}"

        destination = get_destination_id(use_args)
        payload = payload_function(portnum=portnum, **kwargs)

        print(f"\n[TX] Portnum = {get_portnum_name(portnum)} ({portnum})")
        print(f"     Topic: '{topic}'")
        print(f"     To: {kwargs.get('to', destination)}")
        for k, v in kwargs.items():
            if k != "use_args" and k != "to":
                print(f"     {k}: {v}")

        client.publish(topic, payload)

    except Exception as e:
        print(f"Error while sending message: {e}")

def create_payload(data, portnum: int, want_response: bool = False, bitfield: int = 1, **kwargs) -> bytes:
    """Generalized function to create a payload."""
    encoded_message = mesh_pb2.Data()
    encoded_message.portnum = portnum
    encoded_message.payload = data.SerializeToString() if hasattr(data, "SerializeToString") else data
    encoded_message.want_response = want_response
    encoded_message.bitfield = bitfield
    return generate_mesh_packet(encoded_message, use_args=kwargs.get("use_args", False))

def generate_mesh_packet(encoded_message: mesh_pb2.Data, use_args: bool = False, **kwargs) -> bytes:
    """Generate the final mesh packet."""

    if use_args:
        config = _get_config()
        channel_id = config.channel.preset
        channel_key = config.channel.key
        gateway_id = config.nodeinfo.id
        from_id = config.nodeinfo.number
        destination = kwargs.get("to", config.message.destination_id)
    else:
        from mmqtt import client
        channel_id = client.channel
        channel_key = client.key
        gateway_id = client.node_id
        from_id = int(client.node_id.replace("!", ""), 16)
        destination = kwargs.get("to", client.destination_id)

    global message_id
    message_id = get_message_id(message_id)

    destination = kwargs.get("to", destination)

    mesh_packet = mesh_pb2.MeshPacket()
    mesh_packet.id = message_id
    setattr(mesh_packet, "from", from_id)
    mesh_packet.to = int(destination)
    mesh_packet.want_ack = False
    mesh_packet.channel = generate_hash(channel_id, channel_key)
    mesh_packet.hop_limit = 3
    mesh_packet.hop_start = 3

    if channel_key == "":
        mesh_packet.decoded.CopyFrom(encoded_message)
    else:
        mesh_packet.encrypted = encrypt_packet(
            channel_id, channel_key, mesh_packet, encoded_message
        )

    service_envelope = mqtt_pb2.ServiceEnvelope()
    service_envelope.packet.CopyFrom(mesh_packet)
    service_envelope.channel_id = channel_id
    service_envelope.gateway_id = gateway_id

    return service_envelope.SerializeToString()

########## Specific Message Handlers ##########

def send_text_message(message: str, **kwargs) -> None:
    """Send a text message to the specified destination."""
    def create_text_payload(portnum: int, message: str, **kwargs):
        data = message.encode("utf-8")
        return create_payload(data, portnum, **kwargs)

    publish_message(create_text_payload, portnums_pb2.TEXT_MESSAGE_APP, message=message, **kwargs)

def send_nodeinfo(id: str, long_name: str, short_name: str, **kwargs) -> None:
    """Send node information including short/long names and hardware model."""
    def create_nodeinfo_payload(portnum: int, node_long_name: str, node_short_name: str, node_id: str, **kwargs):
        data = mesh_pb2.User(
            id=node_id,
            long_name=node_long_name,
            short_name=node_short_name,
            hw_model=255
        )
        return create_payload(data, portnum, **kwargs)

    publish_message(
        create_nodeinfo_payload,
        portnums_pb2.NODEINFO_APP,
        node_long_name=long_name,
        node_short_name=short_name,
        node_id=id,
        **kwargs
    )

def send_position(latitude: float, longitude: float, altitude: float | str, precision: int, **kwargs) -> None:
    """Send current position with optional precision."""
    def create_position_payload(portnum: int, latitude: float, longitude: float, altitude: float | str, precision: int):
        pos_time = int(time.time())
        latitude_i = int(latitude * 1e7)
        longitude_i = int(longitude * 1e7)
        altitude_units = 1 / 3.28084 if 'ft' in str(altitude).lower() else 1.0
        alt_value = int(altitude_units * float(re.sub(r'[^0-9.]', '', str(altitude))))

        data = mesh_pb2.Position(
            latitude_i=latitude_i,
            longitude_i=longitude_i,
            altitude=alt_value,
            time=pos_time,
            location_source="LOC_MANUAL",
            precision_bits=precision,
            **kwargs
        )
        return create_payload(data, portnum, **kwargs)

    publish_message(
        create_position_payload,
        portnums_pb2.POSITION_APP,
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        precision=precision,
    )

def send_device_telemetry(battery_level: int, voltage: float, chutil: int, airtxutil: int, uptime: int, **kwargs) -> None:
    """Send telemetry packet including battery, voltage, channel usage, and uptime."""
    def create_telemetry_payload(
        portnum: int,
        battery_level: int,
        voltage: float,
        chutil: int,
        airtxutil: int,
        uptime: int,
        **kwargs
    ):
        data = telemetry_pb2.Telemetry(
            time=int(time.time()),
            device_metrics=telemetry_pb2.DeviceMetrics(
                battery_level=battery_level,
                voltage=voltage,
                channel_utilization=chutil,
                air_util_tx=airtxutil,
                uptime_seconds=uptime,
            ),
        )
        return create_payload(data, portnum, **kwargs)

    publish_message(
        create_telemetry_payload,
        portnums_pb2.TELEMETRY_APP,
        battery_level=battery_level,
        voltage=voltage,
        chutil=chutil,
        airtxutil=airtxutil,
        uptime=uptime,
        **kwargs
    )
