import time
import requests
from meshtastic import BROADCAST_NUM
from mmqtt import send_position, send_nodeinfo, client


def send_iss_nodeinfo():
    send_nodeinfo(client.node_id, "ISS", "🛰")


def get_iss_location():
    try:
        response = requests.get("https://api.wheretheiss.at/v1/satellites/25544")
        response.raise_for_status()
        data = response.json()
        return data["latitude"], data["longitude"], data["altitude"] * 1000
    except Exception as e:
        print(f"[ERROR] Failed to fetch ISS location: {e}")
        return None, None, None


def main():
    client.server = "mqtt.meshtastic.org"
    client.port = 1883
    client.user = "meshdev"
    client.password = "large4cats"
    client.root_topic = "msh/US"
    client.channel = "LongFast"
    client.key = "AQ=="
    client.node_id = "!1ceface1"
    client.destination_id = BROADCAST_NUM
    client.enable_verbose(True)
    client.connect()

    send_iss_nodeinfo()
    last_nodeinfo_time = time.time()

    try:
        while True:
            lat, lon, alt = get_iss_location()
            if lat is not None and lon is not None:
                print(f"[ISS] Lat: {lat:.4f}, Lon: {lon:.4f}, Alt: {alt:.2f} m")
                send_position(latitude=lat, longitude=lon, altitude=alt)
                if time.time() - last_nodeinfo_time > 7200:
                    send_iss_nodeinfo()
                    last_nodeinfo_time = time.time()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nDisconnecting...")
        client.disconnect()


if __name__ == "__main__":
    main()
