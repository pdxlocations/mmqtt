import random
import re
import time
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


def publish_message(payload_function: Callable, portnum: int, **kwargs) -> None:
    """Send a message of any type, with logging."""

    from mmqtt import client

    use_config = kwargs.get("use_config", False)

    try:
        if use_config:
            config = _get_config()
            topic = f"{config.mqtt.root_topic}/2/e/{config.channel.preset}/{config.nodeinfo.id}"
        else:
            topic = f"{client.root_topic}/2/e/{client.channel}/{client.node_id}"

        destination = kwargs.get("to")
        if destination is None:
            destination = _get_config().message.destination_id if use_config else client.destination_id
        payload = payload_function(portnum=portnum, **kwargs)

        print(f"\n[TX] Portnum = {get_portnum_name(portnum)} ({portnum})")
        print(f"     Topic: '{topic}'")
        print(f"     To: {kwargs.get('to', destination)}")
        for k, v in kwargs.items():
            if k not in ("use_config", "to") and v is not None:
                print(f"     {k}: {v}")

        client.publish(topic, payload)

    except Exception as e:
        print(f"Error while sending message: {e}")


def create_payload(data, portnum: int, bitfield: int = 1, **kwargs) -> bytes:
    """Generalized function to create a payload."""
    encoded_message = mesh_pb2.Data()
    encoded_message.portnum = portnum
    encoded_message.payload = data.SerializeToString() if hasattr(data, "SerializeToString") else data
    encoded_message.want_response = kwargs.get("want_response", False)
    encoded_message.bitfield = bitfield
    return generate_mesh_packet(encoded_message, **kwargs)


def generate_mesh_packet(encoded_message: mesh_pb2.Data, **kwargs) -> bytes:
    """Generate the final mesh packet."""

    use_config = kwargs.get("use_config", False)
    if use_config:
        config = _get_config()
        if not config.nodeinfo.id.startswith("!"):
            raise ValueError("Node ID must start with '!'")
        channel_id = config.channel.preset
        channel_key = config.channel.key
        gateway_id = config.nodeinfo.id
        from_id = int(config.nodeinfo.id.replace("!", ""), 16)
        destination = kwargs.get("to", config.message.destination_id)
    else:
        from mmqtt import client

        if not client.node_id.startswith("!"):
            raise ValueError("Node ID must start with '!'")
        channel_id = client.channel
        channel_key = client.key
        gateway_id = client.node_id
        from_id = int(client.node_id.replace("!", ""), 16)
        destination = kwargs.get("to", client.destination_id)

    reserved_ids = [1, 2, 3, 4, 4294967295]
    if from_id in reserved_ids:
        raise ValueError(f"Node ID '{from_id}' is reserved and cannot be used. Please choose a different ID.")

    global message_id
    message_id = get_message_id(message_id)

    mesh_packet = mesh_pb2.MeshPacket()
    mesh_packet.id = message_id
    setattr(mesh_packet, "from", from_id)
    mesh_packet.to = int(destination)
    mesh_packet.want_ack = kwargs.get("want_ack", False)
    mesh_packet.channel = generate_hash(channel_id, channel_key)
    mesh_packet.hop_limit = kwargs.get("hop_limit", 3)
    mesh_packet.hop_start = kwargs.get("hop_start", 3)

    if channel_key == "":
        mesh_packet.decoded.CopyFrom(encoded_message)
    else:
        mesh_packet.encrypted = encrypt_packet(channel_id, channel_key, mesh_packet, encoded_message)

    service_envelope = mqtt_pb2.ServiceEnvelope()
    service_envelope.packet.CopyFrom(mesh_packet)
    service_envelope.channel_id = channel_id
    service_envelope.gateway_id = gateway_id

    return service_envelope.SerializeToString()


########## Specific Message Handlers ##########


def send_text_message(message: str = None, **kwargs) -> None:
    """Send a text message to the specified destination."""

    def create_text_payload(portnum: int, message: str = None, **kwargs):
        data = message.encode("utf-8")
        return create_payload(data, portnum, **kwargs)

    publish_message(create_text_payload, portnums_pb2.TEXT_MESSAGE_APP, message=message, **kwargs)


