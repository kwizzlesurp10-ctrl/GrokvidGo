"use client";

import { Handle, Position, type NodeProps } from "reactflow";

export type AgentNodeData = {
  label: string;
  status: "idle" | "running" | "completed" | "failed";
};

const STATUS_STYLES: Record<AgentNodeData["status"], string> = {
  idle: "border-gray-300 bg-white text-gray-600",
  running: "border-blue-400 bg-blue-50 text-blue-700 animate-pulse",
  completed: "border-green-400 bg-green-50 text-green-700",
  failed: "border-red-400 bg-red-50 text-red-700",
};

const STATUS_LABEL: Record<AgentNodeData["status"], string> = {
  idle: "idle",
  running: "running...",
  completed: "done",
  failed: "failed",
};

export function AgentNode({ data }: NodeProps<AgentNodeData>) {
  return (
    <div className={`rounded-xl border-2 px-4 py-3 shadow-sm min-w-[140px] ${STATUS_STYLES[data.status]}`}>
      <Handle type="target" position={Position.Left} />
      <div className="text-sm font-semibold">{data.label}</div>
      <div className="text-xs mt-1 opacity-70">{STATUS_LABEL[data.status]}</div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
