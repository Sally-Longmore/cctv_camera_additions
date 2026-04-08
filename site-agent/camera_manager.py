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
    
    # Set last seen and last updted tmie
    camera.last_seen = datetime.now(timezone.utc)
    camera.last_updated = datetime.now(timezone.utc)

# Detects cameras in the IP address range
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

        except:
            print(f"Failed find a camera at IP address {ipaddress.IPv4Address(ip)}")
                        

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