def send_nodeinfo(id: int = None, long_name: str = None, short_name: str = None, **kwargs) -> None:
    """Send node information including short/long names and hardware model."""

    if "hw_model" not in kwargs:
        kwargs["hw_model"] = 255

    def create_nodeinfo_payload(portnum: int, **_):

        nodeinfo_fields = {
            "id": id if id is not None else None,
            "long_name": long_name if long_name is not None else None,
            "short_name": short_name if short_name is not None else None,
        }
        # Filter out None values and remove keys we've already handled
        reserved_keys = {"node_id", "long_name", "short_name"}
        data = {k: v for k, v in kwargs.items() if v is not None and k not in reserved_keys}
        nodeinfo_fields.update(data)

        return create_payload(mesh_pb2.User(**nodeinfo_fields), portnum)

    publish_message(
        create_nodeinfo_payload, portnums_pb2.NODEINFO_APP, id=id, long_name=long_name, short_name=short_name, **kwargs
    )


def send_position(latitude: float = None, longitude: float = None, **kwargs) -> None:
    """Send current position with optional additional fields (e.g., ground_speed, fix_type, etc)."""

    def create_position_payload(portnum: int, **fields):
        position_fields = {
            "latitude_i": int(latitude * 1e7) if latitude is not None else None,
            "longitude_i": int(longitude * 1e7) if longitude is not None else None,
            "location_source": "LOC_MANUAL",
            "time": int(time.time()),
        }

        # Filter out None values and remove keys we've already handled
        reserved_keys = {"latitude", "longitude"}
        data = {k: v for k, v in fields.items() if v is not None and k not in reserved_keys}
        position_fields.update(data)

        return create_payload(mesh_pb2.Position(**position_fields), portnum)

    publish_message(
        create_position_payload, portnums_pb2.POSITION_APP, latitude=latitude, longitude=longitude, **kwargs
    )


def send_device_telemetry(**kwargs) -> None:
    """Send telemetry packet including battery, voltage, channel usage, and uptime."""

    def create_telemetry_payload(portnum: int, **_):
        metrics_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        metrics = telemetry_pb2.DeviceMetrics(**metrics_kwargs)
        data = telemetry_pb2.Telemetry(time=int(time.time()), device_metrics=metrics)
        return create_payload(data, portnum)

    publish_message(create_telemetry_payload, portnums_pb2.TELEMETRY_APP, **kwargs)


def send_power_metrics(**kwargs) -> None:
    """Send power metrics including voltage and current for three channels."""

    def create_power_metrics_payload(portnum: int, **_):
        metrics_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        metrics = telemetry_pb2.PowerMetrics(**metrics_kwargs)
        data = telemetry_pb2.Telemetry(time=int(time.time()), power_metrics=metrics)
        return create_payload(data, portnum)

    publish_message(create_power_metrics_payload, portnums_pb2.TELEMETRY_APP, **kwargs)


def send_environment_metrics(**kwargs) -> None:
    """Send environment metrics including temperature, humidity, pressure, and gas resistance."""

    def create_environment_metrics_payload(portnum: int, **_):
        # Filter out None values from kwargs
        metrics_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        metrics = telemetry_pb2.EnvironmentMetrics(**metrics_kwargs)
        data = telemetry_pb2.Telemetry(time=int(time.time()), environment_metrics=metrics)
        return create_payload(data, portnum)

    publish_message(create_environment_metrics_payload, portnums_pb2.TELEMETRY_APP, **kwargs)


def send_health_metrics(**kwargs) -> None:
    """Send health metrics including heart rate, SpO2, and body temperature."""

    def create_health_metrics_payload(portnum: int, **_):
        metrics_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        metrics = telemetry_pb2.HealthMetrics(**metrics_kwargs)
        data = telemetry_pb2.Telemetry(time=int(time.time()), health_metrics=metrics)
        return create_payload(data, portnum)

    publish_message(create_health_metrics_payload, portnums_pb2.TELEMETRY_APP, **kwargs)
