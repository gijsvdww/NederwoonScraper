
# Nederwoon Scraper Bot

Een Python-bot die automatisch nieuwe woningen van [Nederwoon](https://www.nederwoon.nl/) scrape’t en notificaties verstuurt via een Telegram-bot.  
De bot draait in een loop en houdt bij welke woningen al verstuurd zijn zodat je geen dubbele meldingen ontvangt.  
Daarnaast is er een heartbeat toegevoegd waarmee je eenvoudig kunt monitoren of de bot nog draait.

---

## 🚀 Functionaliteit
- Scrapen van nieuwe woningen via Nederwoon.
- Verzenden van notificaties naar een Telegram-chat (inclusief adres, type, prijs, link en afbeeldingen).
- Bijhouden van reeds verstuurde woningen in een lokaal JSON-bestand (`send.json`).
- Heartbeat call naar een externe URL om uptime te monitoren.
- Automatisch draaien als systemd-service op een DigitalOcean droplet.

---

## 🛠️ Vereisten
- Python 3.9+ (bij voorkeur via een virtual environment).
- Een Telegram Bot Token en Chat ID. (zie: https://core.telegram.org/bots/tutorial voor uitleg over de telegram bot)
- Een healthcheck endpoint (zie: https://healthchecks.io/)
- Toegang tot een Linux server (bijvoorbeeld een DigitalOcean droplet, de meest lichtgewicht droplet bij DigitalOcean is ruimschoots genoeg en 4$/maand).
- Git voor versiebeheer.

---

## 📦 Installatie & lokaal testen

### 1. Repo clonen
```bash
git clone git@github.com:jouw-gebruikersnaam/nederwoonScraper.git
cd nederwoonScraper
````

### 2. Virtual environment aanmaken

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Dependencies installeren

```bash
pip install -r requirements.txt
```

### 4. `.env` bestand maken

Maak een bestand `.env` in de root van je project met daarin:

```
BOT_TOKEN_ENV=plak_hier_je_telegram_bot_token
CHAT_ID=plak_hier_je_chat_id
NEDERWOON_URL=https://www.nederwoon.nl/search?search_type=1&city=arnhem+
HEARTBEAT_URL=https://uptime-kuma-of-andere-url
```

### 5. Lokaal draaien

```bash
python main.py
```

Als alles goed gaat zie je logs in je terminal, en krijg je notificaties in je Telegram.

---

## 📡 Deployen naar een DigitalOcean droplet

### 1. Inloggen op je droplet

```bash
ssh root@<DROPLET-IP>
```

### 2. Repo clonen op de droplet

```bash
git clone git@github.com:jouw-gebruikersnaam/nederwoonScraper.git
cd nederwoonScraper
```

### 3. Virtual environment maken en dependencies installeren

```bash
python3 -m venv bot-env
source bot-env/bin/activate
pip install -r requirements.txt
```

### 4. `.env` bestand aanmaken

Maak op de droplet een bestand `/root/NederwoonScraper/.env`:

```
BOT_TOKEN_ENV=plak_hier_je_telegram_bot_token
CHAT_ID=plak_hier_je_chat_id
NEDERWOON_URL=https://www.nederwoon.nl/search?search_type=1&city=arnhem+
HEARTBEAT_URL=https://uptime-kuma-of-andere-url
```

### 5. Startscript maken

Het bestand `start_bot.sh` (staat al in de repo) zorgt dat de juiste virtual environment wordt gebruikt:

```bash
#!/bin/bash
source /root/NederwoonScraper/bot-env/bin/activate
exec /root/NederwoonScraper/bot-env/bin/python /root/NederwoonScraper/main.py
```

Zorg dat het uitvoerbaar is:

```bash
chmod +x start_bot.sh
```

### 6. Systemd-service instellen

Het bestand `scraperservice.service` (staat al in de repo) zorgt dat je bot automatisch start:

```ini
[Unit]
Description=Nederwoon Scraper Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/NederwoonScraper
EnvironmentFile=/root/NederwoonScraper/.env
ExecStart=/root/NederwoonScraper/start_bot.sh
Restart=always
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Kopieer dit naar systemd:

```bash
sudo cp scraperservice.service /etc/systemd/system/nederwoonScraper.service
sudo systemctl daemon-reload
sudo systemctl enable nederwoonScraper.service
sudo systemctl start nederwoonScraper.service
```

### 7. Logs bekijken

```bash
sudo journalctl -u nederwoonScraper.service -f
```

Hier zie je dezelfde `print`-statements als bij lokaal testen.

---

## 🔍 Debuggen

* Service status bekijken:

  ```bash
  sudo systemctl status nederwoonScraper.service
  ```
* Service opnieuw starten:

  ```bash
  sudo systemctl restart nederwoonScraper.service
  ```
* Droplet herstarten:

  ```bash
  sudo reboot
  ```

---

## 📝 Bestanden in deze repo

* `main.py` → hoofdscript met scraper en Telegram-integratie.
* `requirements.txt` → Python dependencies.
* `start_bot.sh` → script om de bot vanuit de virtualenv te starten.
* `scraperservice.service` → systemd-servicebestand om de bot automatisch te starten.
* `.env` (niet in git) → configuratiebestand met tokens en URL’s.
* `send.json` (wordt automatisch gemaakt) → opslag van reeds verstuurde woningen.

---

## ⚠️ Let op

* Sla je `.env` bestand **nooit** op in git.
* Houd je bot token en chat ID geheim.
* Dit project is bedoeld voor educatief gebruik; scraping kan tegen de voorwaarden van een site zijn.

---

## 🤝 Bijdragen

Pull requests zijn welkom!
Open een issue als je ideeën hebt of bugs tegenkomt.

