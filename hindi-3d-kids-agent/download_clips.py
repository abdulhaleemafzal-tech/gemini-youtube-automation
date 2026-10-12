#!/usr/bin/env python3
"""Download a ZIP containing exactly one plan.json and five Flow clips."""
import argparse
from pathlib import Path
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import zipfile

MAX_BYTES = 200 * 1024 * 1024

def import_clips(url, folder):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("Need a public HTTPS direct ZIP download link.")
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    temporary = folder / "download.zip"
    response = urlopen(Request(url, headers={"User-Agent":"Kids3DAgent"}), timeout=90)
    total = 0
    with response, temporary.open("wb") as target:
        if urlparse(response.geturl()).scheme != "https":
            raise ValueError("Non-HTTPS redirect rejected")
        while True:
            part = response.read(1048576)
            if not part:
                break
            total += len(part)
            if total > MAX_BYTES:
                raise ValueError("ZIP is too large")
            target.write(part)
    found = set()
    with zipfile.ZipFile(temporary) as archive:
        if sum(info.file_size for info in archive.infolist()) > MAX_BYTES:
            raise ValueError("Extracted ZIP size exceeds 200MB")
        for info in archive.infolist():
            filename = Path(info.filename).name
            if filename != "plan.json" and not re.fullmatch(r"scene_0[1-5]\.mp4", filename):
                continue
            if filename in found:
                raise ValueError("Duplicate file: " + filename)
            with archive.open(info) as original, (folder / filename).open("wb") as target:
                while True:
                    data = original.read(1048576)
                    if not data:
                        break
                    target.write(data)
            found.add(filename)
    temporary.unlink(missing_ok=True)
    expected = {"plan.json"} | {"scene_%02d.mp4" % n for n in range(1, 6)}
    if found != expected:
        raise ValueError("Missing ZIP contents: " + ", ".join(sorted(expected - found)))
    print("Imported matching story and five Flow clips.")

if __name__ == "__main__":
    import os
    p = argparse.ArgumentParser()
    p.add_argument("--url", default=os.getenv("FLOW_CLIPS_ZIP_URL"))
    p.add_argument("--destination", default="hindi-3d-kids-agent/work/episode_001")
    args = p.parse_args()
    if not args.url:
        p.error("URL required")
    import_clips(args.url, args.destination)
