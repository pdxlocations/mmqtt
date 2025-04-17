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


def send_nodeinfo(id: str = None, long_name: str = None, short_name: str = None, **kwargs) -> None:
    """Send node information including short/long names and hardware model."""

    if long_name is not None and len(long_name) > 32:
        raise ValueError("Long name exceeds 32 characters.")
    if short_name is not None and len(short_name) > 4:
        raise ValueError("Short name exceeds 4 characters.")

    def create_nodeinfo_payload(
        portnum: int,
        node_long_name: str = None,
        node_short_name: str = None,
        node_id: str = None,
        **kwargs,
    ):
        data = mesh_pb2.User(
            id=node_id,
            long_name=node_long_name,
            short_name=node_short_name,
            hw_model=255,
        )
        return create_payload(data, portnum, **kwargs)

    publish_message(
        create_nodeinfo_payload,
        portnums_pb2.NODEINFO_APP,
        node_long_name=long_name,
        node_short_name=short_name,
        node_id=id,
        **kwargs,
    )


def send_position(
    latitude: float = None,
    longitude: float = None,
    altitude: int = None,
    precision: int = None,
    HDOP: int = None,
    PDOP: int = None,
    VDOP: int = None,
    altitude_geoidal_separation: int = None,
    altitude_hae: int = None,
    altitude_source: int = None,
    fix_quality: int = None,
    fix_type: int = None,
    gps_accuracy: int = None,
    ground_speed: int = None,
    ground_track: int = None,
    next_update: int = None,
    sats_in_view: int = None,
    sensor_id: int = None,
    seq_number: int = None,
    timestamp: int = None,
    timestamp_millis_adjust: int = None,
    **kwargs,
) -> None:
    """Send current position with optional precision."""

    def create_position_payload(portnum: int, **kwargs):

        pos_time = int(time.time())
        altitude_units = 1 / 3.28084 if "ft" in str(altitude).lower() else 1.0
        alt_value = int(altitude_units * float(re.sub(r"[^0-9.]", "", str(altitude))))

        position_kwargs = {
            "latitude_i": int(latitude * 1e7) if latitude is not None else None,
            "longitude_i": int(longitude * 1e7) if longitude is not None else None,
            "altitude": alt_value,
            "time": pos_time,
            "location_source": "LOC_MANUAL",
            "precision_bits": precision,
            "HDOP": HDOP,
            "PDOP": PDOP,
            "VDOP": VDOP,
            "altitude_geoidal_separation": altitude_geoidal_separation,
            "altitude_hae": altitude_hae,
            "altitude_source": altitude_source,
            "fix_quality": fix_quality,
            "fix_type": fix_type,
            "gps_accuracy": gps_accuracy,
            "ground_speed": ground_speed,
            "ground_track": ground_track,
            "next_update": next_update,
            "sats_in_view": sats_in_view,
            "sensor_id": sensor_id,
            "seq_number": seq_number,
            "timestamp": timestamp,
            "timestamp_millis_adjust": timestamp_millis_adjust,
        }

        data = mesh_pb2.Position(**{k: v for k, v in position_kwargs.items() if v is not None})
        return create_payload(data, portnum)

    publish_message(
        create_position_payload,
        portnums_pb2.POSITION_APP,
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        precision=precision,
        HDOP=HDOP,
        PDOP=PDOP,
        VDOP=VDOP,
        altitude_geoidal_separation=altitude_geoidal_separation,
        altitude_hae=altitude_hae,
        altitude_source=altitude_source,
        fix_quality=fix_quality,
        fix_type=fix_type,
        gps_accuracy=gps_accuracy,
        ground_speed=ground_speed,
        ground_track=ground_track,
        next_update=next_update,
        sats_in_view=sats_in_view,
        sensor_id=sensor_id,
        seq_number=seq_number,
        timestamp=timestamp,
        timestamp_millis_adjust=timestamp_millis_adjust,
        **kwargs,
    )


def send_device_telemetry(
    battery_level: int = None,
    voltage: float = None,
    chutil: int = None,
    airtxutil: int = None,
    uptime: int = None,
    **kwargs,
) -> None:
    """Send telemetry packet including battery, voltage, channel usage, and uptime."""

    def create_telemetry_payload(
        portnum: int,
        battery_level: int = None,
        voltage: float = None,
        chutil: int = None,
        airtxutil: int = None,
        uptime: int = None,
        **kwargs,
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
        **kwargs,
    )


