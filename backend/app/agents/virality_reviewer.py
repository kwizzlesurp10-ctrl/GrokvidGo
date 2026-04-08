import asyncio
import json
import os

from xai_grok import GrokClient

from app.db import upsert_job
from app.models import ContentState

REVIEW_SYSTEM = """You are a viral content analyst specializing in X (Twitter) short-form video.
Score the following script and trend on a 0-100 virality scale.
Consider: emotional hook strength, trend relevance, shareability, controversy potential.
Respond in JSON: {"score": <float>, "reasoning": "<one sentence>"}"""


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
        state = state.model_copy(update={"status": "failed"})

    asyncio.run(upsert_job(state))
    return state
