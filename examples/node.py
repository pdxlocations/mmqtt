from mmqtt import send_nodeinfo, send_position, send_device_telemetry, send_text_message

# NodeInfo: long_name, short_name, hw_model
send_nodeinfo("My Long Name", "Shorty", "T_ECHO")

# Position: lat, lon, altitude, precision
send_position(37.7749, -122.4194, 10, 3)

# Telemetry: battery_level, voltage, chutil, airtxutil, uptime
send_device_telemetry(
    battery_level=50,
    voltage=3.7,
    chutil=25,
    airtxutil=15,
    uptime=123456
)

# Simple text message
send_text_message("Hello, Meshtastic!")