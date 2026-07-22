import os
import requests

# ==========================
# Einstellungen
# ==========================
API_KEY = "DEIN_PEXELS_API_KEY"
SUCHBEGRIFF = "nature"
ANZAHL = 5
DOWNLOAD_ORDNER = "downloads"

os.makedirs(DOWNLOAD_ORDNER, exist_ok=True)

HEADERS = {
    "Authorization": API_KEY
}


def suche_videos(query, per_page=5):
    url = "https://api.pexels.com/videos/search"

    params = {
        "query": query,
        "per_page": per_page
    }

    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()

    return response.json()["videos"]


def ist_916(width, height, toleranz=0.08):
    ratio = width / height
    ziel = 9 / 16
    return abs(ratio - ziel) <= toleranz


def lade_video(video_url, dateiname):
    r = requests.get(video_url, stream=True)
    r.raise_for_status()

    with open(dateiname, "wb") as f:
        for chunk in r.iter_content(1024 * 1024):
            if chunk:
                f.write(chunk)


videos = suche_videos(SUCHBEGRIFF, ANZAHL)

gefunden = False

for video in videos:

    passende_datei = None

    # Suche nach einer Videodatei im 9:16-Format
    for file in video["video_files"]:
        w = file["width"]
        h = file["height"]

        if ist_916(w, h):
            passende_datei = file
            break

    if passende_datei:
        url = passende_datei["link"]

        ausgabe = os.path.join(
            DOWNLOAD_ORDNER,
            f'{video["id"]}.mp4'
        )

        print("Lade herunter:", ausgabe)
        lade_video(url, ausgabe)
        gefunden = True

if not gefunden:
    print("Keine 9:16-Videos gefunden.")
