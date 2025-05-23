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

MAX_RETRIES = 3

def is_valid_frame(frame):
    if frame is None:
        return False
    if frame.shape[0] < 100 or frame.shape[1] < 100:
        return False
    if cv2.countNonZero(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)) < 1000:
        return False
    return True
    
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
                        cap.read()  # Flush bad frames

                    ret, frame = cap.read()
                    retries = 0

                    while (not ret or not is_valid_frame(frame)) and retries < MAX_RETRIES:
                        print(f"⚠️ Bad frame detected from {name}, retrying ({retries+1})...")
                        time.sleep(1)
                        ret, frame = cap.read()
                        retries += 1

                    cap.release()

                    if not ret or not is_valid_frame(frame):
                        raise Exception("Failed to grab a valid frame after retries")

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
            elif not all_success:
                print("⚠️ Snapshot round completed with some errors.")
        else:
            print(f"⏰ Skipped – outside capture window ({START_HOUR}:00–{END_HOUR}:00)")

        print(f"⏳ Sleeping for {INTERVAL_SECONDS} seconds...\n")
        time.sleep(INTERVAL_SECONDS)

except KeyboardInterrupt:
    print("🛑 Add-on stopped")
