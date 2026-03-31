import { motion } from "framer-motion";
import { Pause } from "lucide-react";
import type { ChatEvent } from "../../types";

interface HITLCardProps {
  event: ChatEvent;
}

export function HITLCard({ event }: HITLCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      className="mx-4 my-3"
    >
      <div className="border border-status-warning/30 bg-status-warning/5 rounded-[var(--radius-card)] p-4 backdrop-blur-sm">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-7 h-7 rounded-full bg-status-warning/20 flex items-center justify-center">
            <Pause size={14} className="text-status-warning" />
          </div>
          <span className="text-sm font-semibold text-status-warning">
            需要人工审核
          </span>
        </div>
        <p className="text-sm text-text-body leading-relaxed ml-9">
          {event.content || "图谱执行已暂停，等待你的输入后继续。"}
        </p>
        <p className="text-[11px] text-text-muted mt-2 ml-9">
          请在下方输入框中回复以继续执行
        </p>
      </div>
    </motion.div>
  );
}
