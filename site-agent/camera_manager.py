import onvif_manager
import config_manager
import onvif_manager
import socket
import ipaddress
from datetime import datetime, timezone, timedelta

# Checks if port 80 or 443 are responding on cameras
# Rases exception of camera is not responding
def get_port(ip: str):
    # Check if responding on port 80
    try:
        socket.create_connection((ip, 80), timeout=2).close()
        return 80
    except (socket.timeout, ConnectionRefusedError, OSError):
        print(f"Camera at IP Address {ip} not responding on port 80")
    # Check if responding on port 443
    try:
        socket.create_connection((ip, 443), timeout=2).close()
        return 443
    except (socket.timeout, ConnectionRefusedError, OSError):
        print(f"Camera at IP Address {ip} not responding on port 443")

# Scans the camera and collects information from ONVIF on camera
def scan_camera(camera, admin_user: list[str]):
    # Test logon to onvif
    camera_conn = onvif_manager.DeviceManagement(camera, admin_user) # Need to try different admin users

    # Get hostname
    camera.hostname = camera_conn.get_hostname()

    # Get Manufacture and Model
    device_info = camera_conn.get_device_info()
    camera.manufacturer = device_info.Manufacturer
    camera.onvif_model = device_info.Model
    camera.serial_number = device_info.SerialNumber
    camera.firmware_version = device_info.FirmwareVersion

    # Get Network Information
    dns = camera_conn.get_dns()
    protocols = camera_conn.get_network_protocols()
    for network_if in camera_conn.get_network_interfaces():
        interface_name = network_if.Info.Name
        existing = next((ni for ni in camera.network_information if ni.interface == interface_name), None)
        if existing:
            net_info = existing
        else:
            net_info = config_manager.NetworkInformation()
            camera.network_information.append(net_info)
        net_info.load(network_if)
        net_info.dns.load(dns)
        net_info.protocols.load(protocols)

    # Get Configured Users and User Levels, start fresh each time to avoid issues with deleted users
    camera.users.clear()
    users = camera_conn.get_users()
    for user in users:
        existing = next((u for u in camera.users if u.username == user.Username), None)
        if existing:
            cam_user = existing
        else:
            cam_user = config_manager.CameraUser()
            camera.users.append(cam_user)
        cam_user.username = user.Username
        cam_user.user_level = user.UserLevel

    # Get Date/Time and NTP settings
    date_time = camera_conn.get_date_time()
    ntp_settings = camera_conn.get_ntp_settings()
    camera.date_time.load(date_time, ntp_settings)

    # Set last seen and last updted tmie
    camera.last_seen = datetime.now(timezone.utc)
    camera.last_updated = datetime.now(timezone.utc)

# Detects cameras in the IP address range6
# and then scans the cameras for information
def detect(config: config_manager.Config):
    # Iterate through the IP address range
    start = config.site.camera_scan_range.start
    end = config.site.camera_scan_range.end

    for ip in range(int(start), int(end) + 1):
        try:
            ip = ipaddress.IPv4Address(ip)
            port = get_port(ip.exploded)

            admin_user = config.approved_accounts.get("admin")

            if port != None:
                
                print(f"Camera at {ip.exploded} responded on port {port}")

                camera = config_manager.Camera()
                camera_exists = False
            
                # See if a camera already exists, if so load the camera
                if config.cameras.exists(ip.exploded):
                    camera = config.cameras.get(ip.exploded)
                    camera_exists = True
                
                camera.ip = ip.exploded
                camera.port = port

                scan_camera(camera, admin_user)

                if not camera_exists:
                    config.cameras.add(camera)

                print(f"Hostname: {camera.hostname} | IP: {camera.ip}")

            else:
                print(f"Failed find a camera at IP address {ipaddress.IPv4Address(ip)}")

        except Exception as e:
            print(f"Failed find a camera at IP address {ipaddress.IPv4Address(ip)}: {e}")
                        

# Scans existing cameras to see if they are still online
# and if they are updates information from ONVIF
def scan_existing(config):

    admin_user = config.approved_accounts.get("admin")

    for camera in config.cameras:
        try:
            scan_camera(camera, admin_user)
            print(f"Camera {camera.hostname} at {camera.ip} scan complete")

        except:
            print(f"Camera {camera.hostname} at {camera.ip} is not online")
            camera.last_updated = datetime.now(timezone.utc)

# Checks each of the existing cameras to see if the
# camera is stale. If the camera is stale, then
# the camera is removed.
def remove_stale_cameras(config):

    stale_cameras: list[config_manager.Camera] = []

    stale_date = datetime.now(timezone.utc) - timedelta(days = config.site.camera_max_days_offline)

    for camera in config.cameras:
        
        if camera.last_seen and camera.last_seen < stale_date:
            stale_cameras.append(camera)

    for camera in stale_cameras:
        config.cameras.remove(camera.serial_number)

def configure_camera(config: config_manager.Config):
    for camera in config.cameras:
        if camera.online():
            reboot_required = False

            print(f"Camera {camera.hostname} is online, configuring")
            # Find admin account in list of approved accounts
            camera_model = config.camera_models.get_model(camera.onvif_model)
            if camera_model is None:
                raise ValueError(f"Unknown camera model {camera.onvif_model}, cannot determine management account.")
            user = config.approved_accounts.get(camera_model.management_account)
            if user is None:
                raise ValueError(f"Camera management account {camera_model.management_account} does not exist in approved accounts.")

            # Logon to camera
            try:
                camera_conn = onvif_manager.DeviceManagement(camera, user)
            except ValueError: # Failed to logon to camera
                return 1

            # Set hostname
            camera_name = str(camera.camera_name).lower().replace(" ", "-")
            camera_name = ''.join(c for c in camera_name if c.isalnum() or c == '-')
            if getattr(camera, "camera_name", None) and camera.hostname != camera_name:
                camera_conn.set_hostname(camera_name)
                camera.hostname = camera_conn.get_hostname()

            # Set NTP Settings
            camera_conn.set_ntp_settings(config.ntp.servers, config.ntp.timezone)
            
            # Get offset between camera time and NTP server time
            camera.date_time.camera_time = camera_conn.get_date_time()
            camera.date_time.get_offset_seconds()


            # If time offset is more than reboot_offset_seconds, then reboot camera to update time
            if ((camera.date_time.seconds_offset < config.ntp.reboot_offset_seconds * -1 or
                camera.date_time.seconds_offset > config.ntp.reboot_offset_seconds) and
                config.ntp.reboot_if_offset_exceeded):
                reboot_required = True  


            # If reboot required, then reboot camera
            if reboot_required:
                print(f"Camera {camera.hostname} requires reboot to update time, rebooting")
                camera_conn.reboot()

        else:
            print(f"Camera {camera.hostname} is offline")


