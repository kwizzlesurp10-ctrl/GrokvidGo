# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**viralaether-swarm** is a fully automated viral video generation and posting pipeline. It uses a multi-agent architecture orchestrated by LangGraph to scan trends, generate scripts and media, and post content to X (Twitter). The repo is a **Turborepo monorepo** (`create-turbo` with shadcn) containing a Next.js frontend and a Python/FastAPI backend.

## Architecture

The pipeline is a LangGraph `StateGraph` with a Supervisor node that routes between specialized agents:

```
Supervisor (LangGraph StateGraph)
├── TrendScannerAgent   — fetches trending topics via Grok + X API
├── ScriptGeneratorAgent — generates video scripts using Grok LLM
├── VideoGeneratorAgent  — generates video via Grok Imagine + text overlay
├── AudioGeneratorAgent  — generates voiceover via ElevenLabs v3
├── ComposerAgent        — merges video + audio into final clip
├── ViralityReviewerAgent — scores and predicts virality using Grok
└── XPosterAgent         — uploads media and posts thread to X
```

The shared `StateGraph` state object flows through every agent node, accumulating outputs (trend data → script → video path → audio path → composed path → virality score → post result).

## Key Technology Choices

| Layer | Technology |
|---|---|
| Monorepo | Turborepo (`create-turbo --example with-shadcn`) |
| Frontend | Next.js + shadcn/ui |
| Backend API | FastAPI 0.115 |
| Orchestration | LangGraph 1.1.6 StateGraph |
| Task queue | Celery 5.4 + Redis 5 |
| Database / Storage | Supabase 2.8 (Postgres + object storage for asset URLs) |
| LLM / Vision | Grok (xAI API) — trend analysis, script gen, virality scoring, video generation |
| TTS | ElevenLabs v3 2.42 |
| Data validation | Pydantic 2.10 |

## Development Commands

```bash
# Start the full stack (backend, frontend, redis, supabase)
docker compose up

# Frontend only
cd apps/web && npm run dev

# Backend only (with venv active)
cd backend && uvicorn app.main:app --reload

# Run Celery worker
cd backend && celery -A app.tasks worker --loglevel=info

# Run tests
cd backend && pytest

# Lint (backend)
cd backend && ruff check .
```

## Environment Variables

The pipeline requires secrets for every external service. Expect a `.env` file (never committed):

| Variable | Service |
|---|---|
| `XAI_API_KEY` | Grok / xAI API |
| `ELEVENLABS_API_KEY` | ElevenLabs TTS |
| `X_API_KEY`, `X_API_SECRET` | X (Twitter) OAuth |
| `X_ACCESS_TOKEN`, `X_ACCESS_SECRET` | X (Twitter) OAuth |
| `X_BEARER_TOKEN` | X API v2 read access |

## Job State Contract

`ContentState` is the single Pydantic model that flows through every LangGraph node:

```python
class ContentState(BaseModel):
    job_id: str
    trend: Dict[str, Any]        # raw trend payload — set by TrendScannerAgent
    hook_script: str = ""        # hook-first script — set by ScriptGeneratorAgent
    video_prompt: str = ""       # image/video gen prompt — set by ScriptGeneratorAgent
    video_url: str | None = None        # Supabase storage URL — set by VideoGeneratorAgent
    audio_url: str | None = None        # Supabase storage URL — set by AudioGeneratorAgent
    final_video_url: str | None = None  # composed clip URL — set by ComposerAgent
    virality_score: float | None = None # 0–100 — set by ViralityReviewerAgent
    x_post_id: str | None = None        # post ID — set by XPosterAgent
    status: Literal["queued", "running", "reviewed", "posted", "failed"] = "queued"
```

**Node signature**: every LangGraph node is a plain function `def node_name(state: ContentState) -> ContentState`. Nodes mutate a copy of state and return it.

Key design decisions:
- Assets are stored at **Supabase object storage URLs**, not local paths. Agents upload before writing the URL back to state.
- `hook_script` and `video_prompt` are separate — the script agent produces both independently.
- `status` tracks the full job lifecycle; nodes set `"failed"` on error rather than raising, so the graph can terminate gracefully.

## Graph Flow

Node names as registered in the `StateGraph`:

```
START → scan → script → video → tts → compose → review
      → [conditional: virality_score >= threshold?] → post → END
                                                    ↘ END (discard)
```

```python
workflow = StateGraph(ContentState)
workflow.add_node("scan",    trend_scanner)
workflow.add_node("script",  script_generator)
workflow.add_node("video",   video_generator)   # Grok Imagine Quality mode
workflow.add_node("tts",     tts_generator)     # ElevenLabs v3
workflow.add_node("compose", composer)
workflow.add_node("review",  virality_reviewer)
workflow.add_node("post",    x_poster)
```

## Frontend

- **Framework**: Next.js 15+ App Router (`apps/web/`)
- **Dashboard**: `apps/web/app/dashboard/page.tsx` — live graph visualization of running jobs using **React Flow** with custom `AgentNode` components that reflect per-node status
- **Real-time**: Supabase Realtime subscriptions push `ContentState` status changes to the dashboard without polling
- Custom node type registered as `{ agentNode: AgentNode }` in React Flow

## API & Task Queue

`POST /jobs` is the single entry point. It generates a `job_id`, enqueues a Celery task, and returns immediately. The Celery worker runs the full LangGraph pipeline asynchronously.

```
Client → POST /jobs → FastAPI → celery.send_task("tasks.run_swarm", [job_id]) → Redis
                                                                               ↓
                                                              Celery worker: StateGraph.invoke()
```

- Broker: `redis://redis:6379/0`
- Celery task name: `tasks.run_swarm`
- FastAPI app: `backend/app/main.py`
