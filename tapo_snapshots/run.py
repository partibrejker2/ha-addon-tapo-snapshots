import os
import time
import json
from datetime import datetime
import cv2
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

CONFIG_PATH = "/data/options.json"
# Load config
with open(CONFIG_PATH, "r") as f:
    options = json.load(f)
SERVICE_ACCOUNT_PATH = "/data/service_account.json"
INTERVAL_SECONDS = options.get("interval_seconds", 3600)
START_HOUR = options.get("start_hour", 0)
END_HOUR = options.get("end_hour", 24)
cameras = options.get("cameras", [])

service_account_json = options.get("service_account", "")
if not service_account_json:
    print("❌ Missing service account data")
    exit(1)

with open("/data/service_account.json", "w") as f:
    f.write(service_account_json)
    
# Check for credentials
if not os.path.exists(SERVICE_ACCOUNT_PATH):
    print("❌ Missing service_account.json in /data/")
    exit(1)

# Auth setup
with open("settings.yaml", "w") as f:
    f.write(f"""
client_config_backend: service
service_config:
  client_json_file_path: {SERVICE_ACCOUNT_PATH}
""")

gauth = GoogleAuth(settings_file="settings.yaml")
gauth.ServiceAuth()
drive = GoogleDrive(gauth)

# Create drive folder
def get_or_create_folder(name, parent_id=None):
    q = f"title='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        q += f" and '{parent_id}' in parents"
    folders = drive.ListFile({'q': q}).GetList()
    if folders:
        return folders[0]['id']
    metadata = {'title': name, 'mimeType': 'application/vnd.google-apps.folder'}
    if parent_id:
        metadata['parents'] = [{'id': parent_id}]
    folder = drive.CreateFile(metadata)
    folder.Upload()
    return folder['id']

root_folder = get_or_create_folder("TapoSnapshots")
cam_folders = {cam['name']: get_or_create_folder(cam['name'], root_folder) for cam in cameras}

# Main loop
try:
    while True:
        now = datetime.now()
        if START_HOUR <= now.hour < END_HOUR:
            all_success = True
            for cam in cameras:
                name, ip, user, password = cam['name'], cam['ip'], cam['user'], cam['pass']
                timestamp = now.strftime("%Y%m%d_%H%M%S")
                filename = f"{name}_{timestamp}.jpg"
                filepath = f"/tmp/{filename}"
                rtsp = f"rtsp://{user}:{password}@{ip}/stream1"

                try:
                    cap = cv2.VideoCapture(rtsp)
                    time.sleep(2)
                    for _ in range(3):
                        cap.read()
                    ret, frame = cap.read()
                    cap.release()

                    if not ret:
                        raise Exception("Failed to grab frame")

                    cv2.imwrite(filepath, frame)
                    gfile = drive.CreateFile({
                        'title': filename,
                        'parents': [{'id': cam_folders[name]}]
                    })
                    gfile.SetContentFile(filepath)
                    gfile.Upload()
                    gfile.content.close()
                    os.remove(filepath)

                except Exception as e:
                    all_success = False
                    print(f"❌ {name}: {e}")

            if all_success:
                print("✅ All camera snapshots uploaded successfully")

        time.sleep(INTERVAL_SECONDS)

except KeyboardInterrupt:
    print("🛑 Add-on stopped")
