import asyncio
import logging
import os

from elevenlabs import ElevenLabs
from elevenlabs.types import VoiceSettings

from app.db import upsert_job, get_supabase
from app.models import ContentState

logger = logging.getLogger(__name__)

VOICE_ID = "JBFqnCBsd6RMkjVDRTP6"  # Adam — swap as needed


def tts_generator(state: ContentState) -> ContentState:
    """Generate voiceover via ElevenLabs v3 and upload to Supabase storage."""
    if state.status == "failed":
        return state

    try:
        client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        audio_bytes = b"".join(
            client.text_to_speech.convert(
                voice_id=VOICE_ID,
                text=state.hook_script,
                model_id="eleven_multilingual_v3",
                voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.8),
                output_format="mp3_44100_128",
            )
        )

        supabase = get_supabase()
        path = f"{state.job_id}/audio.mp3"
        supabase.storage.from_("assets").upload(path, audio_bytes, {"content-type": "audio/mpeg"})
        audio_url = supabase.storage.from_("assets").get_public_url(path)

        state = state.model_copy(update={"audio_url": audio_url})
    except Exception as exc:
        logger.error("tts_generator failed for job %s: %s", state.job_id, exc)
        state = state.model_copy(update={"status": "failed"})

    asyncio.run(upsert_job(state))
    return state
