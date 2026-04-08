from supabase import create_client

from app.config import settings
from app.models import ContentState

_client = None


def get_supabase():
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _client


async def upsert_job(state: ContentState) -> None:
    """Write full ContentState to the jobs table and trigger Realtime."""
    supabase = get_supabase()
    supabase.table("jobs").upsert(state.model_dump()).execute()


async def get_job_state(job_id: str) -> dict:
    supabase = get_supabase()
    result = supabase.table("jobs").select("*").eq("job_id", job_id).single().execute()
    return result.data
