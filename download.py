import json
import os
import subprocess
from pathlib import Path

import requests
from internetarchive import upload

# ==========================================================
# Einstellungen
# ==========================================================

PEXELS_API_KEY = "HF7bMRFjADAiArFbahcgaNLUe2K4tmQGsxS0fxOGDW6qiElXp1fNNUAV"

ARCHIVE_ACCESS_KEY = "um2WW5X4LJXNVonC"
ARCHIVE_SECRET_KEY = "iZSXeThzw17GU1HQ"

SUCHBEGRIFF = "nature"
ANZAHL = 5

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

videos = suche_videos(SUCHBEGRIFF, ANZAHL)

for video in videos:

    filename = f'{video["id"]}.mp4'

    if filename in processed:
        print(filename, "bereits verarbeitet.")
        continue

    passende_datei = None

    for file in video["video_files"]:

        if ist_916(file["width"], file["height"]):
            passende_datei = file
            break

    if passende_datei is None:
        print("Kein 9:16-Video:", video["id"])
        continue

    mp4 = DOWNLOADS / filename

    print("Download:", filename)

    lade_video(
        passende_datei["link"],
        mp4
    )

    # nächste freie Nummer finden
    nummern = [
        int(f.stem)
        for f in OUTPUT.glob("*.raw")
        if f.stem.isdigit()
    ]
    
    if nummern:
        nummer = max(nummern) + 1
    else:
        nummer = 1
    
    raw = OUTPUT / f"{nummer}.raw"
    
    identifier = f"koreader-{nummer}"

    print("Konvertiere:", raw.name)

    convert(mp4, raw)

  

    print("Upload:", identifier)

    upload(
        identifier,
        files=[str(raw)],
        metadata={
            "title": str(video["id"]),
            "creator": "KOReader TikTok Plugin",
            "mediatype": "data",
            "collection": "opensource",
            "description": "RAW grayscale animation"
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

print("Fertig.")
