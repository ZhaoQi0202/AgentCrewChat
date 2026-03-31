import { useEffect, useState } from "react";
import { Plus, Trash2, X, Check, Loader2, Terminal } from "lucide-react";
import { useConfigStore } from "../../stores/configStore";
import { GlassCard } from "../shared/GlassCard";

export function McpPage() {
  const { mcps, fetchMcps, createMcp, deleteMcp } = useConfigStore();
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    fetchMcps();
  }, [fetchMcps]);

  return (
    <div className="flex-1 p-8 overflow-y-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-text-primary">MCP 服务器</h1>
          <p className="text-sm text-text-secondary mt-1">管理 Model Context Protocol 服务器配置</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-[var(--radius-card)] gradient-brand-border text-text-secondary hover:text-text-primary transition-colors"
        >
          <Plus size={14} />
          添加 MCP 服务器
        </button>
      </div>

      {showForm && (
        <div className="mb-6">
          <McpForm
            onSubmit={async (data) => {
              await createMcp(data);
              setShowForm(false);
            }}
            onCancel={() => setShowForm(false)}
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {mcps.map((mcp) => (
          <GlassCard key={mcp.id} className="p-4">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-status-info/10 flex items-center justify-center">
                  <Terminal size={18} className="text-status-info" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-text-primary">{mcp.name || mcp.id}</h3>
                  <p className="text-xs text-text-muted font-mono">{mcp.command || "—"}</p>
                </div>
              </div>
            </div>

            {mcp.args.length > 0 && (
              <div className="mb-3">
                <span className="text-xs text-text-muted">参数: </span>
                <span className="text-xs text-text-body font-mono">{mcp.args.join(" ")}</span>
              </div>
            )}

            <div className="flex items-center gap-2 pt-2 border-t border-border-subtle">
              <button
                onClick={() => deleteMcp(mcp.id)}
                className="flex items-center gap-1 px-2.5 py-1 text-xs glass glass-hover text-status-error/70 hover:text-status-error"
              >
                <Trash2 size={12} />
                删除
              </button>
            </div>
          </GlassCard>
        ))}

        {!showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="border-2 border-dashed border-border-subtle rounded-[var(--radius-card)] p-8 flex flex-col items-center justify-center gap-2 hover:border-brand-purple/30 hover:bg-brand-purple/5 transition-all group"
          >
            <Plus size={24} className="text-text-disabled group-hover:text-brand-purple transition-colors" />
            <span className="text-sm text-text-muted group-hover:text-text-secondary transition-colors">
              添加 MCP 服务器
            </span>
          </button>
        )}
      </div>
    </div>
  );
}

function McpForm({
  onSubmit,
  onCancel,
}: {
  onSubmit: (data: { id: string; name: string; command: string; args: string[] }) => Promise<void>;
  onCancel: () => void;
}) {
  const [id, setId] = useState("");
  const [name, setName] = useState("");
  const [command, setCommand] = useState("");
  const [args, setArgs] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    if (!id.trim() || !command.trim()) return;
    setSaving(true);
    await onSubmit({
      id: id.trim(),
      name: name.trim() || id.trim(),
      command: command.trim(),
      args: args.trim() ? args.trim().split(/\s+/) : [],
    });
    setSaving(false);
  };

  return (
    <GlassCard className="p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text-primary">添加 MCP 服务器</h3>
        <button onClick={onCancel} className="text-text-muted hover:text-text-secondary">
          <X size={16} />
        </button>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <FormField label="ID" value={id} onChange={setId} placeholder="my-mcp-server" />
        <FormField label="名称" value={name} onChange={setName} placeholder="可选显示名" />
        <FormField label="命令" value={command} onChange={setCommand} placeholder="npx / python / node" />
        <FormField label="参数" value={args} onChange={setArgs} placeholder="以空格分隔" />
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <button onClick={onCancel} className="px-4 py-2 text-xs glass text-text-secondary">取消</button>
        <button
          onClick={handleSubmit}
          disabled={!id.trim() || !command.trim() || saving}
          className="flex items-center gap-1 px-4 py-2 text-xs gradient-brand text-white rounded-[var(--radius-sm)] disabled:opacity-50"
        >
          {saving ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}
          保存
        </button>
      </div>
    </GlassCard>
  );
}

function FormField({ label, value, onChange, placeholder }: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-xs text-text-muted mb-1">{label}</label>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-bg-elevated border border-border-subtle rounded-[var(--radius-sm)] px-3 py-2 text-sm text-text-primary placeholder:text-text-disabled outline-none focus:border-brand-purple/40 transition-colors"
      />
    </div>
  );
}
