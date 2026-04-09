import inspect
from valkka.onvif import OnVif, getWSDLPath, Media, PTZ
from zeep.exceptions import Fault

# --==## Device Management Class ##==--
class DeviceManagementConnection(OnVif):
    namespace = "http://www.onvif.org/ver10/device/wsdl"
    wsdl_file = getWSDLPath("devicemgmt-10.wsdl")
    #sub_addr = "device_service"
    sub_xaddr = "device_service"
    port = "DeviceBinding"


class DeviceManagement():

    def __init__(self, camera, user = None):
        self.connection = None
        self.connect(camera, user)

    def connect(self, camera, user):
        if user == None:
            self.connection = DeviceManagementConnection(
                ip=camera.ip, port=camera.port
            )
            return

        users = [user.username] + (user.alt_usernames or [])

        for username in users:
            all_passwords = [user.password] + user.previous_passwords + user.default_passwords
            for password in all_passwords:
                self.connection = DeviceManagementConnection(
                    ip=camera.ip, port=camera.port,
                    user=username, password=password.get()
                )
                try:
                    self.connection.ws_client.GetUsers()
                    if password.get() != user.password.get():
                        self.set_user_password(user.username, user.password.get())
                    return  # credentials worked, self.connection is set
                except Fault:
                    continue
        raise ValueError(f"Could not authenticate to {camera.ip}")

    # Test Credentials
    def verify_credentials(self):
        try:
            self.get_users()
            return True
        except Fault:
            return False

    # -- User Management Functions --
    def update_user(self, username, password, userlevel):
        user = self.connection.factory.User(
            Username=f"{username}",
            Password=f"{password}",
            UserLevel=f"{userlevel}"
        )
        return self.connection.ws_client.SetUser(User=[user])

    def set_user_password(self, username, password):
        user = self.get_user(username)
        if not user:
            raise ValueError(f"User {username} not found. Cannot update password.")
            return None
        user.Password = password
        return self.connection.ws_client.SetUser(User=[user])

    def set_user_level(self, username, userlevel):
        user = self.get_user(username)
        if not user:
            raise ValueError(f"User {username} not found. Cannot update user level.")
            return None
        user.UserLevel = userlevel
        return self.connection.ws_client.SetUser(User=[user])

    def create_user(self, username, password, userlevel):
        users = self.get_users()
        if self.get_user(username):
            print(f"User {username} already exists. Updating password and user level.")
            return self.update_user(username, password, userlevel)
        user = self.connection.factory.User(
            Username=f"{username}",
            Password=f"{password}",
            UserLevel=f"{userlevel}"
        )
        return self.connection.ws_client.CreateUsers(User=[user])

    def get_users(self):
        return self.connection.ws_client.GetUsers()

    def get_user(self, username):
        users = self.get_users()
        for user in users:
            if user.Username == username:
                return user
        return None
    
    def delete_user(self, username):
        if not self.get_user(username):
            raise ValueError(f"User {username} not found. Cannot delete user.")
            return None
        return self.connection.ws_client.DeleteUsers(Username=[username])

    # -- Camera Discovery Functions --
    def get_device_info(self):
        return self.connection.ws_client.GetDeviceInformation()

    def get_hostname(self):
        return self.connection.ws_client.GetHostname().Name

    def set_hostname(self, hostname):
        return self.connection.ws_client.SetHostname(Name=hostname)

    # -- Camera Network Functions --
    def get_network_interfaces(self):
        return self.connection.ws_client.GetNetworkInterfaces()

    # set_network_interfaces

    def get_default_gateway(self):
        return self.connection.ws_client.GetNetworkDefaultGateway()

    def get_ip_filters(self):
        return self.connection.ws_client.GetIPAddressFilter()

    def get_network_protocols(self):
        return self.connection.ws_client.GetNetworkProtocols()

    # set_network_protocols

    def get_dns(self):
        return self.connection.ws_client.GetDNS()

    #def set_dns

    # -- Camera Time Functions --
    def get_ntp_settings(self):
        return self.connection.ws_client.GetNTP()

    def set_ntp_settings(self, ntp_server, ntp_port):
        return self.connection.ws_client.SetNTP(NTPInformation=self.connection.factory.NTPInformation(
            NTPFromDHCP=False,
            NTPManual=[self.connection.factory.NTPManualType(
                Type="IPv4",
                IPv4Address=ntp_server
            )]
        ))

    def get_date_time(self):
        return self.connection.ws_client.GetSystemDateAndTime()

    def set_date_time(self, date_time_type, timezone, year, month, day, hour, minute, second):
        return self.connection.ws_client.SetSystemDateAndTime(
            DateTimeType=date_time_type,
            TimeZone=self.connection.factory.TimeZone(Type="UTC", TZ=timezone),
            DaylightSavings=False,
            ManualDateAndTime=self.connection.factory.DateTime(
                Year=year,
                Month=month,
                Day=day,
                Hour=hour,
                Minute=minute,
                Second=second
            )
        )

    # -- Camera System Functions --
    def reboot(self):
        return self.connection.ws_client.SystemReboot()