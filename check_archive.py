import os
import json
import requests
from datetime import datetime

URLS = {
    "Main": "https://assets.nekki.com/raid_configs/master/raid_configs_all.zip",
    "Developer": "https://assets.nekki.com/raid_configs/stage_p4F9e5UAG014kjbbESA/raid_configs_all.zip"
}

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
HISTORY_FILE = "history.json"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

def check_headers(url: str):
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        headers = response.headers
        return {
            "Status": response.status_code,
            "Last-Modified": headers.get("Last-Modified"),
            "Content-Length": headers.get("Content-Length"),
            "ETag": headers.get("ETag")
        }
    except requests.RequestException as e:
        return {"error": str(e)}

if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        history = json.load(f)
else:
    history = {}

updates = []

for name, url in URLS.items():
    info = check_headers(url)
    prev = history.get(name)

    changed = False
    if prev:
        for key in ["ETag", "Last-Modified", "Content-Length"]:
            if info.get(key) != prev.get(key):
                changed = True
                break
    else:
        changed = True

    history[name] = info

    status_msg = f"{datetime.now()} - {name} - {'Обновлён' if changed else 'Без изменений'}"
    print(status_msg)

    if changed:
        msg = f"Архив '{name}' обновлён!\n"
        msg += f"ETag: {info.get('ETag')}\n"
        msg += f"Last-Modified: {info.get('Last-Modified')}\n"
        msg += f"Размер: {info.get('Content-Length')}"
        updates.append(msg)

if updates:
    send_telegram("\n\n".join(updates))

with open(HISTORY_FILE, "w") as f:
    json.dump(history, f, indent=2)