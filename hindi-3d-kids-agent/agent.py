#!/usr/bin/env python3
"""Create an original Hindi kids story package + copy/paste Google Flow prompts."""
import argparse
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def check_plan(plan):
    required = ("title", "topic", "characters", "description", "tags", "thumbnail_text", "scenes")
    for key in required:
        if not plan.get(key):
            raise ValueError("Missing or empty plan field: " + key)
    if not isinstance(plan["tags"], list) or not all(isinstance(x, str) for x in plan["tags"]):
        raise ValueError("tags must be a list of strings")
    scenes = plan["scenes"]
    if not isinstance(scenes, list) or len(scenes) != 5:
        raise ValueError("Expected exactly five scenes")
    if len(plan["title"]) > 100:
        raise ValueError("YouTube title must not exceed 100 characters")
    for i, scene in enumerate(scenes, 1):
        if scene.get("number") != i:
            raise ValueError("Scene numbering must be 1 through 5")
        for key in ("narration_hi", "visual_prompt"):
            if not isinstance(scene.get(key), str) or not scene[key].strip():
                raise ValueError("Scene %s missing %s" % (i, key))
        if scene.get("duration_seconds") != 8:
            raise ValueError("Scene %d duration must be exactly 8 seconds" % i)
    return plan


def create_with_gemini(topic, api_key, model):
    from google import genai

    prompt = (
        "You are a children's Hindi animated shorts producer. "
        "Create a completely original, fun, child-safe Hindi cartoon story for ages 3-8. "
        "Topic: " + topic + ". Make five visually sequential scenes, 8 seconds each, 40 seconds total. "
        "Spoken narration must be natural Hindi in Devanagari, short enough to fit about 8 seconds per scene. "
        "Scene visual_prompt must be detailed English directions for Google Flow/Veo "
        "for genuinely MOVING colorful 3D cartoon characters, no static slides. "
        "Use recurring ORIGINAL cartoon animal characters, keep exactly the same appearance and outfits in ALL scenes. "
        "Include cheerful expressions, movement, camera directions, colorful safe environments and a positive ending. "
        "Do not refer to existing copyrighted franchises, melodies or characters. "
        "No graphic violence, scary threats, dangerous behavior, inappropriate content or direct sales pitches to children. "
        "Return ONLY valid JSON in this schema: "
        "{title:string (under 100 characters, title can be Roman Hindi),topic:string,type:'kids_story',"
        "characters:string (fixed visual character bible),description:string (Hindi or Roman Hindi SEO),"
        "tags:string[],thumbnail_text:string (short uppercase Roman Hindi),"
        "scenes:[{number:1..5,duration_seconds:8,narration_hi:string,visual_prompt:string} x 5]}. "
        "Story must be logical and understandable, with clean grammar and no watermark instructions."
    )
    client = genai.Client(api_key=api_key)
    res = client.models.generate_content(
        model=model,
        contents=prompt,
        config={"response_mime_type": "application/json", "temperature": 0.65},
    )
    if not res.text:
        raise RuntimeError("Gemini gave an empty response")
    return check_plan(json.loads(res.text))


def make_flow_prompts(plan):
    blocks = [
        "# Google Flow: 3D Hindi Cartoon - Copy/Paste Prompts",
        "",
        "Generate FIVE vertical 9:16 clips. Each clip exactly ~8 seconds.",
        "IMPORTANT: Keep recurring characters consistent. Create/import character references in Flow first.",
        "Only original kid-safe 3D cartoon animation; NO captions, logos or on-screen text.",
        "Do NOT generate narration in Flow; separate Hindi voiceover will be synchronized later.",
        "Save the approved exports as scene_01.mp4 through scene_05.mp4.",
        "",
        "## Character reference",
        "",
        plan["characters"],
        "",
    ]
    for i, scene in enumerate(plan["scenes"], 1):
        blocks += [
            "## Scene %02d - scene_%02d.mp4" % (i, i),
            "",
            "Vertical 9:16, 8-second 3D animation for preschool children. "
            "Smooth real movement, consistent character identity and outfits. "
            "Characters: " + plan["characters"] + " "
            "Scene action: " + scene["visual_prompt"] + " "
            "No letters, subtitles, text overlays, logos or watermarks. "
            "No speech audio (Hindi narration added separately).",
            "",
            "Narration for timing: " + scene["narration_hi"],
            "",
        ]
    return "\n".join(blocks)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", default="Sher aur khargosh ki dosti", help="Hindi kids story topic")
    ap.add_argument("--output", default=str(ROOT / "work" / "episode_001"))
    ap.add_argument("--sample", action="store_true", help="Use sample episode, no API required")
    args = ap.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    if args.sample:
        plan = check_plan(json.loads((ROOT / "sample_episode.json").read_text(encoding="utf-8")))
    else:
        key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise SystemExit("GOOGLE_API_KEY missing. To test without API use --sample.")
        plan = create_with_gemini(args.topic, key, os.getenv("GEMINI_MODEL", "gemini-3.8-flash"))
    (output / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "flow_prompts.md").write_text(make_flow_prompts(plan) + "\n", encoding="utf-8")
    (output / "youtube_description.txt").write_text(plan["description"] + "\n", encoding="utf-8")
    print("SUCCESS: Storyboard ready at " + str(output))
    print("Next: Generate 5 3D Flow clips using flow_prompts.md; name scene_01.mp4 to scene_05.mp4.")


if __name__ == "__main__":
    main()
