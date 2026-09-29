import requests
from bs4 import BeautifulSoup
import re
import time
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

seen = set()


def send_discord(message):
    requests.post(
        WEBHOOK_URL,
        json={"content": message},
        timeout=20
    )


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
                r'\d{1,2}\.\s*\d{1,2}\.?\s*2026',
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
                    seen.add(term)
                    found.append(term)

        except Exception as e:
            print("Napaka pri strani", page, ":", e)

    return found


print("🚗 Checker za Kranj B je zagnan!")
print("Preverjam vsakih 60 sekund...")


while True:

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

    if not new_terms:
        print("Ni novih terminov.")

    time.sleep(60)
