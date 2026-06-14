import os, json
import time
import requests, re
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN_ENV")
CHAT_ID = os.getenv("CHAT_ID")
NEDERWOON_URL = os.getenv("NEDERWOON_URL")
HEARTBEAT_URL = os.getenv("HEARTBEAT_URL")
SENT_FILE = "send.json"
BEZICHT_FILE = "bezicht.json"


def load_json_set(filepath: str) -> set:
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                content = f.read().strip()
                if not content:
                    return set()
                return set(json.loads(content))
        except json.JSONDecodeError:
            print(f"{filepath} corrupt, starting fresh")
            return set()
    return set()


def save_sent(sent_objects):
    with open(SENT_FILE, "w") as f:
        json.dump(list(sent_objects), f)

def save_sent_bezichtiging(sent_objects):
    with open(BEZICHT_FILE, "w") as f:
        json.dump(list(sent_objects), f)


def telegram_post(method: str, payload: dict):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    r = requests.post(url, data=payload, timeout=10)
    if r.status_code == 429:
        retry_after = r.json().get("parameters", {}).get("retry_after", 5)
        print(f"telegram rate limit, {retry_after}s wachten...", flush=True)
        time.sleep(retry_after)
        r = requests.post(url, data=payload, timeout=10)
    if not r.ok:
        raise RuntimeError(f"telegram {method} mislukt: {r.status_code} {r.text}")
    return r.json()


def send_notification(message: str):
    print("notificatie")
    return telegram_post("sendMessage", {"chat_id": CHAT_ID, "text": message})


def send_locations(lat: int, lon: int):
    telegram_post("sendLocation", {"chat_id": CHAT_ID, "latitude": lat, "longitude": lon})


def send_pictures(pic_url: str):
    telegram_post("sendPhoto", {"chat_id": CHAT_ID, "photo": pic_url})


def getNieuweWoningen(sent_objects, bezicht_objects):
    r = requests.get(NEDERWOON_URL, timeout=15)
    soup = BeautifulSoup(r.text, 'html.parser')

    woningen = []

    for loc in soup.select("div.location"):
        adres = loc.select_one("p.color-medium.fixed-lh")
        adres = adres.get_text(strip=True) if adres else None

        object_type = loc.select_one("p.color-primary.fixed-lh")
        object_type = object_type.get_text(strip=True) if object_type else None

        prijs_tag = loc.select_one("p.heading-md.text-regular.color-primary")
        if not prijs_tag:
            continue
        raw = prijs_tag.get_text(strip=True)
        prijs = re.sub(r"[^\d,€]", "", raw)

        afbeeldingen = [
            img.get("data-src") or img.get("src")
            for img in loc.select(".slider img")
            if img.get("data-src") or img.get("src")
        ]

        a_tag = loc.select_one("a[href]")
        if not a_tag:
            continue
        link = "nederwoon.nl" + a_tag["href"]

        cleaned = re.sub(r'[^\d,]', '', raw).replace(',', '.')
        try:
            prijs_num = float(cleaned)
        except ValueError:
            continue

        bezichtiging_tag = loc.select_one("p.color-tertiary")
        bezichtiging = not (
                bezichtiging_tag and
                "Er staat geen bezichtiging gepland" in bezichtiging_tag.get_text()
        )

        if prijs_num < 1001:
            woningen.append({
                "adres": adres,
                "type": object_type,
                "prijs": prijs,
                "afbeeldingen": afbeeldingen,
                "link": link,
                "bezichtiging": bezichtiging
            })

    nieuwe_woningen = [obj for obj in woningen if obj['link'] not in sent_objects]
    nieuwe_bezichtigingen = [obj for obj in woningen if obj['link'] not in bezicht_objects and obj['bezichtiging']]


    return nieuwe_woningen, nieuwe_bezichtigingen

def verstuurBezichtigingBericht(woning: dict):
    send_notification(
        f"LET OP!! Er is een bezichtiging ingepland!\n"
        f"Adres: {woning['adres']}\n"
        f"Type: {woning['type']}\n"
        f"Prijs: {woning['prijs']}\n"
        f"Link: {woning['link']}"
    )


def verstuurBericht(woning: dict):
    bezichtiging = "ja" if woning['bezichtiging'] else "nee"

    send_notification(
        f"LET OP!! Er is een nieuwe woning!\n"
        f"Adres: {woning['adres']}\n"
        f"Type: {woning['type']}\n"
        f"Prijs: {woning['prijs']}\n"
        f"Link: {woning['link']}\n"
        f"Bezichtiging gepland: {bezichtiging}"
    )


def verstuurFotos(woning: dict):
    for img in woning['afbeeldingen']:
        try:
            send_pictures(img)
        except Exception as e:
            print(f"foto versturen mislukt ({img}): {e}", flush=True)
        time.sleep(1)


def mainLoop():
    sent_objects = load_json_set(SENT_FILE)
    bezicht_objects = load_json_set(BEZICHT_FILE)

    while True:
        try:
            print("checking...", flush=True)
            nieuweWoningen, nieuweBezichtigingen = getNieuweWoningen(sent_objects, bezicht_objects)
            for woning in nieuweWoningen:
                print("woning gevonden, berichten worden verstuurd.....", flush=True)
                try:
                    verstuurBericht(woning)
                except Exception as e:
                    print(f"bericht versturen mislukt ({woning['link']}): {e}", flush=True)
                    continue
                sent_objects.add(woning['link'])
                save_sent(sent_objects)
                verstuurFotos(woning)
            for woning in nieuweBezichtigingen:
                print("bezichtiging gevonden, berichten worden verstuurd.....", flush=True)
                try:
                    verstuurBezichtigingBericht(woning)
                except Exception as e:
                    print(f"bezichtigingsbericht versturen mislukt ({woning['link']}): {e}", flush=True)
                    continue
                bezicht_objects.add(woning['link'])
                save_sent_bezichtiging(bezicht_objects)
            requests.get(HEARTBEAT_URL, timeout=10)
            print("heartbeat", flush=True)
            time.sleep(20)
        except Exception as e:
            print(f"error in loop: {e}", flush=True)
            time.sleep(60)


if __name__ == "__main__":
    mainLoop()