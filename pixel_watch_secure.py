#!/usr/bin/env python3
"""
Secure PixelUnlock monitor for Railway.
Reads BOT_TOKEN and CHAT_ID from env vars only, never prints them.
Sends Telegram alerts when site appears online.
"""

import os
import time
import requests
from datetime import datetime

# Use requests to call Telegram API directly, avoids heavy libraries and accidental token printing
TELEGRAM_API = "https://api.telegram.org"

URL = os.getenv("PIXEL_URL", "https://pixelunlocktool.com/")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", "60"))

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

USER_AGENT = "pixel-monitor-secure/1.0"
TIMEOUT = 15

def safe_startup_checks():
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not CHAT_ID:
        missing.append("CHAT_ID")
    if missing:
        raise SystemExit(f"Missing env vars: {', '.join(missing)}. Set them in Railway variables and restart.")

def fetch_text(url: str) -> str:
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text

def looks_online(text: str) -> bool:
    t = text.lower()
    if "server status" in t:
        if "offline" in t:
            return False
        return True
    return True

def notify_telegram(message: str):
    # call Telegram sendMessage endpoint directly. Do not log token or chat id.
    try:
        resp = requests.post(
            f"{TELEGRAM_API}/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": message},
            timeout=10
        )
        # do not print resp.text, it can contain echoed message id
        if resp.status_code != 200:
            print("Telegram notify failed.")
    except Exception:
        print("Notification failed, check Railway variables.")

def main():
    safe_startup_checks()
    print("Monitor started at", datetime.utcnow().isoformat())
    sent_alert = False
    while True:
        try:
            text = fetch_text(URL)
            online = looks_online(text)
            ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            print(f"[{ts}] Checked site, online={online}")
            if online and not sent_alert:
                notify_telegram(f"PixelUnlockTool appears ONLINE at {ts}. {URL}")
                print("Alert sent.")
                sent_alert = True
            if not online:
                sent_alert = False
        except requests.RequestException:
            print("Network or HTTP error occurred while checking site.")
        except Exception:
            print("Unexpected error during check.")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
