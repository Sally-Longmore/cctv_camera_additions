import csv
from valkka.onvif import OnVif, getWSDLPath, Media
from cryptography.fernet import Fernet

class User:
    username = ""
    password = ""
    userlevel = ""

    def __init__(self, username, password, userlevel):
        self.username = username
        self.password = password
        self.userlevel = userlevel

    def get_password(self):
        decryptedPassword = fernet.decrypt((self.password).encode()).decode()
        return decryptedPassword


def user_exists(username):


def update_user(username, password, userlevel):
    # Check if user exists

def encrypt_password(password: str) -> str:
    encrypted = fernet.encrypt(password.encode()).decode()
    return encrypted

with open("useraccounts.csv", "r") as user_accounts_file:
    user_accounts_reader = csv.DictReader(user_accounts_file)
    for row in user_accounts_reader:
        update_user(row["username"], row["password"], row["userlevel"])