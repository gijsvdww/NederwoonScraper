import os,json
import time
import requests,re
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN_ENV")
CHAT_ID = "8320757090"
NEDERWOON_URL = "https://www.nederwoon.nl/search?search_type=1&city=arnhem+"

SENT_FILE= "send.json"

def load_send():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return set(json.load(f))

def save_sent(send_objects):
    with open(SENT_FILE, "w") as f:
        json.dump(list(send_objects), f)


def send_notification(message: str):
    print("notificatie")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    r = requests.post(url, data=payload)
    return r.json()

def send_locations(lat: int, lon: int):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendLocation"
    payload = {"chat_id": CHAT_ID, "latitude": lat, "longitude": lon}
    requests.post(url, data=payload)

def send_pictures(pic_url: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    payload = {"chat_id": CHAT_ID, "photo": pic_url}
    requests.post(url, data=payload)


def getNieuweWoningen(send_objects):
    r = requests.get(NEDERWOON_URL)
    soup = BeautifulSoup(r.text, 'html.parser')

    woningen = []

    for loc in soup.select("div.location"):
        # Adres
        adres = loc.select_one("p.color-medium.fixed-lh")
        adres = adres.get_text(strip=True) if adres else None

        # Type
        object_type = loc.select_one("p.color-primary.fixed-lh")
        object_type = object_type.get_text(strip=True) if object_type else None

        # Prijs
        prijs = loc.select_one("p.heading-md.text-regular.color-primary")
        if prijs:
            raw = prijs.get_text(strip=True)
        prijs = re.sub(r"[^\d,€]", "", raw)

        # Afbeeldingen
        afbeeldingen = [
            img.get("data-src") or img.get("src")
            for img in loc.select(".slider img")
            if img.get("data-src") or img.get("src")
        ]

        # Detail link (optioneel: neem eerste <a> in het blok)
        link = None
        a_tag = loc.select_one("a[href]")
        if a_tag:
            link = a_tag["href"]
            link = "nederwoon.nl" + link

        woningen.append({
            "adres": adres,
            "type": object_type,
            "prijs": prijs,
            "afbeeldingen": afbeeldingen,
            "link": link
        })

    nieuwe_woning = [obj for obj in woningen if obj['link'] not in send_objects]
    return nieuwe_woning

def verstuurBericht(woning):
    send_notification(f"LET OP!! Er is een nieuwe woning!\nAdres: {woning['adres']}\ntype: {woning['type']}\nprijs: {woning['prijs']}\nlink: {woning['link']}")
    for img in woning['afbeeldingen']:
        send_pictures("nederwoon.nl" + img)

def mainLoop():
    sent_objects = set()
    try:
        sent_objects = load_send()
    except:
        print("no sent objects found yet")
    while True:
        try:
            print("checking...", flush=True)
            nieuweWoningen = getNieuweWoningen(sent_objects)
            for woning in nieuweWoningen:
                print("woning gevonden, berichten worden verstuurd.....", flush=True)
                verstuurBericht(woning)
                sent_objects.add(woning['link'])
                save_sent(sent_objects)
            requests.get("https://hc-ping.com/b8b5db0a-75a5-4093-aa68-9f38f505374a")
            print("heartbeat")
            time.sleep(20)
        except Exception as e:
            verstuurBericht(f"error in loop: {e}, restarting...")
            raise

if __name__ == "__main__":
    mainLoop()
