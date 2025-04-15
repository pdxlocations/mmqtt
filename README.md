This project is useful for testing Meshtastic networks connected to an MQTT server. Functions can be called via the `mmqtt` command or imported and used programmatically.

# Installation

```bash
pip install mmqtt
```

## For development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install poetry
poetry build
pip install dist/mmqtt*.whl
```

# To run:

```bash
mmqtt
```

## Available functions (see examples for further information):

```bash
from mmqtt import send_nodeinfo, send_position, send_device_telemetry, send_text_message
send_nodeinfo(node_id, long_name, short_name)
send_position(lattitude, longitude, altitude, location_precision)
send_device_telemetry(battery_level, voltage, chutil, airtxutil, uptime)
send_text_message("text")
```
Optional Arguments:
```bash
to=INT
hop_start=INT
hop_limit=INT
want_ack=BOOL
want_response=BOOL
```
Example:
```bash
send_text_message("Happy New Year" to=12345678, hop_limit=5)
```


## Available arguments:

```
  -h, --help             show this help message and exit
  --config CONFIG        Path to the config file
  --message MESSAGE      Message to send. You can use this multiple times.
  --message-file FILE    Path to a file containing messages, one per line
  --nodeinfo             Send NodeInfo from my config
  --telemetry            Send telemetry from my config
  --lat LAT              Latitude coordinate
  --lon LON              Longitude coordinate
  --alt ALT              Altitude
  --precision PRECISION  Position Precision
  --position             Send position from config unless overridden by --lat, --lon, or --alt
  --listen               Stay connected and listen for incoming MQTT messages
```

## Examples:

To publish a message to the broker using settings defined in `config-example.json`:
```
mmqtt --message "I need an Alpinist"
```

To publish a message to the broker using settings defined in `my-config.json`:
```
mmqtt --config "my-config.json" --message "I need an Alpinist"
```

## Example config.json:

```yaml
{
  "mqtt": {
    "broker": "mqtt.meshtastic.org",
    "port": 1883,
    "user": "meshdev",
    "password": "large4cats",
    "root_topic": "msh/US/2/e/"
  },
  "channel": {
    "preset": "LongFast",
    "key": "AQ=="
  },
  "nodeinfo": {
    "id": "!deadbeef",
    "short_name": "q",
    "long_name": "mmqtt",
    "hw_model": 255
  },
  "position": {
    "lat": 45.43139,
    "lon": -122.37354,
    "alt": 9,
    "location_source": "LOC_MANUAL",
    "precision": 16
  },
  "telemetry": {
    "battery_level": 99,
    "voltage": 4.0,
    "chutil": 3,
    "airtxutil": 1,
    "uptime": 420
  },
  "message": {
    "text": "Happy New Year",
    "destination_id": "4294967295"
  },
  "mode": {
    "listen": "False"
  }
}
  ```