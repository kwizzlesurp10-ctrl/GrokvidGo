from celery import Celery

from app.config import settings

celery_app = Celery("tasks", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"


@celery_app.task(name="tasks.run_swarm")
def run_swarm(job_id: str) -> dict:
    import asyncio

    from app.graph import build_graph
    from app.models import ContentState

    state = ContentState(job_id=job_id, trend={}, status="running")
    graph = build_graph()
    result = graph.invoke(state)
    return result.model_dump() if hasattr(result, "model_dump") else result
