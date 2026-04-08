"use client";

import { useEffect, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  type Edge,
  type Node,
} from "reactflow";
import "reactflow/dist/style.css";

import { AgentNode, type AgentNodeData } from "@/components/AgentNode";
import { supabase } from "@/lib/supabase";

const nodeTypes = { agentNode: AgentNode };

// Static pipeline shape — positions arranged left-to-right
const PIPELINE_NODES: Array<{ id: string; label: string; x: number }> = [
  { id: "scan",    label: "TrendScanner",      x: 0   },
  { id: "script",  label: "ScriptGenerator",   x: 180 },
  { id: "video",   label: "VideoGenerator",    x: 360 },
  { id: "tts",     label: "AudioGenerator",    x: 540 },
  { id: "compose", label: "Composer",          x: 720 },
  { id: "review",  label: "ViralityReviewer",  x: 900 },
  { id: "post",    label: "XPoster",           x: 1080},
];

const STATIC_EDGES: Edge[] = [
  { id: "e1", source: "scan",    target: "script"  },
  { id: "e2", source: "script",  target: "video"   },
  { id: "e3", source: "video",   target: "tts"     },
  { id: "e4", source: "tts",     target: "compose" },
  { id: "e5", source: "compose", target: "review"  },
  { id: "e6", source: "review",  target: "post", label: "score ≥ threshold" },
];

type JobRow = {
  job_id: string;
  trend: object;
  hook_script: string;
  video_url: string | null;
  audio_url: string | null;
  final_video_url: string | null;
  virality_score: number | null;
  x_post_id: string | null;
  status: "queued" | "running" | "reviewed" | "posted" | "failed";
};

function jobToNodeStatus(job: JobRow | null, nodeId: string): AgentNodeData["status"] {
  if (!job) return "idle";
  if (job.status === "failed") {
    // Mark nodes up to where failure happened
    const order = PIPELINE_NODES.map((n) => n.id);
    const failIdx = order.indexOf(nodeId);
    if (job.video_url === null && failIdx >= 2) return "idle";
    return "failed";
  }
  const completedMap: Record<string, boolean> = {
    scan:    !!job.trend && Object.keys(job.trend).length > 0,
    script:  !!job.hook_script,
    video:   !!job.video_url,
    tts:     !!job.audio_url,
    compose: !!job.final_video_url,
    review:  job.virality_score !== null,
    post:    !!job.x_post_id,
  };
  if (completedMap[nodeId]) return "completed";
  if (job.status === "running") {
    const order = PIPELINE_NODES.map((n) => n.id);
    const lastDone = order.filter((id) => completedMap[id]).pop();
    const lastDoneIdx = lastDone ? order.indexOf(lastDone) : -1;
    if (order.indexOf(nodeId) === lastDoneIdx + 1) return "running";
  }
  return "idle";
}

export default function DashboardPage() {
  const [latestJob, setLatestJob] = useState<JobRow | null>(null);

  // Subscribe to Supabase Realtime for live updates
  useEffect(() => {
    const channel = supabase
      .channel("jobs-realtime")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "jobs" },
        (payload) => setLatestJob(payload.new as JobRow)
      )
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, []);

  const nodes: Node<AgentNodeData>[] = PIPELINE_NODES.map((n) => ({
    id: n.id,
    type: "agentNode",
    position: { x: n.x, y: 200 },
    data: {
      label: n.label,
      status: jobToNodeStatus(latestJob, n.id),
    },
  }));

  return (
    <div className="react-flow-wrapper">
      <ReactFlow nodes={nodes} edges={STATIC_EDGES} nodeTypes={nodeTypes} fitView>
        <Background />
        <Controls />
      </ReactFlow>

      {latestJob && (
        <div className="absolute bottom-4 left-4 rounded-xl border bg-white p-4 shadow-md text-sm max-w-xs">
          <div className="font-semibold mb-1">Latest Job</div>
          <div>ID: <span className="font-mono text-xs">{latestJob.job_id}</span></div>
          <div>Status: <span className="font-semibold">{latestJob.status}</span></div>
          {latestJob.virality_score !== null && (
            <div>Virality: <span className="font-semibold">{latestJob.virality_score}/100</span></div>
          )}
          {latestJob.x_post_id && (
            <a
              href={`https://x.com/i/web/status/${latestJob.x_post_id}`}
              target="_blank"
              rel="noreferrer"
              className="text-blue-600 underline mt-1 block"
            >
              View Post →
            </a>
          )}
        </div>
      )}
    </div>
  );
}
