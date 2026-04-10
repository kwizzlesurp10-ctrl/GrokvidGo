import asyncio
import json
import logging
import os

from xai_grok import GrokClient

from app.db import upsert_job
from app.models import ContentState

logger = logging.getLogger(__name__)

SCRIPT_SYSTEM = """\
You are an elite viral short-form video scriptwriter. Precision over creativity — every word must earn its place.

TASK
Given a trending topic, output exactly two fields:

1. hook_script — A 55–65 second spoken script (≈ 140–165 words).
   Structure:
   • Hook (0–5s): one of: shocking stat, contrarian claim, pattern-interrupt question, or bold prediction. \
Never open with "In this video", "Today we're going to", or any variant.
   • Value body (5–50s): tight, punchy delivery. One idea per sentence. No filler. Active voice only.
   • Close (50–65s): single clear CTA — follow, share, or reply. Tie back to the opening hook.

2. video_prompt — A cinematic visual generation prompt for Grok Imagine (aurora model).
   Format strictly: [subject], [action/state], [environment], [lighting], [camera angle], [visual style], [motion cue]
   Example: "Close-up of a hacker's fingers on a keyboard, green terminal glow, dark room, \
low-key side lighting, macro lens, cyberpunk aesthetic, subtle camera shake"

HARD CONSTRAINTS
- hook_script: plain spoken English only — no stage directions, no markdown, no emojis, no hashtags
- video_prompt: no identifiable faces, no brand logos, no readable text overlays
- Respond ONLY with strictly valid JSON: {"hook_script": "...", "video_prompt": "..."}
- Do NOT wrap output in markdown code blocks or add any preamble
- If the trend topic is ambiguous, write about the surrounding cultural moment instead\
"""


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
        parsed = json.loads(response.choices[0].message.content)
        state = state.model_copy(update={
            "hook_script": parsed["hook_script"],
            "video_prompt": parsed["video_prompt"],
        })
    except Exception as exc:
        logger.error("script_generator failed for job %s: %s", state.job_id, exc)
        state = state.model_copy(update={"status": "failed"})

    asyncio.run(upsert_job(state))
    return state
