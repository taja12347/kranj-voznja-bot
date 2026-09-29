import requests
from bs4 import BeautifulSoup
import re
import json
import os

WEBHOOK_URL = os.environ["WEBHOOK_URL"]

BASE_URL = "https://e-uprava.gov.si/si/javne-evidence/prosti-termini-zemljevid/content/singleton.html"

params = {
    "lang": "si",
    "type": "1",
    "cat": "6",
    "izpitniCenter": "18",
    "lokacija": "223",
    "offset": "0",
    "sentinel_type": "ok",
    "sentinel_status": "ok",
    "is_ajax": "1",
    "complete": "false",
}

SEEN_FILE = "seen_terms.json"

if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        seen = set(json.load(f))
else:
    seen = set()


def send_discord(message):
    response = requests.post(
        WEBHOOK_URL,
        json={"content": message},
        timeout=20
    )
    response.raise_for_status()


def check_terms():
    found = []

    for page in range(1, 14):

        params["page"] = page

        try:
            response = requests.get(
                BASE_URL,
                params=params,
                timeout=20
            )

            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(" ", strip=True)

            if "KRANJ" not in text.upper():
                continue

            dates = re.findall(
                r'\d{1,2}\.\s*\d{1,2}\.?\s*20\d{2}',
                text
            )

            times = re.findall(
                r'\b\d{1,2}[.:]\d{2}\b',
                text
            )

            if dates and times:

                date = dates[0]
                time_value = times[0]

                term = f"{date} {time_value}"

                if term not in seen:
                    found.append(term)
                    seen.add(term)

        except Exception as e:
            print(f"Napaka pri strani {page}: {e}")

    return found


print("🚗 Kranj B checker zagnan.")

new_terms = check_terms()

for term in new_terms:

    parts = term.split()

    message = (
        "🚨 NOV TERMIN ZA GLAVNO VOŽNJO!\n\n"
        f"📅 Datum: {parts[0]} {parts[1]} {parts[2]}\n"
        f"🕐 Ura: {parts[3]}\n"
        "📍 Kranj\n"
        "🚗 Kategorija: B\n\n"
        "🔗 Odpri eUpravo:\n"
        "https://e-uprava.gov.si/si/javne-evidence/prosti-termini-zemljevid.html"
    )

    send_discord(message)
    print("NOV TERMIN:", term)


with open(SEEN_FILE, "w", encoding="utf-8") as f:
    json.dump(sorted(seen), f, ensure_ascii=False, indent=2)

print(f"Preverjanje končano. Najdenih novih terminov: {len(new_terms)}")
