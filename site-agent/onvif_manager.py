import inspect
from valkka.onvif import OnVif, getWSDLPath, Media, PTZ
from zeep.exceptions import Fault

# --==## Device Management Class ##==--
class DeviceManagement(OnVif):
    namespace = "http://www.onvif.org/ver10/device/wsdl"
    wsdl_file = getWSDLPath("devicemgmt-10.wsdl")
    #sub_addr = "device_service"
    sub_xaddr = "device_service"
    port = "DeviceBinding"

def connect_device_service(ip, port, user, password):
    return DeviceManagement(
        ip = ip,
        port = port,
        user = user,
        password = password
    )

# Test Credentials
def verify_credentials(device_service):
    try:
        get_users(device_service)
        return True
    except Fault:
        return False

def connect_with_fallback(camera, user):
    all_passwords = [user.password] + user.previous_passwords + user.default_passwords
    for password in all_passwords:
        device_service = connect_device_service(
            camera.ip, camera.port, user.username, password.get()
        )
        if verify_credentials(device_service):
            if password.get() != user.password.get():
                set_user_password(device_service, user.username, user.password.get())
            return device_service
    raise ValueError(f"Could not authenticate to {camera.ip} — no valid password found")

# -- User Management Functions --
def update_user(device_service, username, password, userlevel):
    user = device_service.factory.User(
        Username=f"{username}",
        Password=f"{password}",
        UserLevel=f"{userlevel}"
    )
    return device_service.ws_client.SetUser(User=[user])

def set_user_password(device_service, username, password):
    user = get_user(device_service, username)
    if not user:
        raise ValueError(f"User {username} not found. Cannot update password.")
        return None
    user.Password = password
    return device_service.ws_client.SetUser(User=[user])

def set_user_level(device_service, username, userlevel):
    user = get_user(device_service, username)
    if not user:
        raise ValueError(f"User {username} not found. Cannot update user level.")
        return None
    user.UserLevel = userlevel
    return device_service.ws_client.SetUser(User=[user])

def create_user(device_service, username, password, userlevel):
    users = get_users(device_service)
    if get_user(device_service, username):
         print(f"User {username} already exists. Updating password and user level.")
         return update_user(device_service, username, password, userlevel)
    user = device_service.factory.User(
        Username=f"{username}",
        Password=f"{password}",
        UserLevel=f"{userlevel}"
    )
    return device_service.ws_client.CreateUsers(User=[user])

def get_users(device_service):
    return device_service.ws_client.GetUsers()

def get_user(device_service, username):
    users = get_users(device_service)
    for user in users:
        if user.Username == username:
            return user
    return None
   
def delete_user(device_service, username):
    if not get_user(device_service, username):
        raise ValueError(f"User {username} not found. Cannot delete user.")
        return None
    return device_service.ws_client.DeleteUsers(Username=[username])

# -- Camera Discovery Functions --
def get_device_info(device_service):
    return device_service.ws_client.GetDeviceInformation()

def get_hostname(device_service):
    return device_service.ws_client.GetHostname()

def set_hostname(device_service, hostname):
    return device_service.ws_client.SetHostname(HostnameInformation=device_service.factory.HostnameInformation(Name=hostname))

# -- Camera Network Functions --
def get_network_interfaces(device_service):
    return device_service.ws_client.GetNetworkInterfaces()

# set_network_interfaces

def get_default_gateway(device_service):
    return device_service.ws_client.GetNetworkDefaultGateway()

def get_ip_filters(device_service):
    return device_service.ws_client.GetIPAddressFilter()

def get_network_protocols(device_service):
    return device_service.ws_client.GetNetworkProtocols()

# set_network_protocols

def get_dns(device_service):
    return device_service.ws_client.GetDNS()

#def set_dns

# -- Camera Time Functions --
def get_ntp_settings(device_service):
    return device_service.ws_client.GetNTP()

def set_ntp_settings(device_service, ntp_server, ntp_port):
    return device_service.ws_client.SetNTP(NTPInformation=device_service.factory.NTPInformation(
        NTPFromDHCP=False,
        NTPManual=[device_service.factory.NTPManualType(
            Type="IPv4",
            IPv4Address=ntp_server
        )]
    ))

def get_date_time(device_service):
    return device_service.ws_client.GetSystemDateAndTime()

def set_date_time(device_service, date_time_type, timezone, year, month, day, hour, minute, second):
    return device_service.ws_client.SetSystemDateAndTime(
        DateTimeType=date_time_type,
        TimeZone=device_service.factory.TimeZone(Type="UTC", TZ=timezone),
        DaylightSavings=False,
        ManualDateAndTime=device_service.factory.DateTime(
            Year=year,
            Month=month,
            Day=day,
            Hour=hour,
            Minute=minute,
            Second=second
        )
    )

# -- Camera System Functions --
def reboot(device_service):
    return device_service.ws_client.SystemReboot()