import os
import time

import requests,re
from bs4 import BeautifulSoup


BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = "8320757090"
NEDERWOON_URL = "https://www.nederwoon.nl/search?search_type=1&city=arnhem+"

sent_objects = set()

def getNieuweWoningen():
    r = requests.get(NEDERWOON_URL)
    soup = BeautifulSoup(r.text, 'html.parser')

    print(soup)

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

    nieuwe_woning = [obj for obj in woningen if obj['url'] not in sent_objects]
    return nieuwe_woning

def verstuurBericht(woning):
    send_notification(f"LET OP!! Er is een nieuwe woning!\nAdres: {woning['adres']}\ntype: {woning['type']}\nprijs: {woning['prijs']}\nlink: {woning['link']}")
    for img in woning['afbeeldingen']:
        send_pictures("nederwoon.nl" + img)

def mainLoop():
    nieuweWoningen = getNieuweWoningen()
    for woning in nieuweWoningen:
        verstuurBericht(woning)
    time.sleep(20)

if __name__ == "__main__":
    mainLoop()


def send_notification(message: str):
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
