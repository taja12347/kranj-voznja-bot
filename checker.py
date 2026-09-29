import requests
from bs4 import BeautifulSoup
import re
import json
import os

WEBHOOK_URL = os.environ["WEBHOOK_URL"]

BASE_URL = "https://e-uprava.gov.si/si/javne-evidence/prosti-termini-zemljevid/content/singleton.html"

BASE_PARAMS = {
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

        params = BASE_PARAMS.copy()
        params["page"] = page

        try:
            response = requests.get(
                BASE_URL,
                params=params,
                timeout=20
            )

            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Poiščemo vrstice s podatki
            rows = soup.find_all("tr")

            for row in rows:

                cells = [
                    cell.get_text(" ", strip=True)
                    for cell in row.find_all(["td", "th"])
                ]

                if len(cells) < 5:
                    continue

                # Pričakujemo:
                # datum | ura | lokacija | kategorija | prosta mesta
                date = cells[0]
                time_value = cells[1]
                location = cells[2]
                category = cells[3]
                free_places = cells[4]

                # Samo Kranj + B
                if "KRANJ" not in location.upper():
                    continue

                if not re.search(r"\bB\b", category.upper()):
                    continue

                # Mora biti datum
                if not re.match(r"^\d{1,2}\.\s*\d{1,2}\.\s*\d{4}", date):
                    continue

                # Mora biti ura
                if not re.match(r"^\d{1,2}:\d{2}$", time_value):
                    continue

                term_id = (
                    f"{date}|{time_value}|"
                    f"{location}|{category}|{free_places}"
                )

                if term_id not in seen:
                    found.append({
                        "id": term_id,
                        "date": date,
                        "time": time_value,
                        "location": location,
                        "category": category,
                        "free_places": free_places,
                    })

                    seen.add(term_id)

        except Exception as e:
            print(f"Napaka pri strani {page}: {e}")

    return found


print("🚗 Kranj B checker zagnan.")

new_terms = check_terms()

for term in new_terms:

    message = (
        "🚨 **NOV TERMIN ZA GLAVNO VOŽNJO!**\n\n"
        f"📅 **Datum:** {term['date']}\n"
        f"🕐 **Ura:** {term['time']}\n"
        "📍 **Kranj**\n"
        f"🚗 **Kategorija:** {term['category']}\n"
        f"🟢 **Prosta mesta:** {term['free_places']}\n\n"
        "🔗 **Odpri eUpravo:**\n"
        "https://e-uprava.gov.si/si/javne-evidence/prosti-termini-zemljevid.html"
    )

    send_discord(message)

    print(
        "NOV TERMIN:",
        term["date"],
        term["time"],
        term["category"],
        term["free_places"]
    )


with open(SEEN_FILE, "w", encoding="utf-8") as f:
    json.dump(
        sorted(seen),
        f,
        ensure_ascii=False,
        indent=2
    )

print(f"Preverjanje končano. Novi termini: {len(new_terms)}")
