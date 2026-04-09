import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import type { ChatEvent, AgentId } from "../../types";
import { AGENT_META } from "../../types";
import { AgentAvatar } from "../shared/AgentAvatar";
import { useChatStore } from "../../stores/chatStore";

interface AgentMessageProps {
  event: ChatEvent;
}

export function AgentMessage({ event }: AgentMessageProps) {
  const agentId = (event.agent || "consultant") as AgentId;
  const meta = AGENT_META[agentId];
  const dynamicName = event.agent_name || (event.metadata?.agent_name as string | undefined);
  const isToolCall = event.metadata?.tool_call === true;
  const isThinking = event.type === "agent_thinking";

  const displayName = dynamicName || meta?.label || agentId;
  const displayEmoji = dynamicName ? "\u26A1" : meta?.emoji || "\u{1F916}";
  const displayColor = event.agent_color || meta?.color || meta?.nameColor || "#16a34a";

  const time = new Date(event.timestamp).toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  });

  // 动态头像：使用 executor 主题色
  const avatarColor = event.agent_color || meta?.gradient?.[0];

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex gap-3 px-4 py-2 max-w-[85%]"
    >
      {meta ? (
        <AgentAvatar agentId={agentId} size={36} />
      ) : (
        <div
          className="rounded-full flex items-center justify-center text-white font-medium shrink-0"
          style={{
            width: 36,
            height: 36,
            background: `linear-gradient(135deg, ${avatarColor || "#22c55e"}, ${avatarColor || "#10b981"})`,
            fontSize: 14,
          }}
        >
          {displayEmoji}
        </div>
      )}
      <div className="min-w-0 flex-1">
        {/* 头部：Agent 名称 + 时间 */}
        <div className="flex items-baseline gap-2 mb-1">
          <span className="text-sm font-semibold" style={{ color: displayColor }}>
            {displayEmoji} {displayName}
          </span>
          <span className="text-[10px] text-text-muted">{time}</span>
        </div>

        {/* 消息气泡 */}
        <div className={`backdrop-blur-sm border shadow-sm rounded-tl-sm p-3 text-sm leading-relaxed ${
          isToolCall
            ? "bg-amber-50/80 border-amber-200/50 text-amber-900 font-mono text-xs"
            : "bg-white/80 border-black/5 text-text-body"
        }`}>
          {isThinking ? (
            <ThinkingDots />
          ) : (
            <div className="prose prose-sm max-w-none [&>p]:my-1 [&>ul]:my-1 [&>ol]:my-1 overflow-x-auto break-words [&>pre]:max-w-full [&>pre]:overflow-x-auto">
              <AtMentionContent content={event.content || ""} />
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

/** 将消息中的 @名称 用对应 Agent 主题色高亮渲染 */
function AtMentionContent({ content }: { content: string }) {
  const events = useChatStore((s) => s.events);
  const pendingEvents = useChatStore((s) => s.pendingEvents);
  const allEvents = [...pendingEvents, ...events];

  // 收集已知名称 → 颜色映射
  const nameColorMap = new Map<string, string>();
  for (const meta of Object.values(AGENT_META)) {
    if (!nameColorMap.has(meta.label)) {
      nameColorMap.set(meta.label, meta.color);
    }
  }
  for (const e of allEvents) {
    if (e.agent_name && e.agent_color && !nameColorMap.has(e.agent_name)) {
      nameColorMap.set(e.agent_name, e.agent_color);
    }
  }

  const names = [...nameColorMap.keys()].sort((a, b) => b.length - a.length);
  if (names.length === 0) {
    return <ReactMarkdown>{content}</ReactMarkdown>;
  }

  // 用 @名称 分割内容
  const escaped = names.map((n) => n.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const pattern = new RegExp(`@(${escaped.join("|")})`, "g");
  const segments: { type: "text" | "mention"; value: string }[] = [];
  let lastIdx = 0;
  let m: RegExpExecArray | null;
  while ((m = pattern.exec(content)) !== null) {
    if (m.index > lastIdx) {
      segments.push({ type: "text", value: content.slice(lastIdx, m.index) });
    }
    segments.push({ type: "mention", value: m[1] });
    lastIdx = m.index + m[0].length;
  }
  if (lastIdx < content.length) {
    segments.push({ type: "text", value: content.slice(lastIdx) });
  }

  if (segments.length === 0) {
    return <ReactMarkdown>{content}</ReactMarkdown>;
  }

  return (
    <>
      {segments.map((seg, i) =>
        seg.type === "mention" ? (
          <span
            key={i}
            style={{
              color: nameColorMap.get(seg.value) || "#16a34a",
              fontWeight: 600,
            }}
          >
            @{seg.value}
          </span>
        ) : (
          <ReactMarkdown key={i}>{seg.value}</ReactMarkdown>
        )
      )}
    </>
  );
}

function ThinkingDots() {
  return (
    <div className="flex items-center gap-1 py-1">
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="w-2 h-2 rounded-full bg-text-muted"
          animate={{ opacity: [0.3, 1, 0.3] }}
          transition={{
            duration: 1.2,
            repeat: Infinity,
            delay: i * 0.2,
          }}
        />
      ))}
    </div>
  );
}
