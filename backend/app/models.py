from typing import Any, Dict, Literal

from pydantic import BaseModel


class ContentState(BaseModel):
    job_id: str
    trend: Dict[str, Any]
    hook_script: str = ""
    video_prompt: str = ""
    video_url: str | None = None
    audio_url: str | None = None
    final_video_url: str | None = None
    virality_score: float | None = None  # 0-100
    x_post_id: str | None = None
    status: Literal["queued", "running", "reviewed", "posted", "failed"] = "queued"
