import json
import os
import subprocess
from pathlib import Path

from internetarchive import upload

WIDTH = 800
HEIGHT = 600
FPS = 10

VIDEOS = Path("videos")
OUTPUT = Path("output")
DATABASE = Path("processed.json")

ARCHIVE_ACCESS_KEY = os.environ["IA_ACCESS_KEY"]
ARCHIVE_SECRET_KEY = os.environ["IA_SECRET_KEY"]

OUTPUT.mkdir(exist_ok=True)

if DATABASE.exists():
    processed = set(json.loads(DATABASE.read_text()))
else:
    processed = set()


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


for video in VIDEOS.glob("*.mp4"):

    if video.name in processed:
        continue

    print("Konvertiere", video.name)

    raw = OUTPUT / (video.stem + ".raw")

    convert(video, raw)

    identifier = "koreader-" + video.stem.lower()

    print("Lade hoch:", identifier)

    upload(
        identifier,
        files=[str(raw)],
        metadata={
            "title": video.stem,
            "mediatype": "data",
            "collection": "opensource",
            "creator": "KOReader TikTok Plugin",
            "description": "RAW grayscale animation"
        },
        access_key=ARCHIVE_ACCESS_KEY,
        secret_key=ARCHIVE_SECRET_KEY
    )

    processed.add(video.name)

DATABASE.write_text(json.dumps(sorted(processed), indent=4))

print("Fertig.")
