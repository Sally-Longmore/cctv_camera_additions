import config_manager
import camera_manager
import account_manager


config = config_manager.Config()
config.load()

account_manager.remove_temp_access(config, "installer")
print(account_manager.create_temp_access(config, "installer", 0.01, "Sally Longmore", "1167800"))
config.temp_access_requests.remove_expired(config.password_policy)

camera_manager.detect(config)
camera_manager.scan_existing(config)

config.save()

print("here")
