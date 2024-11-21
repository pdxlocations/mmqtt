from meshtastic import mqtt_pb2, portnums_pb2, mesh_pb2, telemetry_pb2
from encryption import decrypt_packet

from load_config import (
    mqtt_broker, mqtt_port, mqtt_username, mqtt_password,
    root_topic, channel, key, node_id, node_short_name,
    node_long_name, lat, lon, alt, node_hw_model, node_number
)


#################################
# Receive Messages

def on_message(client, userdata, msg):
    se = mqtt_pb2.ServiceEnvelope()
    try:
        se.ParseFromString(msg.payload)

        print ("")
        print ("Service Envelope:")
        print (se)

        mp = se.packet
    except Exception as e:
        print(f"*** ServiceEnvelope: {str(e)}")
        return
    
    if mp.HasField("encrypted") and not mp.HasField("decoded"):
        
        decrypt_packet(mp, key)

    print ("")
    print ("Message Packet:")
    print(mp)

    if mp.decoded.portnum == portnums_pb2.TEXT_MESSAGE_APP:
        try:
            from_str = getattr(mp, "from")
            from_id = '!' + hex(from_str)[2:]
            text_payload = mp.decoded.payload.decode("utf-8")
            print(f"{from_id}: {text_payload}")
        except Exception as e:
            print(f"*** TEXT_MESSAGE_APP: {str(e)}")
        
    elif mp.decoded.portnum == portnums_pb2.NODEINFO_APP:
        info = mesh_pb2.User()
        try:
            info.ParseFromString(mp.decoded.payload)

            print("")
            print("NodeInfo:")
            print(info)

        except Exception as e:
            print(f"*** NODEINFO_APP: {str(e)}")
        
    elif mp.decoded.portnum == portnums_pb2.POSITION_APP:
        pos = mesh_pb2.Position()
        try:
            pos.ParseFromString(mp.decoded.payload)

            print("")
            print("Position:")
            print(pos)

        except Exception as e:
            print(f"*** POSITION_APP: {str(e)}")

    elif mp.decoded.portnum == portnums_pb2.TELEMETRY_APP:
        env = telemetry_pb2.Telemetry()
        try:
            env.ParseFromString(mp.decoded.payload)

            print("")
            print("Telemetry:")
            print(env)

        except Exception as e:
            print(f"*** TELEMETRY_APP: {str(e)}")

        rssi = getattr(mp, "rx_rssi")

        # Device Metrics
        device_metrics_dict = {
            'Battery Level': env.device_metrics.battery_level,
            'Voltage': round(env.device_metrics.voltage, 2),
            'Channel Utilization': round(env.device_metrics.channel_utilization, 1),
            'Air Utilization': round(env.device_metrics.air_util_tx, 1)
        }

        # Environment Metrics
        environment_metrics_dict = {
            'Temp': round(env.environment_metrics.temperature, 2),
            'Humidity': round(env.environment_metrics.relative_humidity, 0),
            'Pressure': round(env.environment_metrics.barometric_pressure, 2),
            'Gas Resistance': round(env.environment_metrics.gas_resistance, 2)
        }
