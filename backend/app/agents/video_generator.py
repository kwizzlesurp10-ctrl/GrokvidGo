import asyncio
import os

from xai_grok import GrokClient

from app.db import upsert_job, get_supabase
from app.models import ContentState


def video_generator(state: ContentState) -> ContentState:
    """Generate video via Grok Imagine (Quality mode) and upload to Supabase storage."""
    if state.status == "failed":
        return state

    try:
        grok = GrokClient(api_key=os.getenv("GROK_API_KEY"))
        response = grok.images.generate(
            model="aurora",
            prompt=state.video_prompt,
            quality="high",
            n=1,
        )
        video_bytes = response.data[0].bytes  # adjust per SDK

        supabase = get_supabase()
        path = f"{state.job_id}/video.mp4"
        supabase.storage.from_("assets").upload(path, video_bytes, {"content-type": "video/mp4"})
        video_url = supabase.storage.from_("assets").get_public_url(path)

        state = state.model_copy(update={"video_url": video_url})
    except Exception as exc:
        state = state.model_copy(update={"status": "failed"})

    asyncio.run(upsert_job(state))
    return state
