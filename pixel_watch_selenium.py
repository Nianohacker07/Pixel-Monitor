#!/usr/bin/env python3
"""
PixelUnlock monitor using Selenium + headless Chromium.
Sends Telegram alert when server goes online.
Reads BOT_TOKEN, CHAT_ID, PIXEL_URL, CHECK_INTERVAL_SECONDS from environment variables.
"""

import os
import time
import requests
from datetime import datetime, timezone
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup

# Config from environment
URL = os.getenv("PIXEL_URL", "https://pixelunlocktool.com/")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", "60"))
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
)

def safe_startup_checks():
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not CHAT_ID:
        missing.append("CHAT_ID")
    if missing:
        raise SystemExit(f"Missing environment variables: {', '.join(missing)}")

def make_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"user-agent={USER_AGENT}")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_binary = os.getenv("CHROME_BIN", "/usr/bin/chromium")
    if os.path.exists(chrome_binary):
        chrome_options.binary_location = chrome_binary
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)
    return driver

def looks_online(html_text: str) -> bool:
    """
    Returns True if PixelUnlockTool server is online, False if offline.
    Uses BeautifulSoup to parse 'Server Status' element.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    status_text = ""
    for tag in soup.find_all(["h1","h2","h3","div","span"]):
        if "Server Status" in tag.get_text():
            status_text = tag.get_text().strip().lower()
            break
    if status_text:
        return "offline" not in status_text
    return False

def notify_telegram(message: str):
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": message},
            timeout=10,
        )
        if resp.status_code != 200:
            print(f"Telegram notify failed: HTTP {resp.status_code}")
    except Exception:
        print("Telegram notification failed, check Railway environment variables.")

def main():
    safe_startup_checks()
    print("Monitor started at", datetime.now(timezone.utc).isoformat())
    sent_alert = False
    driver = None

    while True:
        try:
            if driver is None:
                try:
                    driver = make_driver()
                except WebDriverException as e:
                    print(f"Could not start webdriver: {e}")
                    driver = None
                    time.sleep(CHECK_INTERVAL)
                    continue

            driver.get(URL)
            html = driver.page_source
            online = looks_online(html)
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
            try:
                if driver:
                    driver.quit()
            except Exception:
                pass
            driver = None

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
