import { motion } from "framer-motion";
import { User } from "lucide-react";
import type { ChatEvent } from "../../types";

interface UserMessageProps {
  event: ChatEvent;
}

export function UserMessage({ event }: UserMessageProps) {
  const time = new Date(event.timestamp).toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex gap-3 px-4 py-2 justify-end"
    >
      <div className="max-w-[75%] flex flex-col items-end">
        <div className="flex items-baseline gap-2 mb-1">
          <span className="text-[10px] text-text-muted">{time}</span>
          <span className="text-sm font-semibold text-brand-purple">你</span>
        </div>
        <div className="bg-brand-purple/10 border border-brand-purple/15 rounded-[var(--radius-card)] rounded-tr-sm p-3 text-sm text-text-body leading-relaxed">
          {event.content}
        </div>
      </div>
      <div className="w-9 h-9 rounded-full bg-brand-purple/20 flex items-center justify-center shrink-0">
        <User size={16} className="text-brand-purple" />
      </div>
    </motion.div>
  );
}
