# Use slim Python base
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# install chrome (Chromium) and dependencies, plus fonts for headless rendering
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    wget \
    unzip \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# set chrome binary env in container so script can find it
ENV CHROME_BIN=/usr/bin/chromium

# copy code
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
# make script executable
RUN chmod +x /app/pixel_watch_selenium.py

# start command
CMD ["python", "/app/pixel_watch_selenium.py"]
