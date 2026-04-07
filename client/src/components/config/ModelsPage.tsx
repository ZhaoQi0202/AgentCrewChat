import { useEffect, useState } from "react";
import { Plus, Trash2, Zap, X, Check, Loader2 } from "lucide-react";
import { useConfigStore } from "../../stores/configStore";
import { GlassCard } from "../shared/GlassCard";
import type { ModelConnection } from "../../types";

export function ModelsPage() {
  const {
    modelConnections,
    fetchModelConnections,
    createModelConnection,
    deleteModelConnection,
    probeModelConnection,
  } = useConfigStore();

  const [showForm, setShowForm] = useState(false);
  const [probing, setProbing] = useState<string | null>(null);
  const [probeResults, setProbeResults] = useState<Record<string, { ok: boolean; message: string }>>({});

  useEffect(() => {
    fetchModelConnections();
  }, [fetchModelConnections]);

  const handleProbe = async (id: string) => {
    setProbing(id);
    try {
      const result = await probeModelConnection(id);
      setProbeResults((prev) => ({ ...prev, [id]: result }));
    } catch {
      setProbeResults((prev) => ({ ...prev, [id]: { ok: false, message: "请求失败" } }));
    } finally {
      setProbing(null);
    }
  };

  return (
    <div className="flex-1 p-8 overflow-y-auto">
      {/* 页面标题 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-text-primary">模型连接管理</h1>
          <p className="text-sm text-text-secondary mt-1">管理 LLM 提供商连接配置</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-[var(--radius-card)] gradient-brand-border text-text-secondary hover:text-text-primary transition-colors"
        >
          <Plus size={14} />
          添加模型连接
        </button>
      </div>

      {/* 表单 */}
      {showForm && (
        <div className="mb-6">
          <ModelConnectionForm
            onSubmit={async (data) => {
              await createModelConnection(data);
              setShowForm(false);
            }}
            onCancel={() => setShowForm(false)}
          />
        </div>
      )}

      {/* 卡片网格 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {modelConnections.map((conn) => (
          <ConnectionCard
            key={conn.id}
            conn={conn}
            probing={probing === conn.id}
            probeResult={probeResults[conn.id]}
            onProbe={() => handleProbe(conn.id)}
            onDelete={() => deleteModelConnection(conn.id)}
          />
        ))}

        {/* 虚线占位卡片 */}
        {!showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="border-2 border-dashed border-border-subtle rounded-[var(--radius-card)] p-8 flex flex-col items-center justify-center gap-2 hover:border-brand-purple/30 hover:bg-brand-purple/5 transition-all group"
          >
            <Plus size={24} className="text-text-disabled group-hover:text-brand-purple transition-colors" />
            <span className="text-sm text-text-muted group-hover:text-text-secondary transition-colors">
              添加新连接
            </span>
          </button>
        )}
      </div>
    </div>
  );
}

// ── 连接卡片 ────────────────────────────────────────

