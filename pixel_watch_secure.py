#!/usr/bin/env python3
"""
Secure PixelUnlock monitor for Railway.
Bypasses Cloudflare with cloudscraper.
Reads BOT_TOKEN and CHAT_ID from environment variables only.
Sends Telegram alerts when site appears online.
"""

import os
import time
from datetime import datetime, timezone
import cloudscraper

# Config from environment variables
URL = os.getenv("PIXEL_URL", "https://pixelunlocktool.com/")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", "60"))

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Realistic User-Agent to avoid Cloudflare blocks
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"

def safe_startup_checks():
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not CHAT_ID:
        missing.append("CHAT_ID")
    if missing:
        raise SystemExit(f"Missing environment variables: {', '.join(missing)}")

def fetch_text(url: str) -> str:
    """
    Fetch the page using cloudscraper to bypass Cloudflare.
    """
    scraper = cloudscraper.create_scraper(browser={'custom': USER_AGENT})
    r = scraper.get(url, timeout=15)
    r.raise_for_status()
    return r.text

def looks_online(text: str) -> bool:
    """
    Determines if the PixelUnlockTool server is online.
    """
    t = text.lower()
    if "server status" in t:
        return "offline" not in t
    return True

def notify_telegram(message: str):
    """
    Sends a message via Telegram API using environment variables.
    """
    import requests
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": message},
            timeout=10
        )
        if resp.status_code != 200:
            print(f"Telegram notify failed: HTTP {resp.status_code}")
    except Exception:
        print("Notification failed, check Railway environment variables.")

def main():
    safe_startup_checks()
    print("Monitor started at", datetime.now(timezone.utc).isoformat())
    sent_alert = False

    while True:
        try:
            text = fetch_text(URL)
            online = looks_online(text)
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            print(f"[{ts}] Checked site, online={online}")

            if online and not sent_alert:
                notify_telegram(f"PixelUnlockTool appears ONLINE at {ts}. {URL}")
                print("Alert sent to Telegram.")
                sent_alert = True
            if not online:
                sent_alert = False

        except Exception as e:
            print(f"Network/HTTP error occurred: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
