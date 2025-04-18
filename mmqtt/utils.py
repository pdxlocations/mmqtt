from meshtastic.protobuf import portnums_pb2
import random


def get_portnum_name(portnum) -> str:
    """For Logging: Retrieve the name of the port number from the protobuf enum."""
    try:
        return portnums_pb2.PortNum.Name(portnum)  # Use protobuf's enum name lookup
    except ValueError:
        return f"Unknown ({portnum})"  # Handle unknown port numbers gracefully


def protobuf_to_clean_string(proto_message) -> str:
    """For Logging: Convert protobuf message to string and remove newlines."""
    return str(proto_message).replace("\n", " ").replace("\r", " ").strip()


def get_message_id(rolling_message_id: int, max_message_id: int = 4294967295) -> int:
    """Increment the message ID with sequential wrapping and add a random upper bit component to prevent predictability."""
    rolling_message_id = (rolling_message_id + 1) % (max_message_id & 0x3FF + 1)
    random_bits = random.randint(0, (1 << 22) - 1) << 10
    message_id = rolling_message_id | random_bits
    return message_id


def validate_lat_lon_alt(parser, args) -> None:
    # Check if --alt is provided
    if args.alt:
        if not args.lat or not args.lon:
            parser.error("--alt should not be provided without --lat and --lon.")

    # Check if lat and lon are provided
    if args.lat or args.lon or args.pre:
        # If one of lat lon or pre is provided, ensure lat and lon are provided
        if not (args.lat and args.lon):
            parser.error("If you specify --lat, --lon, or --pre, you must specify both --lat and --lon.")
