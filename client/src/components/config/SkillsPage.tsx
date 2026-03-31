import { useEffect, useState } from "react";
import { Plus, Trash2, Download, Star, Loader2, X } from "lucide-react";
import { useConfigStore } from "../../stores/configStore";
import { GlassCard } from "../shared/GlassCard";

export function SkillsPage() {
  const { skills, fetchSkills, importSkill, deleteSkill } = useConfigStore();
  const [showImport, setShowImport] = useState(false);
  const [importText, setImportText] = useState("");
  const [importing, setImporting] = useState(false);
  const [importError, setImportError] = useState("");

  useEffect(() => {
    fetchSkills();
  }, [fetchSkills]);

  const handleImport = async () => {
    if (!importText.trim()) return;
    setImporting(true);
    setImportError("");
    try {
      await importSkill(importText.trim());
      setImportText("");
      setShowImport(false);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "导入失败");
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="flex-1 p-8 overflow-y-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-text-primary">技能管理</h1>
          <p className="text-sm text-text-secondary mt-1">管理和导入 Agent 技能</p>
        </div>
        <button
          onClick={() => setShowImport(true)}
          className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-[var(--radius-card)] gradient-brand-border text-text-secondary hover:text-text-primary transition-colors"
        >
          <Download size={14} />
          导入技能
        </button>
      </div>

      {/* 导入面板 */}
      {showImport && (
        <GlassCard className="p-5 mb-6 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-text-primary">导入技能</h3>
            <button onClick={() => setShowImport(false)} className="text-text-muted hover:text-text-secondary">
              <X size={16} />
            </button>
          </div>
          <p className="text-xs text-text-muted">输入 GitHub URL 或本地路径</p>
          <input
            value={importText}
            onChange={(e) => setImportText(e.target.value)}
            placeholder="https://github.com/user/repo 或 C:/path/to/skill"
            className="w-full bg-bg-elevated border border-border-subtle rounded-[var(--radius-sm)] px-3 py-2 text-sm text-text-primary placeholder:text-text-disabled outline-none focus:border-brand-purple/40 transition-colors"
            onKeyDown={(e) => e.key === "Enter" && handleImport()}
          />
          {importError && <p className="text-xs text-status-error">{importError}</p>}
          <div className="flex justify-end gap-2">
            <button onClick={() => setShowImport(false)} className="px-4 py-2 text-xs glass text-text-secondary">取消</button>
            <button
              onClick={handleImport}
              disabled={!importText.trim() || importing}
              className="flex items-center gap-1 px-4 py-2 text-xs gradient-brand text-white rounded-[var(--radius-sm)] disabled:opacity-50"
            >
              {importing ? <Loader2 size={12} className="animate-spin" /> : <Download size={12} />}
              导入
            </button>
          </div>
        </GlassCard>
      )}

      {/* 技能卡片网格 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {skills.map((skill) => (
          <GlassCard key={skill.id} className="p-4">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-brand-purple/10 flex items-center justify-center">
                  <Star size={18} className="text-brand-purple" />
                </div>
                <div className="min-w-0">
                  <h3 className="text-sm font-semibold text-text-primary truncate">
                    {skill.name || skill.id}
                  </h3>
                  {skill.description && (
                    <p className="text-xs text-text-muted truncate mt-0.5">{skill.description}</p>
                  )}
                </div>
              </div>
              <span className={`text-[10px] px-2 py-0.5 rounded-full ${skill.scope === "task" ? "bg-status-info/10 text-status-info" : "bg-brand-purple/10 text-brand-purple"}`}>
                {skill.scope === "task" ? "任务级" : "全局"}
              </span>
            </div>

            <div className="flex items-center gap-2 pt-2 border-t border-border-subtle">
              <span className={`flex items-center gap-1 text-[10px] ${skill.enabled ? "text-status-success" : "text-text-muted"}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${skill.enabled ? "bg-status-success" : "bg-text-disabled"}`} />
                {skill.enabled ? "已启用" : "已禁用"}
              </span>
              <div className="flex-1" />
              <button
                onClick={() => deleteSkill(skill.id)}
                className="flex items-center gap-1 px-2.5 py-1 text-xs glass glass-hover text-status-error/70 hover:text-status-error"
              >
                <Trash2 size={12} />
                删除
              </button>
            </div>
          </GlassCard>
        ))}

        {!showImport && (
          <button
            onClick={() => setShowImport(true)}
            className="border-2 border-dashed border-border-subtle rounded-[var(--radius-card)] p-8 flex flex-col items-center justify-center gap-2 hover:border-brand-purple/30 hover:bg-brand-purple/5 transition-all group"
          >
            <Plus size={24} className="text-text-disabled group-hover:text-brand-purple transition-colors" />
            <span className="text-sm text-text-muted group-hover:text-text-secondary transition-colors">
              导入新技能
            </span>
          </button>
        )}
      </div>
    </div>
  );
}