def send_power_metrics(
    ch1_voltage: float = None,
    ch1_current: float = None,
    ch2_voltage: float = None,
    ch2_current: float = None,
    ch3_voltage: float = None,
    ch3_current: float = None,
    **kwargs,
) -> None:
    """Send power metrics including voltage and current for three channels."""

    def create_power_metrics_payload(
        portnum: int,
        ch1_voltage: float = None,
        ch1_current: float = None,
        ch2_voltage: float = None,
        ch2_current: float = None,
        ch3_voltage: float = None,
        ch3_current: float = None,
        **kwargs,
    ):
        data = telemetry_pb2.Telemetry(
            time=int(time.time()),
            power_metrics=telemetry_pb2.PowerMetrics(
                ch1_voltage=ch1_voltage,
                ch1_current=ch1_current,
                ch2_voltage=ch2_voltage,
                ch2_current=ch2_current,
                ch3_voltage=ch3_voltage,
                ch3_current=ch3_current,
            ),
        )
        return create_payload(data, portnum, **kwargs)

    publish_message(
        create_power_metrics_payload,
        portnums_pb2.TELEMETRY_APP,
        ch1_voltage=ch1_voltage,
        ch1_current=ch1_current,
        ch2_voltage=ch2_voltage,
        ch2_current=ch2_current,
        ch3_voltage=ch3_voltage,
        ch3_current=ch3_current,
        **kwargs,
    )


def send_environment_metrics(
    temperature: float = None,
    relative_humidity: float = None,
    barometric_pressure: float = None,
    gas_resistance: float = None,
    voltage: float = None,
    current: float = None,
    iaq: int = None,
    distance: float = None,
    ir_lux: float = None,
    lux: float = None,
    radiation: float = None,
    rainfall_1h: float = None,
    rainfall_24h: float = None,
    soil_moisture: float = None,
    soil_temperature: float = None,
    uv_lux: float = None,
    weight: float = None,
    white_lux: float = None,
    wind_direction: int = None,
    wind_gust: float = None,
    wind_lull: float = None,
    wind_speed: float = None,
    **kwargs,
) -> None:

    def create_environment_metrics_payload(portnum: int, **kwargs):
        metrics_kwargs = {
            "temperature": temperature,
            "relative_humidity": relative_humidity,
            "barometric_pressure": barometric_pressure,
            "gas_resistance": gas_resistance,
            "voltage": voltage,
            "current": current,
            "iaq": iaq,
            "distance": distance,
            "ir_lux": ir_lux,
            "lux": lux,
            "radiation": radiation,
            "rainfall_1h": rainfall_1h,
            "rainfall_24h": rainfall_24h,
            "soil_moisture": soil_moisture,
            "soil_temperature": soil_temperature,
            "uv_lux": uv_lux,
            "weight": weight,
            "white_lux": white_lux,
            "wind_direction": wind_direction,
            "wind_gust": wind_gust,
            "wind_lull": wind_lull,
            "wind_speed": wind_speed,
        }
        metrics = telemetry_pb2.EnvironmentMetrics(**{k: v for k, v in metrics_kwargs.items() if v is not None})
        data = telemetry_pb2.Telemetry(time=int(time.time()), environment_metrics=metrics)
        return create_payload(data, portnum)

    publish_message(
        create_environment_metrics_payload,
        portnums_pb2.TELEMETRY_APP,
        temperature=temperature,
        relative_humidity=relative_humidity,
        barometric_pressure=barometric_pressure,
        gas_resistance=gas_resistance,
        voltage=voltage,
        current=current,
        iaq=iaq,
        distance=distance,
        ir_lux=ir_lux,
        lux=lux,
        radiation=radiation,
        rainfall_1h=rainfall_1h,
        rainfall_24h=rainfall_24h,
        soil_moisture=soil_moisture,
        soil_temperature=soil_temperature,
        uv_lux=uv_lux,
        weight=weight,
        white_lux=white_lux,
        wind_direction=wind_direction,
        wind_gust=wind_gust,
        wind_lull=wind_lull,
        wind_speed=wind_speed,
        **kwargs,
    )
