This project is useful for testing Meshtastic networks connected to an MQTT server. Functions can be called in mqttc.py or by using arguments in the command line.


Available arguments:

```
  -h, --help             show this help message and exit
  --config CONFIG        Path to the config file
  --message MESSAGE      The message to send
  --lat LAT              Latitude coordinate
  --lon LON              Longitude coordinate
  --alt ALT              Altitude
  --precision PRECISION  Position Precision```

Example:

To publish a message to the broker using settings defined in config.json:
``` python3 mqttc.py --message "I need an Alpinist"```

