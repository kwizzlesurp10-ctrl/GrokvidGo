import asyncio
import logging
import os
import tempfile
import urllib.request

import tweepy

from app.db import upsert_job
from app.models import ContentState

logger = logging.getLogger(__name__)


def _get_client() -> tweepy.Client:
    return tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_SECRET"),
    )


def _get_api_v1() -> tweepy.API:
    auth = tweepy.OAuth1UserHandler(
        os.getenv("X_API_KEY"),
        os.getenv("X_API_SECRET"),
        os.getenv("X_ACCESS_TOKEN"),
        os.getenv("X_ACCESS_SECRET"),
    )
    return tweepy.API(auth)


def x_poster(state: ContentState) -> ContentState:
    """Upload final video to X and post tweet thread."""
    if state.status == "failed":
        return state

    try:
        api_v1 = _get_api_v1()
        client = _get_client()

        # Download final video to temp file for upload
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            urllib.request.urlretrieve(state.final_video_url, tmp.name)
            media = api_v1.media_upload(tmp.name, media_category="tweet_video")

        tweet_text = state.hook_script[:280]
        response = client.create_tweet(text=tweet_text, media_ids=[media.media_id])
        post_id = str(response.data["id"])

        state = state.model_copy(update={"x_post_id": post_id, "status": "posted"})
    except Exception as exc:
        logger.error("x_poster failed for job %s: %s", state.job_id, exc)
        state = state.model_copy(update={"status": "failed"})

    asyncio.run(upsert_job(state))
    return state
