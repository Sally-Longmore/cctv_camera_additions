import onvif_manager
import config_manager

def enforce_accounts(config: config_manager.Config):
    # Connect to each camera and enabled

    admin_user = None

    for camera in config.cameras:
        # Check if camera is online first
        if camera.online():
            print(f"Camera {camera.hostname} is online, enforcing accounts")
            # Find admin account in list of approved accounts
            admin_user = config.approved_accounts.get(camera.management_account)
            if admin_user == None:
                raise ValueError(f"Camera admin_user {camera.management_account} does not exist.")

            # Logon to camera
            try:
                camera_conn = onvif_manager.DeviceManagement(camera, admin_user)
            except ValueError: # Failed to logon to camera
                return 1
            
            # Check existing users on the camera and remove if not approved
            for user in camera_conn.get_users():
                if not config.approved_accounts.exists(user.Username):
                    camera_conn.delete_user(user.Username)
            
            # Add any accounts that are missing
            for user in config.approved_accounts:
                if not camera_conn.get_user(user.username):
                    camera_conn.create_user(user.username, user.password.get(), user.user_level)
        else:
            print(f"Camera {camera.hostname} is offline")

def enforce_passwords(config: config_manager.Config):
    for camera in config.cameras:
        # Check if camera is online
        if camera.online():
            print(f"Camera {camera.hostname} is online, enforcing passwords")
            # Find admin account in list of approved accounts
            admin_user = config.approved_accounts.get(camera.management_account)
            if admin_user == None:
                raise ValueError(f"Camera admin_user {camera.management_account} does not exist.")

            # Logon to camera
            try:
                camera_conn = onvif_manager.DeviceManagement(camera, admin_user)
            except ValueError: # Failed to logon to camera
                return 1
        
            # Enforce passwords for all accounts that are not using Temp Access
            for user in config.approved_accounts:
                # Check user exists
                if not camera_conn.get_user(user.username):
                    raise ValueError (f"User {user.username} does not exist")

                # Check if user is currently using Temp Access
                if config.temp_access_requests.exists(user.username):
                    # Set account to temp access password
                    user_temp_req = config.temp_access_requests.get(user.username).get_user()
                    camera_conn.set_user_password(user.username, user_temp_req.password.get())
                else:
                    # Set account password to normal password
                    camera_conn.set_user_password(user.username, user.password.get())
        else:
            print(f"Camera {camera.hostname} is offline.")

config = config_manager.Config()
config.load()
enforce_accounts(config)
enforce_passwords(config)