import os
import json
import crypto
from datetime import datetime, timezone, timedelta

CONFIG_FILE = os.getenv("SITE_AGENT_CONFIG_FILE")
if CONFIG_FILE is None:
    CONFIG_FILE = os.path.join(os.path.dirname(__file__), "site-agent.cfg")
else:
    CONFIG_FILE = os.path.expanduser(CONFIG_FILE)

# Password policy class
class PasswordPolicy:
    def __init__(self):
        self.uppercase = None
        self.lowercase = None
        self.digits = None
        self.special_chars = None
        self.length = None

    # Load and deseralise password policy
    def load(self, password_policy_json: json):
        self.uppercase = password_policy_json["uppercase"]
        self.lowercase = password_policy_json["lowercase"]
        self.digits = password_policy_json["digits"]
        self.special_chars = password_policy_json["special_chars"]
        self.length = password_policy_json["length"]

    def save(self) -> dict:
        password_policy_dict = {
            "uppercase": self.uppercase,
            "lowercase": self.lowercase,
            "digits": self.digits,
            "special_chars": self.special_chars,
            "length": self.length
        }
        return password_policy_dict

    def __repr__(self) -> str:
        return f"PasswordPolicy(uppercase={self.uppercase}, lowercase={self.lowercase}, digits={self.digits}, special_chars={self.special_chars}, length={self.length})"
    
    def __str__(self) -> str:
        return f"PasswordPolicy(uppercase={self.uppercase}, lowercase={self.lowercase}, digits={self.digits}, special_chars={self.special_chars}, length={self.length})"

# Class used to store site information
class Site:
    def __init__(self):
        self.last_sync = None
        self.site_id = None
        self.site_name = None
        self.camera_scan_range = None
        self.camera_scan_interval = None
        self.last_camera_scan = None

    # Load and deseralise Sites
    def load(self, site_json: json):
        self.last_sync = datetime.fromisoformat(site_json["last_sync"]) if site_json["last_sync"] else None
        self.site_id = site_json["site_id"]
        self.site_name = site_json["site_name"]
        self.camera_scan_range = site_json["camera_scan_range"]
        self.camera_scan_interval = site_json["camera_scan_interval"]
        self.last_camera_scan = datetime.fromisoformat(site_json["last_camera_scan"]) if site_json["last_camera_scan"] else None
        Password.site_id = self.site_id

    def save(self) -> dict:
        site_dict = {
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "site_id": self.site_id,
            "site_name": self.site_name,
            "camera_scan_range": self.camera_scan_range,
            "camera_scan_interval": self.camera_scan_interval,
            "last_camera_scan": self.last_camera_scan.isoformat() if self.last_camera_scan else None
        }
        return site_dict

    def add(self, site_id: str, site_name: str, camera_scan_range: str, camera_scan_interval: int):
        self.last_sync = None
        self.site_id = site_id
        self.site_name = site_name
        self.camera_scan_range = camera_scan_range
        self.camera_scan_interval = camera_scan_interval
        self.last_camera_scan = None
        Password.site_id = self.site_id

    def __repr__(self) -> str:
        return f"Site(site_id={self.site_id}, last_sync={self.last_sync})"
    
    def __str__(self) -> str:
        return f"Site(site_id={self.site_id}, last_sync={self.last_sync})"
    
    def __repr__(self):
        return self.__str__()

# Class used to store and retrieve
class Password:
    site_id: str

    def __init__(self, password: str):
        self._password = password

    def get(self):
        return self._password.replace("{site_id}", self.site_id)
    
    def get_original(self):
        return self._password

    def randomise(self):
        self._password = crypto.generate_password(
            length = config.password_policy.length,
            uppercase = config.password_policy.uppercase,
            lowercase = config.password_policy.lowercase,
            digits = config.password_policy.digits,
            special_chars = config.password_policy.special_chars
        )
    
    def __repr__(self) -> str:
        return f"Password=**************"  # prevents password being printed accidentally
    
    def __str__(self) -> str:
        return f"Password=**************"  # prevents password being printed accidentally

# Class used to store users
class User:
    def __init__(self):
        self.username = None
        self.password = None
        self.user_level = None
        self.temp_access = None
        self.last_modified = None
        self.previous_passwords: list[Password] = []
        self.default_passwords: list[Password] = []

    # Load and deseralise user
    def load(self, user_json: json):
        self.username = user_json["username"]
        self.password = Password(user_json["password"])
        self.user_level = user_json["user_level"]
        self.temp_access = user_json["temp_access"]
        self.last_modified = datetime.fromisoformat(user_json["last_modified"]) if user_json["last_modified"] else None
        for prev_password in user_json.get("previous_passwords", []):
            self.add_previous_password(prev_password)
        for default_password in user_json.get("default_passwords", []):
            self.add_default_password(default_password)

    def save(self) -> dict:
        user_dict = {
            "username": self.username,
            "password": self.password.get_original(),
            "user_level": self.user_level,
            "temp_access": self.temp_access,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "previous_passwords": [prev_passwd.get_original() for prev_passwd in self.previous_passwords],
            "default_passwords": [default_passwd.get_original() for default_passwd in self.default_passwords]
        }
        return user_dict

    def add(self, username: str, password: str, user_level: str, temp_access: str):
        self.username = username
        self.password = Password(password)
        self.user_level = user_level
        self.temp_access = temp_access
        self.last_modified = datetime.now(timezone.utc)
    
    def add_previous_password(self, password):
        self.previous_passwords.append(Password(password))

    def add_default_password(self, password):
        self.default_passwords.append(Password(password))

    def last_modified_iso(self):
        return self.last_modified.isoformat if self.last_modified else None

    def __repr__(self) -> str:
        return f"User(username={self.username}, user_level={self.user_level}, temp_access={self.temp_access})"
    
    def __str__(self) -> str:
        return f"User(username={self.username}, user_level={self.user_level}, temp_access={self.temp_access})"

