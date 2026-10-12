# Hindi 3D Kids AI Agent - Hamza Dar YouTube

**Status: initial working-code setup, first end-to-end real Flow video test pending.** The old General Knowledge daily upload schedule was stopped separately. This project never publishes by default.

## Goal

Original **3D animated Hindi kids stories**, later poems/nursery rhymes. Use existing Gemini API key, ChatGPT Plus/Gemini subscription interfaces, Google Flow credits, GitHub Actions, FFmpeg and Hindi text-to-speech. Do not buy another VPS or subscription.

**Key limitation:** Google Flow generation/clip export is still handled inside the Flow app, with your existing credits. This repo DOES NOT have a supported Flow-credit API connection; it cannot silently create Google Flow video clips. It never pretends to animate stock images.

## Production pipeline

1. Story + five consistent-character 3D scene prompts from Google Gemini.
2. Copy prompts into Google Flow Agent, and generate five genuine MOVING 3D cartoon clips.
3. Download clips and name them scene_01.mp4, scene_02.mp4, scene_03.mp4, scene_04.mp4, scene_05.mp4.
4. Voice module generates Hindi Devanagari speech using edge-tts hi-IN-SwaraNeural; FFmpeg synchronizes the narration with the clips and overlays Hindi captions. Clips repeat (if needed) rather than cutting narration short.
5. Makes a vertical 1080x1920 Short, thumbnail.png, seo.json.
6. Upload to YouTube is OPTIONAL and PRIVATE by default, with Made for Kids set to true.

### A. First easy test - without extra paid tools (GitHub web UI)

1. Open **Actions > Hindi 3D Kids AI Agent (manual only) > Run workflow**.
2. Choose mode = prepare, sample = true. Click Run workflow.
3. Download its hindi-kids-prepare **Artifact** (at bottom of the completed run). It contains plan.json and flow_prompts.md.
4. Open [Google Flow](https://labs.google/fx/tools/flow). Use the exact character bible at the top of flow_prompts.md; create consistent character references. Paste the prompts one by one or work with Flow Agent. Set 9:16 aspect ratio. Review the result before spending more credits.
5. Export the best FIVE clips. Rename them as above.
6. For rendering, either use the local Windows option below or make a ZIP containing **plan.json plus all five scene_01.mp4..scene_05.mp4** (same exact plan.json used to make clips).
7. If using GitHub render mode, upload that ZIP to a place that provides a **public direct HTTPS download link**, e.g. a temporary URL on your existing Hostinger hosting. In GitHub Actions select mode = render, paste the exact clips_zip_url, upload_private = false. The workflow generates downloadable hindi_kids_short.mp4, thumbnail.png and seo.json under the **hindi-kids-render Artifact**.
8. Review the generated video. To upload, run render again with upload_private=true (requires existing CLIENT_SECRET_B64 and CREDENTIALS_B64 secrets). Confirm the uploaded video on YouTube Studio. If the OAuth token expired or YouTube API restricts privacy, the job may fail; do not assume publication.
9. Delete publicly accessible source ZIP when finished, to avoid unnecessarily leaving assets online. **Do not paste private tokens or passwords into a workflow URL input.**

### B. Real AI story instead of sample

Run workflow in prepare mode with **sample=false**, set topic. It uses the existing GOOGLE_API_KEY GitHub Actions secret and the Google model set in agent.py (GEMINI_MODEL env override supported locally). Its output artifact contains original plan.json, flow_prompts.md and youtube_description.txt. If Gemini quota/model is unavailable, the run fails rather than silently producing wrong content. Make changes to the Hindi lines/prompts before using credits.

### C. Local Windows rendering (no Hostinger ZIP needed)

Requirements: Windows Python 3.11+ installed and working **ffmpeg** plus **ffprobe** on PATH. The repo is standalone within the existing repository. From the repo root, in PowerShell or CMD:

    cd hindi-3d-kids-agent
    python -m pip install -r requirements.txt
    python agent.py --sample --output work/episode_001

Download/import 3D clips from Google Flow into a folder named clips:

    clips/scene_01.mp4
    clips/scene_02.mp4
    clips/scene_03.mp4
    clips/scene_04.mp4
    clips/scene_05.mp4

Then run:

    python producer.py --project work/episode_001/plan.json --clips clips --out output

Optional: add a music track you own the rights to, e.g. --music my_music.mp3 (music volume is kept low). Preview **output/hindi_kids_short.mp4**. English/Roman Hindi thumbnail text is generated from the first story; video Hindi captions use system fonts. FFmpeg build must support subtitles/libass.

To upload privately only after reviewing:

    python producer.py --project work/episode_001/plan.json --clips clips --out output --upload

To intentionally publish publicly (only after manual review):

    python producer.py --project work/episode_001/plan.json --clips clips --out output --upload --privacy public

YouTube API projects sometimes impose **private-only uploads** and may refuse custom thumbnails. A request to publish is NOT proof that YouTube actually shows a public video. Verify in YouTube Studio. Mark all clearly child-directed cartoons Made for Kids; this code does so when uploading.

### D. Free resources / important limits

* Gemini Pro and ChatGPT Plus app subscriptions **do not include unlimited paid developer API usage**. Existing GOOGLE_API_KEY may have its own free quota.
* Google Flow uses your **existing 1000 credits**, but charges per generation/model and can change pricing. Flow generation isn't automated by this repo.
* Edge TTS relies on Microsoft's web speech service and might change or be rate-limited. Confirm usage/commercial rights before monetization.
* Nursery rhyme **singing** needs a separate properly licensed music/voice workflow: spoken narration is NOT singing.
* The YouTube API/OAuth secrets must stay in GitHub Actions secrets, never in source code. Testing-mode refresh tokens can expire.
* Uploading a public ZIP to an existing website makes those clips downloadable until removed. Use local Windows rendering if you want to keep files private.
* YouTube kids content must comply with Made for Kids requirements and age-appropriate content policies.
* A human should review dialogue correctness, character consistency, copyright and audio/visual quality before publishing.

## Files

- agent.py - Gemini story & five Flow prompts generator
- sample_episode.json - Original safe Hindi sample story
- producer.py - Hindi TTS, animated MP4 compositor, captions, thumbnail
- youtube_upload.py - Optional YouTube upload, Made for Kids, private default
- download_clips.py - safe subset extract of a user-provided direct HTTPS ZIP
- .github/workflows/hindi-kids.yml - GitHub Actions manual prepare/render
- requirements.txt - free Python dependencies

## Next improvements

Once a real five-clip test succeeds: build reusable 3D character reference packs, optional scene-by-scene dubbing, stronger automated caption timing, 16:9 long form, copyright-safe original music, and quality review before YouTube upload.
