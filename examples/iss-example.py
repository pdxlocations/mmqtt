import math
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
        return data["latitude"], data["longitude"], data["altitude"] * 1000, data["velocity"]
    except Exception as e:
        print(f"[ERROR] Failed to fetch ISS location: {e}")
        return None, None, None


def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
    initial_bearing = math.atan2(x, y)
    return (math.degrees(initial_bearing) + 360) % 360


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
    last_lat, last_lon = None, None

    try:
        while True:
            lat, lon, alt, velocity = get_iss_location()
            if lat is not None and lon is not None:
                ground_track = None
                if last_lat is not None and last_lon is not None:
                    ground_track = int(calculate_bearing(last_lat, last_lon, lat, lon))

                print(f"[ISS] Lat: {lat:.4f}, Lon: {lon:.4f}, Alt: {alt:.2f} m, Vel: {velocity:.2f} m/s")
                if ground_track is not None:
                    print(f"      Track: {ground_track:.1f}°")

                send_position(
                    latitude=lat,
                    longitude=lon,
                    altitude=alt,
                    precision=32,
                    ground_speed=int(velocity),
                    ground_track=ground_track,
                )
                last_lat, last_lon = lat, lon
                if time.time() - last_nodeinfo_time > 7200:
                    send_iss_nodeinfo()
                    last_nodeinfo_time = time.time()
            time.sleep(300)
    except KeyboardInterrupt:
        print("\nDisconnecting...")
        client.disconnect()


if __name__ == "__main__":
    main()
