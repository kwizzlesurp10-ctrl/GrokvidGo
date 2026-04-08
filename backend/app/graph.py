from langgraph.graph import END, StateGraph

from app.agents.composer import composer
from app.agents.script_generator import script_generator
from app.agents.trend_scanner import trend_scanner
from app.agents.tts_generator import tts_generator
from app.agents.video_generator import video_generator
from app.agents.virality_reviewer import virality_reviewer
from app.agents.x_poster import x_poster
from app.config import settings
from app.models import ContentState


def _should_post(state: ContentState) -> str:
    if state.status == "failed":
        return END
    if state.virality_score is not None and state.virality_score >= settings.virality_threshold:
        return "post"
    return END


def build_graph() -> StateGraph:
    workflow = StateGraph(ContentState)

    workflow.add_node("scan", trend_scanner)
    workflow.add_node("script", script_generator)
    workflow.add_node("video", video_generator)
    workflow.add_node("tts", tts_generator)
    workflow.add_node("compose", composer)
    workflow.add_node("review", virality_reviewer)
    workflow.add_node("post", x_poster)

    workflow.set_entry_point("scan")
    workflow.add_edge("scan", "script")
    workflow.add_edge("script", "video")
    workflow.add_edge("video", "tts")
    workflow.add_edge("tts", "compose")
    workflow.add_edge("compose", "review")
    workflow.add_conditional_edges("review", _should_post, {"post": "post", END: END})
    workflow.add_edge("post", END)

    return workflow.compile()
