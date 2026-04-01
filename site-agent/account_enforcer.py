import onvif_manager
import config_manager
from config_manager import config

def enforce_cameras(config: config_manager.Config):
    # Connect to each camera and enabled

    admin_user = None

    for camera in config.cameras:
        # Find admin account in list of approved accounts
        admin_user = config.approved_accounts.get(camera.management_account)
        if admin_user == None:
            raise ValueError(f"Camera admin_user {camera.management_account} does not exist.")

        # Logon to camera
        onvif_manager.connect_with_fallback(camera, admin_user)

# Debuggings

config.load()
enforce_cameras(config)