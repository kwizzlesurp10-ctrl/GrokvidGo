import asyncio
import logging
import subprocess
import tempfile
import urllib.request

from app.db import upsert_job, get_supabase
from app.models import ContentState

logger = logging.getLogger(__name__)


def composer(state: ContentState) -> ContentState:
    """Download video + audio from Supabase, merge with FFmpeg, re-upload final clip."""
    if state.status == "failed":
        return state

    try:
        with tempfile.TemporaryDirectory() as tmp:
            video_path = f"{tmp}/video.mp4"
            audio_path = f"{tmp}/audio.mp3"
            output_path = f"{tmp}/final.mp4"

            urllib.request.urlretrieve(state.video_url, video_path)
            urllib.request.urlretrieve(state.audio_url, audio_path)

            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", video_path,
                    "-i", audio_path,
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-shortest",
                    output_path,
                ],
                check=True,
                capture_output=True,
            )

            with open(output_path, "rb") as f:
                final_bytes = f.read()

        supabase = get_supabase()
        path = f"{state.job_id}/final.mp4"
        supabase.storage.from_("assets").upload(path, final_bytes, {"content-type": "video/mp4"})
        final_url = supabase.storage.from_("assets").get_public_url(path)

        state = state.model_copy(update={"final_video_url": final_url})
    except Exception as exc:
        logger.error("composer failed for job %s: %s", state.job_id, exc)
        state = state.model_copy(update={"status": "failed"})

    asyncio.run(upsert_job(state))
    return state
