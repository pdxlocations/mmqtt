from typing import Any
from paho.mqtt.client import Client as MQTTClient, MQTTMessage

from meshtastic import mqtt_pb2, portnums_pb2, mesh_pb2, telemetry_pb2, protocols
from mmqtt.encryption import decrypt_packet
from mmqtt.load_config import ConfigLoader


def on_message(client: MQTTClient, userdata: Any, msg: MQTTMessage) -> None:
    """Handle incoming MQTT messages."""

    config = ConfigLoader.get_config()
    se = mqtt_pb2.ServiceEnvelope()
    print()
    try:
        se.ParseFromString(msg.payload)

        print("[RX] Service Envelope:")
        for line in str(se).splitlines():
            print("     " + line)

        mp = se.packet
    except Exception as e:
        print(f"*** [RX] ServiceEnvelope: {str(e)}")
        return

    if mp.HasField("encrypted") and not mp.HasField("decoded"):
        decoded_data = decrypt_packet(mp, config.channel.key)
        if decoded_data is not None:
            mp.decoded.CopyFrom(decoded_data)
        else:
            print("*** [RX] Failed to decrypt message — decoded_data is None")
            return
    print()
    print("[RX] Message Packet:")
    for line in str(mp).splitlines():
        print("     " + line)

    if mp.decoded.portnum == portnums_pb2.TEXT_MESSAGE_APP:
        print()
        try:
            from_str = getattr(mp, "from")
            from_id = "!" + hex(from_str)[2:]
            text_payload = mp.decoded.payload.decode("utf-8")

            print("[RX] Message Payload:")
            for line in str(mp.decoded).splitlines():
                print("     " + line)
            # print(f"{from_id}: {text_payload}")

        except Exception as e:
            print(f"*** [RX] TEXT_MESSAGE_APP: {str(e)}")

    elif mp.decoded.portnum == portnums_pb2.NODEINFO_APP:
        info = mesh_pb2.User()
        print()
        try:
            info.ParseFromString(mp.decoded.payload)

            print("[RX] NodeInfo:")
            for line in str(info).splitlines():
                print("     " + line)

        except Exception as e:
            print(f"*** [RX] NODEINFO_APP: {str(e)}")

    elif mp.decoded.portnum == portnums_pb2.POSITION_APP:
        pos = mesh_pb2.Position()
        print()
        try:
            pos.ParseFromString(mp.decoded.payload)

            print("[RX] Position:")
            for line in str(pos).splitlines():
                print("     " + line)

        except Exception as e:
            print(f"*** [RX] POSITION_APP: {str(e)}")

    elif mp.decoded.portnum == portnums_pb2.TELEMETRY_APP:
        telem = telemetry_pb2.Telemetry()
        print()
        try:
            # Parse the payload into the main telemetry message
            telem.ParseFromString(mp.decoded.payload)

            # Check and parse device_metrics if available
            if telem.HasField("device_metrics"):
                device_metrics = telem.device_metrics
                print("[RX] Device Metrics:")
                for line in str(device_metrics).splitlines():
                    print("     " + line)

            # Check and parse environment_metrics if available
            if telem.HasField("environment_metrics"):
                environment_metrics = telem.environment_metrics
                print("[RX] Environment Metrics:")
                for line in str(environment_metrics).splitlines():
                    print("     " + line)

            # Check and parse power_metrics if available
            if telem.HasField("power_metrics"):
                power_metrics = telem.power_metrics
                print("[RX] Power Metrics:")
                for line in str(power_metrics).splitlines():
                    print("     " + line)

        except Exception as e:
            print(f"*** [RX] TELEMETRY_APP: {str(e)}")

    else:
        # Attempt to process the decrypted or encrypted payload
        portNumInt = mp.decoded.portnum if mp.HasField("decoded") else None
        handler = protocols.get(portNumInt) if portNumInt else None

        pb = None
        if handler is not None and handler.protobufFactory is not None:
            pb = handler.protobufFactory()
            pb.ParseFromString(mp.decoded.payload)

        if pb:
            # Clean and update the payload
            pb_str = str(pb).replace("", " ").replace("\r", " ").strip()
            mp.decoded.payload = pb_str.encode("utf-8")
        print("[RX] Raw Message:")
        for line in str(mp).splitlines():
            print("     " + line)
