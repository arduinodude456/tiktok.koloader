import json
import os
import subprocess
import random as r
from pathlib import Path

import requests
from internetarchive import upload

# ==========================================================
# Einstellungen
# ==========================================================

PEXELS_API_KEY = "HF7bMRFjADAiArFbahcgaNLUe2K4tmQGsxS0fxOGDW6qiElXp1fNNUAV"

ARCHIVE_ACCESS_KEY = "um2WW5X4LJXNVonC"
ARCHIVE_SECRET_KEY = "iZSXeThzw17GU1HQ"
begriffe=["tiny house","food","deco","tiny house"]
SUCHBEGRIFF = "tiny house"
ANZAHL = 500

WIDTH = 800
HEIGHT = 600
FPS = 10

DOWNLOADS = Path("videos")
OUTPUT = Path("output")
DATABASE = Path("processed.json")

DOWNLOADS.mkdir(exist_ok=True)
OUTPUT.mkdir(exist_ok=True)

HEADERS = {
    "Authorization": PEXELS_API_KEY
}

# ==========================================================
# Bereits verarbeitete Videos laden
# ==========================================================

if DATABASE.exists():
    processed = set(json.loads(DATABASE.read_text()))
else:
    processed = set()

# ==========================================================
# Pexels
# ==========================================================

def suche_videos(query, per_page):

    response = requests.get(
        "https://api.pexels.com/videos/search",
        headers=HEADERS,
        params={
            "query": query,
            "per_page": per_page
        }
    )

    response.raise_for_status()

    return response.json()["videos"]


def ist_916(width, height, toleranz=0.08):
    ratio = width / height
    return abs(ratio - (9 / 16)) <= toleranz


def lade_video(url, ziel):
    r = requests.get(url, stream=True)
    r.raise_for_status()

    with open(ziel, "wb") as f:
        for chunk in r.iter_content(1024 * 1024):
            if chunk:
                f.write(chunk)

# ==========================================================
# FFmpeg
# ==========================================================

def convert(input_file, output_file):

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_file),
        "-vf",
        f"scale={WIDTH}:{HEIGHT},fps={FPS},format=gray",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "gray",
        str(output_file)
    ]

    subprocess.run(cmd, check=True)
# ==========================================================
# Hauptprogramm
# ==========================================================

erfolgreich = 0

while erfolgreich < ANZAHL:

    suchbegriff = r.choice(begriffe)
    print(f"\nSuche nach: {suchbegriff}")

    try:
        videos = suche_videos(suchbegriff, 30)

    except Exception as e:
        print("Fehler bei der Suche:", e)
        continue


    if not videos:
        continue


    # zufälliges Video aus den Treffern wählen
    r.shuffle(videos)

    video = None
    passende_datei = None


    for kandidat in videos:

        filename_test = f'{kandidat["id"]}.mp4'

        # bereits verarbeitet überspringen
        if filename_test in processed:
            continue


        for file in kandidat["video_files"]:

            if ist_916(file["width"], file["height"]):

                video = kandidat
                passende_datei = file
                break


        if passende_datei:
            break


    if passende_datei is None:
        print("Kein neues 9:16 Video gefunden.")
        continue


    filename = f'{video["id"]}.mp4'


    mp4 = DOWNLOADS / filename

    print("Download:", filename)


    try:
        lade_video(
            passende_datei["link"],
            mp4
        )

    except Exception as e:
        print("Downloadfehler:", e)
        continue



    nummern = [
        int(f.stem)
        for f in OUTPUT.glob("*.raw")
        if f.stem.isdigit()
    ]


    nummer = max(nummern) + 1 if nummern else 1

    raw = OUTPUT / f"{nummer}.raw"

    identifier = f"koreader-{nummer}"


    print("Konvertiere:", raw.name)


    try:
        convert(mp4, raw)

    except Exception as e:
        print("FFmpeg Fehler:", e)
        continue



    print("Upload:", identifier)


    uploaded = False

    while not uploaded:

        try:

            upload(
                identifier,
                files=[str(raw)],
                metadata={
                    "title": str(video["id"]),
                    "creator": "KOReader TikTok Plugin",
                    "mediatype": "data",
                    "collection": "opensource",
                    "description": f"RAW grayscale animation - {suchbegriff}"
                },
                access_key=ARCHIVE_ACCESS_KEY,
                secret_key=ARCHIVE_SECRET_KEY
            )


            processed.add(filename)

            DATABASE.write_text(
                json.dumps(
                    sorted(processed),
                    indent=4
                )
            )


            uploaded = True
            erfolgreich += 1

            print(
                f"Fortschritt: {erfolgreich}/{ANZAHL}"
            )


        except Exception as e:

            print("Upload fehlgeschlagen:", e)


print("Fertig.")