function ConnectionCard({
  conn,
  probing,
  probeResult,
  onProbe,
  onDelete,
}: {
  conn: ModelConnection;
  probing: boolean;
  probeResult?: { ok: boolean; message: string };
  onProbe: () => void;
  onDelete: () => void;
}) {
  const providerLabel = conn.provider === "anthropic" ? "Anthropic" : "OpenAI Compatible";

  return (
    <GlassCard className="p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 rounded-lg gradient-brand flex items-center justify-center text-white text-sm font-bold shrink-0">
            {conn.provider === "anthropic" ? "A" : "O"}
          </div>
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-text-primary truncate">{conn.name || conn.id}</h3>
            <p className="text-xs text-text-muted">{providerLabel}</p>
          </div>
        </div>
        {conn.enabled && (
          <span className="flex items-center gap-1 text-[10px] text-status-success">
            <span className="w-1.5 h-1.5 rounded-full bg-status-success" />
            启用
          </span>
        )}
      </div>

      <div className="space-y-1 mb-3">
        <InfoLine label="模型" value={conn.model || "—"} />
        <InfoLine label="Base URL" value={conn.base_url || "默认"} />
        <InfoLine label="API Key" value={conn.api_key ? `${conn.api_key.slice(0, 8)}...` : "—"} />
      </div>

      {/* 探测结果 */}
      {probeResult && (
        <div className={`text-xs p-2 rounded-lg mb-3 ${probeResult.ok ? "bg-status-success/10 text-status-success" : "bg-status-error/10 text-status-error"}`}>
          {probeResult.ok ? "连接成功" : probeResult.message}
        </div>
      )}

      {/* 操作 */}
      <div className="flex items-center gap-2 pt-2 border-t border-border-subtle">
        <button
          onClick={onProbe}
          disabled={probing}
          className="flex items-center gap-1 px-2.5 py-1 text-xs glass glass-hover text-text-secondary"
        >
          {probing ? <Loader2 size={12} className="animate-spin" /> : <Zap size={12} />}
          测试
        </button>
        <button
          onClick={onDelete}
          className="flex items-center gap-1 px-2.5 py-1 text-xs glass glass-hover text-status-error/70 hover:text-status-error"
        >
          <Trash2 size={12} />
          删除
        </button>
      </div>
    </GlassCard>
  );
}

function InfoLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex text-xs">
      <span className="text-text-muted w-16 shrink-0">{label}</span>
      <span className="text-text-body truncate">{value}</span>
    </div>
  );
}

// ── 新建表单 ────────────────────────────────────────

function ModelConnectionForm({
  onSubmit,
  onCancel,
}: {
  onSubmit: (data: Omit<ModelConnection, "id">) => Promise<void>;
  onCancel: () => void;
}) {
  const [name, setName] = useState("");
  const [provider, setProvider] = useState<"openai_compatible" | "anthropic">("openai_compatible");
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    if (!name.trim()) return;
    setSaving(true);
    await onSubmit({
      name: name.trim(),
      provider,
      base_url: baseUrl.trim(),
      api_key: apiKey.trim(),
      model: model.trim(),
      enabled: true,
    });
    setSaving(false);
  };

  return (
    <GlassCard className="p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text-primary">添加模型连接</h3>
        <button onClick={onCancel} className="text-text-muted hover:text-text-secondary">
          <X size={16} />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Field label="名称" value={name} onChange={setName} placeholder="如: 硅基流动" />
        <div>
          <label className="block text-xs text-text-muted mb-1">提供商</label>
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value as typeof provider)}
            className="w-full bg-bg-elevated border border-border-subtle rounded-[var(--radius-sm)] px-3 py-2 text-sm text-text-primary outline-none"
          >
            <option value="openai_compatible">OpenAI Compatible</option>
            <option value="anthropic">Anthropic</option>
          </select>
        </div>
        <Field label="Base URL" value={baseUrl} onChange={setBaseUrl} placeholder="https://api.openai.com/v1" />
        <Field label="模型" value={model} onChange={setModel} placeholder="gpt-4o / claude-sonnet..." />
        <div className="col-span-2">
          <Field label="API Key" value={apiKey} onChange={setApiKey} placeholder="sk-..." type="password" />
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <button onClick={onCancel} className="px-4 py-2 text-xs glass text-text-secondary">
          取消
        </button>
        <button
          onClick={handleSubmit}
          disabled={!name.trim() || saving}
          className="flex items-center gap-1 px-4 py-2 text-xs gradient-brand text-white rounded-[var(--radius-sm)] disabled:opacity-50"
        >
          {saving ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}
          保存
        </button>
      </div>
    </GlassCard>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <div>
      <label className="block text-xs text-text-muted mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-bg-elevated border border-border-subtle rounded-[var(--radius-sm)] px-3 py-2 text-sm text-text-primary placeholder:text-text-disabled outline-none focus:border-brand-purple/40 transition-colors"
      />
    </div>
  );
}
