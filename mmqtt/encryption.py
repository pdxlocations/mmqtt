import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from meshtastic.protobuf import mesh_pb2

from mmqtt.utils import generate_hash

def decrypt_packet(mp: mesh_pb2.MeshPacket, key: str) -> mesh_pb2.Data | None:
    """
    Decrypt the encrypted message payload and return the decoded Data object.

    Args:
        mp: The MeshPacket with encrypted payload.
        key: Base64-encoded encryption key.

    Returns:
        A decoded mesh_pb2.Data object or None on failure.
    """
    try:
        key_bytes = base64.b64decode(key.encode('ascii'))

        # Build the nonce from message ID and sender
        nonce_packet_id = getattr(mp, "id").to_bytes(8, "little")
        nonce_from_node = getattr(mp, "from").to_bytes(8, "little")
        nonce = nonce_packet_id + nonce_from_node

        # Decrypt the encrypted payload
        cipher = Cipher(algorithms.AES(key_bytes), modes.CTR(nonce), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_bytes = decryptor.update(getattr(mp, "encrypted")) + decryptor.finalize()

        # Parse the decrypted bytes into a Data object
        data = mesh_pb2.Data()
        data.ParseFromString(decrypted_bytes)
        return data

    except Exception as e:
        print(f"Failed to decrypt: {e}")
        return None

def encrypt_packet(channel: str, key: str, mp: mesh_pb2.MeshPacket, encoded_message: mesh_pb2.Data) -> bytes | None:
    """
    Encrypt an encoded message and return the ciphertext.

    Args:
        channel: Channel name or ID.
        key: Base64-encoded encryption key.
        mp: MeshPacket used for ID and from fields (nonce).
        encoded_message: Data object to encrypt.

    Returns:
        The encrypted message bytes or None on failure.
    """
    try:
        mp.channel = generate_hash(channel, key)
        key_bytes = base64.b64decode(key.encode('ascii'))

        nonce_packet_id = getattr(mp, "id").to_bytes(8, "little")
        nonce_from_node = getattr(mp, "from").to_bytes(8, "little")
        
        # Put both parts into a single byte array.
        nonce = nonce_packet_id + nonce_from_node

        cipher = Cipher(algorithms.AES(key_bytes), modes.CTR(nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_bytes = encryptor.update(encoded_message.SerializeToString()) + encryptor.finalize()

        return encrypted_bytes
    
    except Exception as e:
        print(f"Failed to encrypt: {e}")
        return None