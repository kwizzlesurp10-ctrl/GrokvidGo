import os

from xai_grok import GrokClient

from app.db import upsert_job
from app.models import ContentState


def trend_scanner(state: ContentState) -> ContentState:
    """Fetch the hottest real-time trend via Grok / X API."""
    try:
        grok = GrokClient(api_key=os.getenv("GROK_API_KEY"))
        trends = grok.trends_real_time()
        state = state.model_copy(update={"trend": trends[0], "status": "running"})
    except Exception as exc:
        state = state.model_copy(update={"status": "failed", "trend": {"error": str(exc)}})

    import asyncio
    asyncio.run(upsert_job(state))
    return state
