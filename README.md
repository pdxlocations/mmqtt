This project is useful for testing Meshtastic networks connected to an MQTT server. Functions can be called in mqttc.py or by using arguments in the command line.

## Available functions:

```
send_nodeinfo(short_name, long_name, hw_model)
send_position(lat, lon, alt, precision)
send_device_telemetry(battery_level, voltage, chutil, airtxutil, uptime)
send_text_message("text")
```

## Available arguments:

```
  -h, --help             show this help message and exit
  --config CONFIG        Path to the config file
  --message MESSAGE      The message to send
  --lat LAT              Latitude coordinate
  --lon LON              Longitude coordinate
  --alt ALT              Altitude
  --precision PRECISION  Position Precision
```

## Examples:

To publish a message to the broker using settings defined in config.json:
```
python3 mqttc.py --message "I need an Alpinist"
```

To publish a message to the broker using settings defined in my-config.json:
```
python3 mqttc.py --congig "my-config.json" --message "I need an Alpinist"
```


## Installation:
```
git clone https://github.com/pdxlocations/MQTTc-for-Meshtastic.git
cd MQTTc-for-Meshtastic
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Rename config-example.json and edit configuration:
```
sudo mv config-example.json config.json
sudo nano config.json
```