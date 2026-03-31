import { create } from "zustand";
import type { LlmSettings, McpEntry, ModelConnection, SkillEntry } from "../types";
import {
  llmSettingsApi,
  mcpApi,
  modelConnectionsApi,
  skillsApi,
} from "../services/api";

interface ConfigStore {
  // 模型连接
  modelConnections: ModelConnection[];
  fetchModelConnections: () => Promise<void>;
  createModelConnection: (data: Omit<ModelConnection, "id">) => Promise<void>;
  deleteModelConnection: (id: string) => Promise<void>;
  probeModelConnection: (id: string) => Promise<{ ok: boolean; message: string }>;

  // MCP
  mcps: McpEntry[];
  fetchMcps: () => Promise<void>;
  createMcp: (data: McpEntry) => Promise<void>;
  deleteMcp: (id: string) => Promise<void>;

  // 技能
  skills: SkillEntry[];
  fetchSkills: () => Promise<void>;
  importSkill: (text: string) => Promise<SkillEntry[]>;
  deleteSkill: (id: string) => Promise<void>;

  // LLM 设置
  llmSettings: LlmSettings | null;
  fetchLlmSettings: () => Promise<void>;
  updateLlmSettings: (data: LlmSettings) => Promise<void>;
}

export const useConfigStore = create<ConfigStore>((set) => ({
  // ── 模型连接 ──────────────────────────────────────
  modelConnections: [],
  fetchModelConnections: async () => {
    const list = await modelConnectionsApi.list();
    set({ modelConnections: list });
  },
  createModelConnection: async (data) => {
    const entry = await modelConnectionsApi.create(data);
    set((s) => ({ modelConnections: [...s.modelConnections, entry] }));
  },
  deleteModelConnection: async (id) => {
    await modelConnectionsApi.remove(id);
    set((s) => ({
      modelConnections: s.modelConnections.filter((c) => c.id !== id),
    }));
  },
  probeModelConnection: async (id) => {
    return modelConnectionsApi.probe(id);
  },

  // ── MCP ───────────────────────────────────────────
  mcps: [],
  fetchMcps: async () => {
    const list = await mcpApi.list();
    set({ mcps: list });
  },
  createMcp: async (data) => {
    const entry = await mcpApi.create(data);
    set((s) => ({ mcps: [...s.mcps, entry] }));
  },
  deleteMcp: async (id) => {
    await mcpApi.remove(id);
    set((s) => ({ mcps: s.mcps.filter((m) => m.id !== id) }));
  },

  // ── 技能 ──────────────────────────────────────────
  skills: [],
  fetchSkills: async () => {
    const list = await skillsApi.list();
    set({ skills: list });
  },
  importSkill: async (text) => {
    const entries = await skillsApi.importSkill(text);
    set((s) => ({ skills: [...s.skills, ...entries] }));
    return entries;
  },
  deleteSkill: async (id) => {
    await skillsApi.remove(id);
    set((s) => ({ skills: s.skills.filter((sk) => sk.id !== id) }));
  },

  // ── LLM 设置 ─────────────────────────────────────
  llmSettings: null,
  fetchLlmSettings: async () => {
    const settings = await llmSettingsApi.get();
    set({ llmSettings: settings });
  },
  updateLlmSettings: async (data) => {
    const settings = await llmSettingsApi.update(data);
    set({ llmSettings: settings });
  },
}));
