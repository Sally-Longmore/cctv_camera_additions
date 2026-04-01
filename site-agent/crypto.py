# **** crypto.py ****
# Provides encryption and decryption of strings

import os
import secrets
import string
from cryptography.fernet import Fernet, InvalidToken

# Set up encryption key for Fernet. This will be injected by AWX at pod deployment
# In dev keyfile will be used
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")

if ENCRYPTION_KEY:
    # Production - key from environment variable
    FERNET_KEY = ENCRYPTION_KEY.encode()
else:
    # Development - key from file
    KEY_FILE = os.path.join(os.path.dirname(__file__), "secret.key")
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            FERNET_KEY = f.read()
    else:
        FERNET_KEY = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(FERNET_KEY)

cipher = Fernet(FERNET_KEY)

# Encrypt string
def encrypt(unencrypted: str) -> str:
    try:
        encrypted = cipher.encrypt(unencrypted.encode()).decode()
        return encrypted
    except InvalidToken:
        raise ValueError("Encryption failed - invalid token or wrong key")

# Decrypt string
def decrypt(encrypted: str) -> str:
    try:
        decrypted = cipher.decrypt(encrypted.encode()).decode()
        return decrypted
    except InvalidToken:
        raise ValueError("Decryption failed - invalid token or wrong key")
    
# Generate Password
def generate_password(length: int, uppercase: bool, lowercase: bool, digits: bool, special_chars: str) -> str:
    valid_chars = ""
    guaranteed = []
    if uppercase:
        valid_chars += string.ascii_uppercase
        guaranteed.append(secrets.choice(string.ascii_uppercase))
    if lowercase:
        valid_chars += string.ascii_lowercase
        guaranteed.append(secrets.choice(string.ascii_lowercase))
    if digits:
        valid_chars += string.digits
        guaranteed.append(secrets.choice(string.digits))
    if special_chars:
        valid_chars += special_chars
        guaranteed.append(secrets.choice(special_chars))

    if not valid_chars:
        raise ValueError("Password policy must allow at least one character type")
    
    password = guaranteed + [secrets.choice(valid_chars) for _ in range(length - len(guaranteed))]

    # Shuffle so guaranteed characters aren't always at the start
    secrets.SystemRandom().shuffle(password)

    return "".join(password)
    
