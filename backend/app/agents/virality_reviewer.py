import asyncio
import json
import logging
import os

from xai_grok import GrokClient

from app.db import upsert_job
from app.models import ContentState

logger = logging.getLogger(__name__)

REVIEW_SYSTEM = """\
You are a hard-nosed viral content analyst. Your predictions are calibrated against real engagement data — not hype.

TASK
Score a short-form video script against its source trend on a 0–100 virality scale for X (Twitter/TikTok crossover audience).

SCORING RUBRIC — score each dimension 0–20, then sum for the total:

1. Hook Strength (0–20)
   Does the first sentence make stopping mandatory?
   18–20 = instant pattern interrupt or visceral shock. 10–17 = decent, earns attention. <10 = weak open.

2. Trend Fit (0–20)
   How directly does the script ride the trend wave?
   18–20 = trend is the spine of the script. 10–17 = clearly connected. <10 = trend is window dressing.

3. Shareability (0–20)
   Would someone RT or screenshot this without watching the full video?
   18–20 = quotable take or hot opinion. 10–17 = shareable with context. <10 = forgettable.

4. Emotional Charge (0–20)
   Does it trigger a strong feeling — awe, anger, FOMO, laughter, or disbelief?
   18–20 = visceral reaction. 10–17 = mild engagement. <10 = flat/neutral.

5. Novelty / Angle (0–20)
   Is this a fresh take or the tenth version of the same content?
   18–20 = genuinely unique angle. 10–17 = slight twist on familiar. <10 = derivative.

OUTPUT FORMAT
Respond ONLY with strictly valid JSON — no markdown, no preamble, no trailing text:
{
  "score": <float 0–100, sum of subscores>,
  "subscores": {
    "hook": <int 0–20>,
    "trend_fit": <int 0–20>,
    "shareability": <int 0–20>,
    "emotion": <int 0–20>,
    "novelty": <int 0–20>
  },
  "reasoning": "<one tight sentence, max 120 characters>"
}\
"""


def virality_reviewer(state: ContentState) -> ContentState:
    if state.status == "failed":
        return state

    try:
        grok = GrokClient(api_key=os.getenv("GROK_API_KEY"))
        response = grok.chat.completions.create(
            model="grok-3",
            messages=[
                {"role": "system", "content": REVIEW_SYSTEM},
                {"role": "user", "content": json.dumps({
                    "trend": state.trend,
                    "hook_script": state.hook_script,
                })},
            ],
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)
        state = state.model_copy(update={
            "virality_score": float(data["score"]),
            "status": "reviewed",
        })
    except Exception as exc:
        logger.error("virality_reviewer failed for job %s: %s", state.job_id, exc)
        state = state.model_copy(update={"status": "failed"})

    asyncio.run(upsert_job(state))
    return state
