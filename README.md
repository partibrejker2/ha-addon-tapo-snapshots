# Tapo Snapshot Uploader

A Home Assistant add-on that captures snapshots from Tapo (and compatible RTSP) cameras and uploads them to Google Drive.

---

## 📷 Features

- Captures snapshots from multiple cameras
- Runs every hour between 06:00–22:00
- Skips first few frames for clearer images
- Uploads to Google Drive using a service account
- Configurable camera list in the add-on UI
- Logs success once per round, and errors per camera if needed

---

## 🧠 Requirements

- Google Drive API enabled
- A Google **Service Account JSON** file

---

## 🔐 How to Get `service_account.json`

1. Go to: https://console.cloud.google.com/
2. Create a new project
3. Enable **Google Drive API**
4. Go to **IAM & Admin > Service Accounts**
5. Create a new service account (no role needed)
6. Under **Keys > Add Key > Create JSON Key** → download it
7. Open the add-on in Home Assistant and upload the `service_account.json` file in the UI

---

## 📦 Installation

1. Fork or clone this repo
2. In Home Assistant:
   - Go to **Settings > Add-ons > Add-on Store**
   - Click the **three dots > Repositories**
   - Add your GitHub repo:
     ```
     https://github.com/YOUR_USERNAME/ha-addon-tapo-snapshots
     ```
3. Find the new add-on and click **Install**
4. Configure camera list
5. Upload `service_account.json`
6. Start the add-on

---

## ✅ Example Config in UI

```json
{
  "cameras": [
    {
      "name": "Garage",
      "ip": "192.168.1.100",
      "user": "tapoadmin",
      "pass": "yourpassword"
    },
    {
      "name": "Porch",
      "ip": "192.168.1.101",
      "user": "tapoadmin",
      "pass": "yourpassword"
    }
  ]
}
