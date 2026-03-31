// ── 配置类型（与 Python Pydantic 模型 1:1 映射） ──────

export interface ModelConnection {
  id: string;
  name: string;
  provider: "openai_compatible" | "anthropic";
  base_url: string;
  api_key: string;
  model: string;
  enabled: boolean;
}

export interface McpEntry {
  id: string;
  name: string | null;
  command: string | null;
  args: string[];
}

export interface SkillEntry {
  id: string;
  name: string | null;
  description: string | null;
  skill_dir: string;
  enabled: boolean;
  scope: "app" | "task";
}

export interface LlmSettings {
  default_model_connection_id: string | null;
  default_provider: "openai" | "anthropic";
  openai_api_key: string;
  anthropic_api_key: string;
  openai_model: string;
  anthropic_model: string;
}

// ── 任务类型 ──────────────────────────────────────────

export interface Task {
  id: string;
  name: string;
  path: string;
  modified_at: string;
  /** 前端本地状态，后端不持久化 */
  status?: "idle" | "running" | "paused" | "completed";
}

// ── Agent 对话流事件 ──────────────────────────────────

export type ChatEventType =
  | "phase_start"
  | "agent_thinking"
  | "agent_output"
  | "hitl_interrupt"
  | "user_response"
  | "phase_complete"
  | "task_complete"
  | "error";

export interface ChatEvent {
  type: ChatEventType;
  timestamp: string;
  phase?: string;
  agent?: AgentId;
  content?: string;
  metadata?: Record<string, unknown>;
}

// ── Agent 标识与视觉配置 ─────────────────────────────

export type AgentId =
  | "consultant"
  | "architect"
  | "hitl_blueprint"
  | "experts"
  | "reviewer";

export interface AgentMeta {
  label: string;
  emoji: string;
  gradient: [string, string];
  nameColor: string;
}

export const AGENT_META: Record<AgentId, AgentMeta> = {
  consultant: {
    label: "Consultant",
    emoji: "\u{1F50D}",
    gradient: ["#8b5cf6", "#6366f1"],
    nameColor: "#c4b5fd",
  },
  architect: {
    label: "Architect",
    emoji: "\u{1F4D0}",
    gradient: ["#3b82f6", "#06b6d4"],
    nameColor: "#93c5fd",
  },
  hitl_blueprint: {
    label: "HITL Blueprint",
    emoji: "\u23F8",
    gradient: ["#f59e0b", "#f97316"],
    nameColor: "#fcd34d",
  },
  experts: {
    label: "Expert (Swarm)",
    emoji: "\u26A1",
    gradient: ["#22c55e", "#10b981"],
    nameColor: "#86efac",
  },
  reviewer: {
    label: "Reviewer",
    emoji: "\u{1F50E}",
    gradient: ["#ec4899", "#f43f5e"],
    nameColor: "#f9a8d4",
  },
};

/** 五阶段工作流有序列表 */
export const WORKFLOW_PHASES: AgentId[] = [
  "consultant",
  "architect",
  "hitl_blueprint",
  "experts",
  "reviewer",
];
