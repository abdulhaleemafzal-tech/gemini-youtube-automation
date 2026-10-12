#!/usr/bin/env python3
"""Turn five user-generated Google Flow clips into a Hindi-narrated 3D kids Short."""
import argparse
import asyncio
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import textwrap

from agent import check_plan


def run(args, cwd=None):
    print("RUN:", " ".join(str(x) for x in args[:5]), "...")
    subprocess.run([str(x) for x in args], cwd=cwd, check=True)


def duration_seconds(filename):
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(filename)],
        check=True, capture_output=True, text=True,
    )
    return float(p.stdout.strip())


def srt_time(seconds):
    milliseconds = int(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3600000)
    minutes, milliseconds = divmod(milliseconds, 60000)
    secs, milliseconds = divmod(milliseconds, 1000)
    return "%02d:%02d:%02d,%03d" % (hours, minutes, secs, milliseconds)


async def synthesize_scenes(plan, output, voice):
    import edge_tts
    for number, scene in enumerate(plan["scenes"], 1):
        path = output / ("voice_%02d.mp3" % number)
        for attempt in range(3):
            try:
                await edge_tts.Communicate(text=scene["narration_hi"], voice=voice).save(str(path))
                if path.stat().st_size == 0:
                    raise RuntimeError("Generated empty voice file")
                break
            except Exception:
                if attempt == 2:
                    raise
                await asyncio.sleep(3 * (attempt + 1))


def font_file():
    options = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    return next((x for x in options if Path(x).exists()), None)


def create_thumbnail(video, title, dest):
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance
    frame = dest.parent / "thumbnail_frame.png"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", "0.8",
         "-i", video, "-frames:v", "1", str(frame)])
    image = Image.open(frame).convert("RGB")
    w, h = image.size
    scale = max(1280 / w, 720 / h)
    image = image.resize((math.ceil(w * scale), math.ceil(h * scale)), Image.Resampling.LANCZOS)
    left = (image.width - 1280) // 2
    top = (image.height - 720) // 2
    image = image.crop((left, top, left + 1280, top + 720))
    image = ImageEnhance.Contrast(image).enhance(1.15)
    overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    ink = ImageDraw.Draw(overlay)
    ink.rounded_rectangle((50, 460, 1230, 681), radius=28, fill=(4, 26, 70, 210))
    ink.rounded_rectangle((62, 470, 438, 522), radius=18, fill=(245, 193, 25, 255))
    fontpath = font_file()
    small = ImageFont.truetype(fontpath, 29) if fontpath else ImageFont.load_default()
    big = ImageFont.truetype(fontpath, 75) if fontpath else ImageFont.load_default()
    ink.text((83, 475), "3D HINDI CARTOON", font=small, fill=(8, 20, 36, 255))
    lines = textwrap.wrap(title.upper(), width=27)[:2] or ["KIDS STORY"]
    for j, line in enumerate(lines):
        ink.text((72, 536 + j * 72), line, font=big, fill=(255, 255, 255, 255),
                 stroke_width=3, stroke_fill=(0, 0, 0, 255))
    Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB").save(dest, optimize=True)
    frame.unlink(missing_ok=True)


def produce(plan_path, clips_dir, output, voice, music=None):
    for binary in ("ffmpeg", "ffprobe"):
        if not shutil.which(binary):
            raise RuntimeError(binary + " must be installed and added to PATH")
    plan = check_plan(json.loads(Path(plan_path).read_text(encoding="utf-8")))
    clips = [Path(clips_dir).resolve() / ("scene_%02d.mp4" % n) for n in range(1, 6)]
    missing = [str(clip) for clip in clips if not clip.is_file() or clip.stat().st_size == 0]
    if missing:
        raise FileNotFoundError("Missing Google Flow 3D animated MP4 clips:\n" + "\n".join(missing))
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    asyncio.run(synthesize_scenes(plan, output, voice))
    segments = []
    for number, (scene, clip) in enumerate(zip(plan["scenes"], clips), 1):
        voice_path = output / ("voice_%02d.mp3" % number)
        length = max(float(scene["duration_seconds"]), duration_seconds(voice_path) + 0.35)
        captions = output / ("caption_%02d.srt" % number)
        captions.write_text(
            "1\n%s --> %s\n%s\n" % (
                srt_time(0.2), srt_time(length - 0.2), scene["narration_hi"]
            ), encoding="utf-8",
        )
        segment = output / ("segment_%02d.mp4" % number)
        style = "FontName=Noto Sans Devanagari,FontSize=19,PrimaryColour=&H00FFFFFF,OutlineColour=&H00404040,Outline=3,Shadow=1,Alignment=2,MarginV=160"
        filt = ("scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,fps=30,format=yuv420p,"
                "subtitles=caption_%02d.srt:force_style='%s'" % (number, style))
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-stream_loop", "-1", "-i", clip, "-i", voice_path,
             "-map", "0:v:0", "-map", "1:a:0",
             "-vf", filt, "-af", "apad",
             "-t", "%.3f" % length,
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "25",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
             "-ar", "44100", "-ac", "2", "-movflags", "+faststart", segment], cwd=output)
        segments.append(segment)
    concatlist = output / "concat.txt"
    concatlist.write_text("".join("file 'segment_%02d.mp4'\n" % n for n in range(1, 6)), encoding="utf-8")
    video = output / "hindi_kids_short.mp4"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "concat", "-safe", "0", "-i", str(concatlist),
         "-c", "copy", "-movflags", "+faststart", str(video)], cwd=output)
    if music:
        royalty_free = Path(music).resolve()
        if not royalty_free.is_file():
            raise FileNotFoundError("Music file not found: " + str(royalty_free))
        mixed = output / "music_mix.mp4"
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-i", video, "-stream_loop", "-1", "-i", royalty_free,
             "-filter_complex",
             "[0:a]volume=1[a];[1:a]volume=0.08[b];[a][b]amix=inputs=2:duration=first:dropout_transition=1[m]",
             "-map", "0:v:0", "-map", "[m]", "-c:v", "copy",
             "-c:a", "aac", "-b:a", "160k", "-shortest", str(mixed)])
        mixed.replace(video)
    thumbnail = output / "thumbnail.png"
    create_thumbnail(segments[2], plan["thumbnail_text"], thumbnail)
    (output / "seo.json").write_text(
        json.dumps({key: plan[key] for key in ("title", "description", "tags")},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("SUCCESS video:", video)
    print("SUCCESS thumbnail:", thumbnail)
    print("SUCCESS metadata:", output / "seo.json")
    print("Video is NOT uploaded automatically. Review before uploading.")
    return video, thumbnail, plan


def main():
    ap = argparse.ArgumentParser(description="5 Google Flow clips -> Hindi kid-safe Short")
    ap.add_argument("--project", default="work/episode_001/plan.json")
    ap.add_argument("--clips", default="clips")
    ap.add_argument("--out", default="output/kids")
    ap.add_argument("--voice", default="hi-IN-SwaraNeural")
    ap.add_argument("--music", help="Optional music file you have RIGHTS to use")
    ap.add_argument("--upload", action="store_true", help="Opt in to YouTube upload after review")
    ap.add_argument("--privacy", choices=["private", "unlisted", "public"], default="private")
    args = ap.parse_args()
    video, thumbnail, plan = produce(
        args.project, args.clips, args.out, args.voice, args.music
    )
    if args.upload:
        from youtube_upload import upload
        upload(video, thumbnail, plan, args.privacy)


if __name__ == "__main__":
    main()
