import { useEffect, useState } from "react";
import { Save, Loader2 } from "lucide-react";
import { useConfigStore } from "../../stores/configStore";
import { GlassCard } from "../shared/GlassCard";
import type { LlmSettings } from "../../types";

export function SettingsPage() {
  const {
    llmSettings,
    fetchLlmSettings,
    updateLlmSettings,
    modelConnections,
    fetchModelConnections,
  } = useConfigStore();

  const [form, setForm] = useState<LlmSettings | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetchLlmSettings();
    fetchModelConnections();
  }, [fetchLlmSettings, fetchModelConnections]);

  useEffect(() => {
    if (llmSettings) setForm({ ...llmSettings });
  }, [llmSettings]);

  const handleSave = async () => {
    if (!form) return;
    setSaving(true);
    await updateLlmSettings(form);
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  if (!form) return null;

  return (
    <div className="flex-1 p-8 overflow-y-auto max-w-2xl">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-text-primary">设置</h1>
        <p className="text-sm text-text-secondary mt-1">通用 LLM 和系统设置</p>
      </div>

      {/* 默认模型连接 */}
      <GlassCard className="p-5 mb-4">
        <h3 className="text-sm font-semibold text-text-primary mb-4">默认模型连接</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-xs text-text-muted mb-1">默认连接</label>
            <select
              value={form.default_model_connection_id || ""}
              onChange={(e) => setForm({ ...form, default_model_connection_id: e.target.value || null })}
              className="w-full bg-bg-elevated border border-border-subtle rounded-[var(--radius-sm)] px-3 py-2 text-sm text-text-primary outline-none"
            >
              <option value="">未设置</option>
              {modelConnections.map((c) => (
                <option key={c.id} value={c.id}>{c.name || c.id}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-text-muted mb-1">默认提供商</label>
            <select
              value={form.default_provider}
              onChange={(e) => setForm({ ...form, default_provider: e.target.value as "openai" | "anthropic" })}
              className="w-full bg-bg-elevated border border-border-subtle rounded-[var(--radius-sm)] px-3 py-2 text-sm text-text-primary outline-none"
            >
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
            </select>
          </div>
        </div>
      </GlassCard>

      {/* API Keys */}
      <GlassCard className="p-5 mb-4">
        <h3 className="text-sm font-semibold text-text-primary mb-4">API Keys（快捷设置）</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-xs text-text-muted mb-1">OpenAI API Key</label>
            <input
              type="password"
              value={form.openai_api_key}
              onChange={(e) => setForm({ ...form, openai_api_key: e.target.value })}
              placeholder="sk-..."
              className="w-full bg-bg-elevated border border-border-subtle rounded-[var(--radius-sm)] px-3 py-2 text-sm text-text-primary placeholder:text-text-disabled outline-none focus:border-brand-purple/40 transition-colors"
            />
          </div>
          <div>
            <label className="block text-xs text-text-muted mb-1">Anthropic API Key</label>
            <input
              type="password"
              value={form.anthropic_api_key}
              onChange={(e) => setForm({ ...form, anthropic_api_key: e.target.value })}
              placeholder="sk-ant-..."
              className="w-full bg-bg-elevated border border-border-subtle rounded-[var(--radius-sm)] px-3 py-2 text-sm text-text-primary placeholder:text-text-disabled outline-none focus:border-brand-purple/40 transition-colors"
            />
          </div>
        </div>
      </GlassCard>

      {/* 默认模型 */}
      <GlassCard className="p-5 mb-6">
        <h3 className="text-sm font-semibold text-text-primary mb-4">默认模型</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-text-muted mb-1">OpenAI 模型</label>
            <input
              value={form.openai_model}
              onChange={(e) => setForm({ ...form, openai_model: e.target.value })}
              className="w-full bg-bg-elevated border border-border-subtle rounded-[var(--radius-sm)] px-3 py-2 text-sm text-text-primary outline-none focus:border-brand-purple/40 transition-colors"
            />
          </div>
          <div>
            <label className="block text-xs text-text-muted mb-1">Anthropic 模型</label>
            <input
              value={form.anthropic_model}
              onChange={(e) => setForm({ ...form, anthropic_model: e.target.value })}
              className="w-full bg-bg-elevated border border-border-subtle rounded-[var(--radius-sm)] px-3 py-2 text-sm text-text-primary outline-none focus:border-brand-purple/40 transition-colors"
            />
          </div>
        </div>
      </GlassCard>

      {/* 保存按钮 */}
      <button
        onClick={handleSave}
        disabled={saving}
        className="flex items-center gap-1.5 px-5 py-2.5 text-sm gradient-brand text-white rounded-[var(--radius-sm)] disabled:opacity-50"
      >
        {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
        {saved ? "已保存" : "保存设置"}
      </button>
    </div>
  );
}
