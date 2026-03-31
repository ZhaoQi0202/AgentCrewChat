import { motion } from "framer-motion";
import type { ChatEvent } from "../../types";
import { AGENT_META, type AgentId } from "../../types";

interface SystemMessageProps {
  event: ChatEvent;
}

export function SystemMessage({ event }: SystemMessageProps) {
  let text = "";
  if (event.type === "phase_start") {
    const meta = event.agent ? AGENT_META[event.agent as AgentId] : null;
    const label = meta ? `${meta.emoji} ${meta.label}` : event.phase;
    text = `\u2192 阶段: ${label}`;
  } else if (event.type === "phase_complete") {
    text = event.content || "阶段完成";
  } else if (event.type === "task_complete") {
    text = event.content || "任务完成";
  } else {
    text = event.content || "";
  }

  const isComplete = event.type === "task_complete";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex justify-center my-3"
    >
      <span
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs
          ${isComplete
            ? "bg-status-success/10 text-status-success border border-status-success/20"
            : "bg-bg-elevated text-text-muted border border-border-subtle"
          }`}
      >
        {text}
      </span>
    </motion.div>
  );
}
