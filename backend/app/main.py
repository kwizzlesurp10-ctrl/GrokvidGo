import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.tasks import celery_app, run_swarm

app = FastAPI(title="ViralAether Swarm API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/jobs", status_code=202)
async def create_job():
    job_id = str(uuid.uuid4())
    celery_app.send_task("tasks.run_swarm", args=[job_id])
    return {"job_id": job_id, "status": "queued"}


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    from app.db import get_job_state
    return await get_job_state(job_id)


@app.get("/health")
async def health():
    return {"status": "ok"}