class Approved_Accounts:
    def __init__(self):
        self._users: list[User] = []

    def add(self, user: User):
        if not self.exists(user.username):
            self._users.append(user)
            return 0
        else:
            return 1
    
    def get(self, username: str):
        for user in self._users:
            if username == user.username:
                return user
        return None

    def exists(self, username:str):
        for user in self._users:
            if username == user.username:
                return True
        return False
    
    def remove(self, username: str):
        user = self.get(username)
        if user:
            self._users.remove(user)
            return 0
        else:
            return 1
    
    def count(self):
        return self._users.count()

    def __getitem__(self, index: int):
        return self._users[index]

    def __iter__(self):
        return iter(self._users)
    
    def __str__(self):
        return ", ".join(str(user) for user in self._users)

    def __repr__(self):
        return self.__str__()

# Class used to store TempAccess requests
class TempAccess:
    def __init__(self):
        self.user = None
        self.expiry = None
        self.requested_by = None
        self.requested_id = None
        self.requested_time = None

    # Load and desearlise Temp Access
    def load(self, temp_access_json: json, approved_accounts: Approved_Accounts):
        self.user = approved_accounts.get(temp_access_json["username"])
        self.requested_by = temp_access_json["requested_by"]
        self.requested_id = temp_access_json["requested_id"]
        self.requested_time = datetime.fromisoformat(temp_access_json["requested_time"]) if temp_access_json["requested_time"] else None
        self.expiry = datetime.fromisoformat(temp_access_json["expiry"]) if temp_access_json['expiry'] else None

    def save(self) -> dict:
        temp_access_dict = {
            "username": self.user.username,
            "requested_by": self.requested_by,
            "requested_id": self.requested_id,
            "requested_time": self.requested_time.isoformat() if self.requested_time else None,
            "expiry": self.expiry.isoformat() if self.expiry else datetime.now().isoformat()
        }
        return temp_access_dict

    def add(self, user: User, requested_by: str, requested_id: str, req_days: int):
        if req_days > 5:
            raise ValueError("Temp access cannot exceed 5 days")
        
        if user.temp_access == False:
            raise ValueError("User not allower temporary access password")

        self.user = user
        self.requested_by = requested_by
        self.requested_id = requested_id
        self.requested_time = datetime.now(timezone.utc)
        self.expiry = self.requested_time + timedelta(days=req_days)

    def check_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expiry

    def __repr__(self) -> str:
        return f"TempAccess(username={self.user.username if self.user else None}, expiry={self.expiry}, requested_by={self.requested_by})"
    
    def __str__(self) -> str:
        return f"TempAccess(username={self.user.username if self.user else None}, expiry={self.expiry}, requested_by={self.requested_by})"

class TempAccessRequests:
    def __init__(self):
        self._requests: list[TempAccess] = []

    def add(self, request: TempAccess):
        if not self.exists(request.user.username):
            self._requests.append(request)
            return 0
        else:
            return 1

    def get(self, username: str):
        for request in self._requests:
            if username == request.user.username:
                return request
        return None
    
    def exists(self, username: str):
        for request in self._requests:
            if username == request.user.username:
                return True
        return False
    
    def remove(self, username: str):
        request = self.get(username)
        if request:
            self._requests.remove(request)
            return 0
        else:
            return 1
        
    def count(self):
        return self._requests.count()
    
    def remove_expired(self):
        for request in self._requests:
            if request.check_expired():
                request.user.randomise_password()
                self._requests.remove(request)

    def __getitem__(self, index: int):
        return self._requests[index]
    
    def __iter__(self):
        return iter(self._requests)
    
    def __str__(self):
        return ", ".join(str(request) for request in self._requests)
    
    def __repr__(self):
        return self.__str__()

