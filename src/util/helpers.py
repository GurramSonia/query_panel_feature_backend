from bson import ObjectId
from datetime import datetime
from Crypto.Cipher import AES
import base64
import hashlib
import base64
from Crypto.Util.Padding import unpad

def convert_objectid_and_datetime(data):
    """Recursively convert ObjectId and datetime in MongoDB results."""
    if isinstance(data, dict):
        print("dictionary")
        return {key: convert_objectid_and_datetime(value) for key, value in data.items()}
     
    elif isinstance(data, list):
        print("list")
        return [convert_objectid_and_datetime(item) for item in data]
    elif isinstance(data, ObjectId):
        print("string")
        return str(data)
    elif isinstance(data, datetime):
        print("datetime")
        return data.strftime('%Y-%m-%d %H:%M:%S')
    return data
def decrypt_password(encrypted_password, token, iv_str):
    
    key = token.encode('utf-8').ljust(32, b'\0')[:32]
    iv = iv_str.encode('utf-8').ljust(16, b'\0')[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(base64.b64decode(encrypted_password))
    return unpad(decrypted, AES.block_size).decode('utf-8')
   
