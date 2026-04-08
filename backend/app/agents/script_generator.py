import asyncio
import os

from xai_grok import GrokClient

from app.db import upsert_job
from app.models import ContentState

SCRIPT_SYSTEM = """You are a viral short-form video scriptwriter.
Given a trending topic, produce:
1. A hook_script: a punchy 60-second spoken script that opens with a pattern-interrupt hook.
2. A video_prompt: a cinematic image/video generation prompt describing the visuals.

Respond in JSON: {"hook_script": "...", "video_prompt": "..."}"""


def script_generator(state: ContentState) -> ContentState:
    if state.status == "failed":
        return state

    try:
        grok = GrokClient(api_key=os.getenv("GROK_API_KEY"))
        response = grok.chat.completions.create(
            model="grok-3",
            messages=[
                {"role": "system", "content": SCRIPT_SYSTEM},
                {"role": "user", "content": f"Trend: {state.trend}"},
            ],
            response_format={"type": "json_object"},
        )
        data = response.choices[0].message.content
        import json
        parsed = json.loads(data)
        state = state.model_copy(update={
            "hook_script": parsed["hook_script"],
            "video_prompt": parsed["video_prompt"],
        })
    except Exception as exc:
        state = state.model_copy(update={"status": "failed"})

    asyncio.run(upsert_job(state))
    return state