# Class used to store Cameras
class Camera:
    def __init__(self):
        self.ip = None
        self.port = None
        self.last_discovery = None
        self.manufacturer = None
        self.model = None
        self.serial_number = None
        self.hostname = None
        self.management_account = None
        self.last_seen = None
        self.last_updated = None

    # Load and desearlise Camera
    def load(self, camera_json: json):
        self.ip = camera_json["ip"]
        self.port = camera_json["port"]
        self.manufacturer = camera_json["manufacturer"]
        self.model = camera_json["model"]
        self.serial_number = camera_json["serial_number"]
        self.hostname = camera_json["hostname"]
        self.management_account = camera_json["management_account"]
        self.last_seen = datetime.fromisoformat(camera_json["last_seen"]) if camera_json["last_seen"] else None
        self.last_updated = datetime.fromisoformat(camera_json["last_updated"]) if camera_json["last_updated"] else None

    def save(self) -> dict:
        camera_dict = {
            "ip": self.ip,
            "port": self.port,
            "manufacturer": self.last_discovery,
            "model": self.model,
            "serial_number": self.serial_number,
            "hostname": self.hostname,
            "management_account": self.management_account,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }
        return camera_dict

    def add(self, ip: str, port: int, manufacturer: str, model: str, serial_number: str, hostname: str):
        self.ip = ip
        self.port = port
        self.manufacturer = manufacturer
        self.model = model
        self.serial_number = serial_number
        self.hostname = hostname
        self.last_seen = datetime.now(timezone.utc)
        self.last_updated = datetime.now(timezone.utc)

    def update_last_seen(self):
        self.last_seen = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"Camera(hostname={self.hostname}, ip={self.ip}, manufacturer={self.manufacturer}, model={self.model}), last_seen={self.last_seen}"
    
    def __str__(self) -> str:
        return f"Camera(hostname={self.hostname}, ip={self.ip}, manufacturer={self.manufacturer}, model={self.model}), last_seen={self.last_seen}"    

class Cameras:
    def __init__(self):
        self._cameras: list[Camera] = []

    def add(self, camera: Camera):
        if not self.exists(camera.serial_number):
            self._cameras.append(camera)
            return 0
        else:
            return 1
        
    def get(self, identifier: str):
        for camera in self._cameras:
            if identifier == camera.serial_number:
                return camera
        for camera in self._cameras:
            if identifier == camera.hostname:
                return camera
        return None
    
    def exists(self, identifier: str):
        for camera in self._cameras:
            if identifier == camera.serial_number:
                return True
        for camera in self._cameras:
            if identifier == camera.hostname:
                return True
        return False
    
    def remove(self, identifier: str):
        camera = self.get(identifier)
        if camera:
            self._cameras.remove(camera)
            return 0
        else:
            return 1
        
    def count(self):
        return self._cameras.count()
    
    def __getitem__(self, index: int):
        return self._cameras[index]
    
    def __iter__(self):
        return iter(self._cameras)
    
    def __str__(self):
        return ", ".join(str(camera) for camera in self._cameras)
    
    def __repr__(self):
        return self.__str__()

# Class for storing the site-agent config
class Config:
    def __init__(self):
        self.password_policy = PasswordPolicy()
        self.site = Site()
        self.approved_accounts = Approved_Accounts()
        self.temp_access_requests = TempAccessRequests()
        self.cameras = Cameras()

    def load(self) -> None:
        try:
            with open(CONFIG_FILE, 'r') as config_file:
                raw = config_file.read()
                
                try:
                    decrypted = crypto.decrypt(raw)
                except ValueError:
                    print("WARNING: Config file not encrypted, loading as plain JSON")
                    decrypted = raw
                    # save as encrypted
                
                json_data = json.loads(decrypted)
                
                # Load password policy
                self.password_policy.load(json_data["password_policy"])
                
                # Load Site
                self.site.load(json_data["site"])

                # Load Approved Accounts
                for user_json in json_data["approved_accounts"]:
                    user = User()
                    user.load(user_json)
                    self.approved_accounts.add(user)

                # Load temp access
                for temp_acc_json in json_data["temp_access"]:
                    temp_access_item = TempAccess()
                    temp_access_item.load(temp_acc_json, self.approved_accounts)
                    self.temp_access_requests.add(temp_access_item)

                # Load Cameras
                for camera_json in json_data["cameras"]:
                    camera = Camera()
                    camera.load(camera_json)
                    self.cameras.add(camera)
        
        except FileNotFoundError:
            raise FileNotFoundError(f"{CONFIG_FILE} does not exist.")
        except json.JSONDecodeError as e:
            raise ValueError(f"Config is not valid JSON: {e}")
        except ValueError as e:
            raise ValueError(f"Failed to decrypt config: {e}")

    def save(self) -> None:
        try:
            json_string = json.dumps({
                "password_policy": self.password_policy.save(),
                "site": self.site.save(),
                "approved_accounts": [user.save() for user in self.approved_accounts],
                "temp_access": [request.save() for request in self.temp_access_requests],
                "cameras": [camera.save() for camera in self.cameras]
            })
            encrypted = crypto.encrypt(json_string)
            with open(CONFIG_FILE, 'w') as config_file:
                config_file.write(encrypted)
        except Exception as e:
            raise ValueError(f"Failed to save config: {e}")

config = Config()