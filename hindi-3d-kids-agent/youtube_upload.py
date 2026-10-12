"""Optional manual YouTube upload. Correctly marks original kids' cartoons Made for Kids."""
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPE = ["https://www.googleapis.com/auth/youtube.upload"]


def authenticated_youtube():
    # Local credentials work from the repository root; GitHub Actions may restore them via secrets.
    credfile = Path(os.getenv("YOUTUBE_CREDENTIALS_PATH", "credentials.json"))
    clientfile = Path(os.getenv("YOUTUBE_CLIENT_SECRETS_PATH", "client_secrets.json"))
    credentials = None
    if credfile.is_file():
        credentials = Credentials.from_authorized_user_file(str(credfile), scopes=SCOPE)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            if not clientfile.is_file():
                raise FileNotFoundError(
                    "YouTube OAuth credentials missing: obtain and authorize locally first."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(clientfile), SCOPE)
            credentials = flow.run_local_server(port=0)
        credfile.write_text(credentials.to_json(), encoding="utf-8")
    return build("youtube", "v3", credentials=credentials)


def upload(video, thumbnail, plan, privacy="private"):
    if privacy not in ("private", "unlisted", "public"):
        raise ValueError("Invalid privacy")
    if len(plan["title"]) > 100:
        raise ValueError("Title too long")
    yt = authenticated_youtube()
    body = {
        "snippet": {
            "title": plan["title"],
            "description": plan["description"],
            "tags": plan["tags"],
            "categoryId": "1",
            "defaultLanguage": "hi",
            "defaultAudioLanguage": "hi",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": True,
        },
    }
    request = yt.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(str(video), chunksize=-1, resumable=True),
    )
    response = None
    while response is None:
        progress, response = request.next_chunk()
        if progress:
            print("Upload progress %d%%" % (progress.progress() * 100))
    vid = response["id"]
    print("Uploaded (requested privacy=%s): https://www.youtube.com/watch?v=%s" % (privacy, vid))
    print("Confirm actual visibility in YouTube Studio; API restrictions may override it.")
    if Path(thumbnail).is_file():
        try:
            yt.thumbnails().set(
                videoId=vid, media_body=MediaFileUpload(str(thumbnail))
            ).execute()
            print("Custom thumbnail uploaded.")
        except Exception as exc:
            print("Thumbnail API permission/Shorts support limitation:", exc)
    print("Remember to verify made-for-kids designation and thumbnail selection in YouTube Studio.")
    return vid
