type Status = "running" | "paused" | "completed" | "idle" | "waiting" | "error";

const STATUS_CONFIG: Record<Status, { label: string; dotClass: string; bgClass: string }> = {
  running:   { label: "运行中", dotClass: "bg-status-success", bgClass: "bg-status-success/10 text-status-success" },
  paused:    { label: "已暂停", dotClass: "bg-status-warning", bgClass: "bg-status-warning/10 text-status-warning" },
  completed: { label: "已完成", dotClass: "bg-status-success", bgClass: "bg-status-success/10 text-status-success" },
  idle:      { label: "未开始", dotClass: "bg-text-muted",     bgClass: "bg-text-muted/10 text-text-muted" },
  waiting:   { label: "等待中", dotClass: "bg-status-info",    bgClass: "bg-status-info/10 text-status-info" },
  error:     { label: "错误",   dotClass: "bg-status-error",   bgClass: "bg-status-error/10 text-status-error" },
};

interface StatusBadgeProps {
  status: Status;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const cfg = STATUS_CONFIG[status];
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${cfg.bgClass}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dotClass} ${status === "running" ? "animate-pulse-glow" : ""}`} />
      {cfg.label}
    </span>
  );
}
