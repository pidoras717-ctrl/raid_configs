import os
import json
import requests
from datetime import datetime, timedelta

URLS = {
    "Main": "https://assets.nekki.com/raid_configs/master/raid_configs_all.zip",
    "Developer": "https://assets.nekki.com/raid_configs/stage_p4F9e5UAG014kjbbESA/raid_configs_all.zip"
}

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
HISTORY_FILE = os.path.join(os.getcwd(), "history.json")
SCHEDULED_HOURS_UTC = list(range(6, 18))

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print(f"Ошибка при отправке Telegram: {e}")

def check_headers(url: str):
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        headers = response.headers
        return {
            "Status": response.status_code,
            "Last-Modified": headers.get("Last-Modified"),
            "Content-Length": headers.get("Content-Length")
        }
    except requests.RequestException as e:
        return {"error": str(e)}

def format_last_modified(lm_str):
    if not lm_str:
        return "нет данных"
    try:
        dt = datetime.strptime(lm_str, "%a, %d %b %Y %H:%M:%S %Z")
    except ValueError:
        dt = datetime.strptime(lm_str[:-4], "%a, %d %b %Y %H:%M:%S")
    return dt.strftime("%d-%m-%Y %H:%M")

if not os.path.exists(HISTORY_FILE):
    history = {}
else:
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    except json.JSONDecodeError:
        history = {}

now = datetime.utcnow()
current_hour = now.hour
formatted_now = now.strftime("%d-%m-%Y %H:%M")

if current_hour in SCHEDULED_HOURS_UTC:
    next_hour = next((h for h in SCHEDULED_HOURS_UTC if h > current_hour), SCHEDULED_HOURS_UTC[0])
    next_time = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)
    if next_time <= now:
        next_time += timedelta(days=1)
    formatted_next = next_time.strftime("%d-%m-%Y %H:%M")
    send_telegram(f"Workflow запущен по плану: {formatted_now}\nСледующая проверка: {formatted_next}")
else:
    next_time = now.replace(hour=6, minute=0, second=0, microsecond=0)
    if next_time <= now:
        next_time += timedelta(days=1)
    formatted_next = next_time.strftime("%d-%m-%Y %H:%M")
    send_telegram(f"Workflow запущен вне расписания: {formatted_now} UTC\nСледующая проверка: {formatted_next}")

updates = []

for name, url in URLS.items():
    info = check_headers(url)
    prev = history.get(name)

    changed = False
    if prev:
        for key in ["Last-Modified", "Content-Length"]:
            if info.get(key) != prev.get(key):
                changed = True
                break
    else:
        changed = True

    history[name] = info
    lm_formatted = format_last_modified(info.get("Last-Modified"))
    status_msg = f"{formatted_now} - {name} - {'Обновлён' if changed else 'Без изменений'}"
    print(status_msg)

    if changed:
        msg = f"Архив '{name}' обновлён!\nLast-Modified: {lm_formatted}\nРазмер: {info.get('Content-Length')}"
        updates.append(msg)
    else:
        updates.append(f"Архив '{name}' без изменений")

if updates:
    send_telegram("\n\n".join(updates))

with open(HISTORY_FILE, "w") as f:
    json.dump(history, f, indent=2)