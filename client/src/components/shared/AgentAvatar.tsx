import type { AgentId } from "../../types";
import { AGENT_META } from "../../types";

interface AgentAvatarProps {
  agentId: AgentId;
  size?: number;
}

export function AgentAvatar({ agentId, size = 36 }: AgentAvatarProps) {
  const meta = AGENT_META[agentId];
  return (
    <div
      className="rounded-full flex items-center justify-center text-white font-medium shrink-0"
      style={{
        width: size,
        height: size,
        background: `linear-gradient(135deg, ${meta.gradient[0]}, ${meta.gradient[1]})`,
        fontSize: size * 0.4,
      }}
    >
      {meta.emoji}
    </div>
  );
}
