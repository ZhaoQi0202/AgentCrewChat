type RestartDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
};

export function RestartDialog({ open, onOpenChange, onConfirm }: RestartDialogProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div
        className="absolute inset-0"
        onClick={() => onOpenChange(false)}
        aria-hidden
      />
      <div className="relative glass max-w-md w-full rounded-[var(--radius-card)] p-5 shadow-lg border border-border-subtle">
        <p className="text-sm text-text-primary leading-relaxed">
          重启后所有对话记录和工作进度将被清除，需求分析师将重新加入开始新一轮协作。
        </p>
        <div className="flex justify-end gap-2 mt-5">
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            className="px-3 py-1.5 text-xs font-medium rounded-lg glass glass-hover text-text-secondary"
          >
            取消
          </button>
          <button
            type="button"
            onClick={() => {
              onConfirm();
              onOpenChange(false);
            }}
            className="px-3 py-1.5 text-xs font-medium rounded-lg bg-status-error/90 text-white hover:bg-status-error"
          >
            确认重启
          </button>
        </div>
      </div>
    </div>
  );
}
