import inspect
from valkka.onvif import OnVif, getWSDLPath, Media, PTZ

# Device Management Class
class DeviceManagement(OnVif):
    namespace = "http://www.onvif.org/ver10/device/wsdl"
    wsdl_file = getWSDLPath("devicemgmt-10.wsdl")
    #sub_addr = "device_service"
    sub_xaddr = "device_service"
    port = "DeviceBinding"

# Device Management Connector
device_service = DeviceManagement(
    ip = "10.10.1.195",
    port = 80,
    user = "admin",
    password = "Andno1cares"
)

getusers = device_service.ws_client.GetUsers()
print(getusers)

username = "test_viewer_2"
password = "P@ssw0rd"
userlevel = "Administrator"

# user = device_service.factory.User(
#     Username="test_viewer",
#     Password="N3wP@ssw0rd",
#     UserLevel="Administrator"
# )

# setuser = device_service.ws_client.SetUser(User=[user]) 

user = device_service.factory.User(
    Username=f"{username}",
    Password=f"{password}",
    UserLevel=f"{userlevel}"
)

createuser = device_service.ws_client.CreateUsers(User=[user]) 


# # Media Connector
# media_service = Media(
#     ip = "10.10.1.195",
#     port = 80,
#     user = "admin",
#     password = "Andno1cares"
# )

# # PTZ Control Connector
# ptz_service = PTZ(
#     ip = "192.168.2.11",
#     port = 80,
#     user = "admin",
#     password = "PASSwordz"
# )

# Get profiles
# Need to work out how to extract the profile name form the object
# I think Profile_1 is stream 1, Profile_2 is stream 2 and Profile_3 is stream 3
# profiles = media_service.ws_client.GetProfiles()
# print("-----------------------------")
# print(" Profiles")
# print("-----------------------------")
# print(profiles)


# Get current status of the Camera
# Shows the position of the Camrea
# Shows if the camera is idle or moving
# Y is tilt and is from 1 (Up) to 0 (Down)
# X is rotation:
#       0° = 0
#       45 = 0.25
#       90° = 0.5
#       135° = 0.75
#       180° = 1
#       225° = -0.75
#       270° = -0.5
#       315° = -0.25
# camstatus = ptz_service.ws_client.GetStatus('Profile_1')
# print("-----------------------------")
# print(" CamStatus (GetStatus)")
# print("-----------------------------")
# print(camstatus)

# Take Snapshot
# snapshot = media_service.ws_client.GetSnapshotUri('Profile_1')
# print("-----------------------------")
# print(" Snapshot")
# print("-----------------------------")
# print(snapshot)

