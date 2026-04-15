import onvif_manager
import config_manager

# Enforce approved accounts on cameras
# Creates missing accounts and removes non approved accounts
def enforce_accounts(config: config_manager.Config):
    # Connect to each camera and enabled

    admin_user = None

    for camera in config.cameras:
        # Check if camera is online first
        if camera.online():
            print(f"Camera {camera.hostname} is online, enforcing accounts")
            # Find admin account in list of approved accounts
            camera_model = config.camera_models.get_model(camera.onvif_model)
            if camera_model is None:
                raise ValueError(f"Unknown camera model {camera.onvif_model}, cannot determine management account.")
            admin_user = config.approved_accounts.get(camera_model.management_account)
            if admin_user is None:
                raise ValueError(f"Camera management account {camera_model.management_account} does not exist in approved accounts.")

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

# Enforce current passwords for approved accounts
def enforce_passwords(config: config_manager.Config, username: str = None):
    for camera in config.cameras:
        # Check if camera is online
        if camera.online():
            print(f"Camera {camera.hostname} is online, enforcing passwords")
            # Find admin account in list of approved accounts
            camera_model = config.camera_models.get_model(camera.onvif_model)
            if camera_model is None:
                raise ValueError(f"Unknown camera model {camera.onvif_model}, cannot determine management account.")
            admin_user = config.approved_accounts.get(camera_model.management_account)
            if admin_user is None:
                raise ValueError(f"Camera management account {camera_model.management_account} does not exist in approved accounts.")

            # Logon to camera
            try:
                camera_conn = onvif_manager.DeviceManagement(camera, admin_user)
            except ValueError: # Failed to logon to camera
                return 1

            # Enforce passwords for all accounts that are not using Temp Access
            if username == None:
                users = config.approved_accounts
            else:
                user = config.approved_accounts.get(username)
                if user is None:
                    raise ValueError(f"User {username} does not exist in approved accounts.")
                users = [user]
                        
            for user in users:
                # Check user exists
                if not camera_conn.get_user(user.username):
                    raise ValueError (f"User {user.username} does not exist")

                print(f"Temp access exists for {user.username}: {config.temp_access_requests.exists(user.username)}")
                # Check if user is currently using Temp Access
                if config.temp_access_requests.exists(user.username):
                    # Set account to temp access password
                    user_temp_req = config.temp_access_requests.get(user.username).get_user()
                    camera_conn.set_user_password(user.username, user_temp_req.password.get())
                else:
                    # Set account password to normal password
                    camera_conn.set_user_password(user.username, user.password.get())

            if config.camera_models.get_model(camera.onvif_model).reboot_on_user_change:
                camera_conn.reboot()

        else:
            print(f"Camera {camera.hostname} is offline.")

# Now to work on Temp Access....
def create_temp_access(config: config_manager.Config, username, requested_days, requested_by, requested_id):
    # Check if there is an existing temp access for user, then add or update
    
    temp_request = config.temp_access_requests.get(username)
    password = None

    if temp_request == None:
        temp_request = config_manager.TempAccess()
        user = config.approved_accounts.get(username)
        temp_request.add(user, requested_by, requested_id, requested_days)
        # Set a random password for the user
        temp_request.user.password.randomise(config.password_policy)
        password = temp_request.user.password.get()
        config.temp_access_requests.add(temp_request)
    else:
        temp_request.update(requested_by, requested_id, requested_days)
        password = temp_request.user.password.get()

    print(f"DEBUG: The password for {username} is: {password}")

    config.save()

    # Push password change to cameras
    enforce_passwords(config, username)

    return password

def check_temp_access_expired(config: config_manager.Config):
    # Check for expired accounts and expire
    access_removed = config.temp_access_requests.remove_expired(config.password_policy)

    config.save()

    # Push password change to cameras if there was any changes
    if access_removed:
        enforce_accounts(config)

def remove_temp_access(config: config_manager.Config, username):
    if config.temp_access_requests.exists(username):
        config.temp_access_requests.remove(username)

# config = config_manager.Config()
# config.load()
# enforce_accounts(config)
# enforce_passwords(config)