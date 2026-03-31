import { useChatStore } from "../../stores/chatStore";
import { AGENT_META, WORKFLOW_PHASES, type AgentId } from "../../types";
import { AgentAvatar } from "../shared/AgentAvatar";

export function RightPanel() {
  const { currentPhase, events, isRunning } = useChatStore();

  // 从事件流推断每个阶段的完成状态
  const completedPhases = new Set<string>();
  for (const e of events) {
    if (e.type === "agent_output" && e.agent) {
      completedPhases.add(e.agent);
    }
  }

  // 活跃 Agent 列表
  const activeAgents = WORKFLOW_PHASES.filter(
    (id) => completedPhases.has(id) || id === currentPhase,
  );

  return (
    <aside className="w-[260px] shrink-0 border-l border-border-subtle bg-bg-surface/50 flex flex-col overflow-y-auto">
      {/* 工作流进度 */}
      <div className="p-4 border-b border-border-subtle">
        <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
          工作流进度
        </h3>
        <div className="space-y-0">
          {WORKFLOW_PHASES.map((phaseId, i) => {
            const meta = AGENT_META[phaseId];
            const isCompleted = completedPhases.has(phaseId) && phaseId !== currentPhase;
            const isCurrent = phaseId === currentPhase;
            const isPending = !isCompleted && !isCurrent;

            return (
              <div key={phaseId} className="flex items-stretch gap-3">
                {/* 时间线 */}
                <div className="flex flex-col items-center w-6">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold shrink-0
                      ${isCompleted
                        ? "bg-status-success/20 text-status-success"
                        : isCurrent
                          ? "bg-status-warning/20 text-status-warning animate-pulse-glow"
                          : "bg-bg-elevated text-text-disabled border border-border-subtle"
                      }`}
                  >
                    {isCompleted ? "✓" : i + 1}
                  </div>
                  {i < WORKFLOW_PHASES.length - 1 && (
                    <div
                      className={`w-0.5 flex-1 min-h-[20px] my-1 rounded-full ${
                        isCompleted
                          ? "bg-status-success/40"
                          : isCurrent
                            ? "bg-status-warning/30"
                            : "bg-border-subtle"
                      }`}
                    />
                  )}
                </div>
                {/* 阶段信息 */}
                <div className="pb-4 pt-0.5 min-w-0">
                  <p
                    className={`text-sm font-medium truncate ${
                      isPending ? "text-text-disabled" : "text-text-primary"
                    }`}
                  >
                    {meta.emoji} {meta.label}
                  </p>
                  <p className="text-[11px] text-text-muted mt-0.5">
                    {isCompleted
                      ? "已完成"
                      : isCurrent
                        ? isRunning
                          ? "运行中..."
                          : "等待审核"
                        : "未开始"}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 活跃 Agent */}
      <div className="p-4 border-b border-border-subtle">
        <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
          活跃 Agent
        </h3>
        {activeAgents.length === 0 ? (
          <p className="text-xs text-text-muted">暂无活跃 Agent</p>
        ) : (
          <div className="space-y-2">
            {activeAgents.map((id) => {
              const meta = AGENT_META[id];
              const isCurrent = id === currentPhase;
              return (
                <div
                  key={id}
                  className="flex items-center gap-2.5 p-2 rounded-lg bg-bg-elevated"
                >
                  <AgentAvatar agentId={id} size={28} />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium truncate" style={{ color: meta.nameColor }}>
                      {meta.label}
                    </p>
                    <p className="text-[10px] text-text-muted">
                      {isCurrent ? "活跃" : "已完成"}
                    </p>
                  </div>
                  <span
                    className={`w-2 h-2 rounded-full shrink-0 ${
                      isCurrent ? "bg-status-success animate-pulse-glow" : "bg-text-disabled"
                    }`}
                  />
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 任务信息 */}
      <div className="p-4">
        <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
          任务信息
        </h3>
        <dl className="space-y-2 text-xs">
          <InfoRow label="状态" value={isRunning ? "运行中" : currentPhase ? "已暂停" : "未开始"} />
          <InfoRow label="当前阶段" value={currentPhase ? AGENT_META[currentPhase as AgentId]?.label ?? currentPhase : "—"} />
          <InfoRow label="事件数" value={String(events.length)} />
        </dl>
      </div>
    </aside>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <dt className="text-text-muted">{label}</dt>
      <dd className="text-text-body font-medium">{value}</dd>
    </div>
  );
}
