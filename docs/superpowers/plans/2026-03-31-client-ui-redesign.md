# AgentLoom 客户端 UI 重设计 — 实施计划

> **设计规格**: `docs/superpowers/specs/2026-03-31-client-ui-redesign.md`
> **目标**: PySide6 → Electron + React 前端，玻璃拟态深色 SaaS 风 UI

---

## Phase 0: Python FastAPI 后端 API 层

将现有同步业务逻辑封装为 REST + WebSocket API，供 React 前端调用。

### Step 0.1 — 添加 FastAPI 依赖

- [ ] 在 `pyproject.toml` 的 `dependencies` 中添加：
  ```
  "fastapi>=0.115",
  "uvicorn[standard]>=0.34",
  "websockets>=14",
  ```
- [ ] 运行 `uv sync` 安装依赖

### Step 0.2 — 创建 API 入口模块

- [ ] 创建 `src/agentloom/api/__init__.py`（空文件）
- [ ] 创建 `src/agentloom/api/app.py`：
  ```python
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware

  from agentloom.bootstrap import ensure_layout

  def create_app() -> FastAPI:
      ensure_layout()
      app = FastAPI(title="AgentLoom API", version="0.1.0")
      app.add_middleware(
          CORSMiddleware,
          allow_origins=["http://localhost:5173", "http://localhost:3000"],
          allow_methods=["*"],
          allow_headers=["*"],
      )
      from agentloom.api.routes import config_router, tasks_router, graph_router
      app.include_router(config_router, prefix="/api")
      app.include_router(tasks_router, prefix="/api")
      app.include_router(graph_router, prefix="/api")
      return app
  ```
- [ ] 创建 `src/agentloom/api/server.py`：
  ```python
  import uvicorn
  from agentloom.api.app import create_app

  def main(host: str = "127.0.0.1", port: int = 9800) -> None:
      app = create_app()
      uvicorn.run(app, host=host, port=port)

  if __name__ == "__main__":
      main()
  ```

### Step 0.3 — 配置管理 REST 路由

- [ ] 创建 `src/agentloom/api/routes/__init__.py`：
  ```python
  from agentloom.api.routes.config import router as config_router
  from agentloom.api.routes.tasks import router as tasks_router
  from agentloom.api.routes.graph import router as graph_router
  ```
- [ ] 创建 `src/agentloom/api/routes/config.py`，实现以下端点：
  - `GET /config/model-connections` — 调用 `list_model_connections()`
  - `POST /config/model-connections` — 调用 `save_model_connection_entry()`
  - `DELETE /config/model-connections/{id}` — 调用 `delete_model_connection_entry()`
  - `POST /config/model-connections/{id}/probe` — 调用 `probe_model_connection()`
  - `GET /config/mcps` — 从 `load_all()` 提取 MCPs
  - `POST /config/mcps` — 调用 `save_mcp_entry()`
  - `GET /config/skills` — 从 `load_all()` 提取 Skills
  - `POST /config/skills/import` — 调用 `import_skills_from_input()`
  - `DELETE /config/skills/{id}` — 调用 `delete_skill_entry()`
  - `GET /config/llm-settings` — 调用 `load_llm_settings()`
  - `PUT /config/llm-settings` — 调用 `save_llm_settings()`

### Step 0.4 — 任务管理 REST 路由

- [ ] 创建 `src/agentloom/api/routes/tasks.py`：
  - `GET /tasks` — 调用 `list_tasks()`, 返回任务列表（名称、路径、修改时间）
  - `POST /tasks` — 调用 `create_task(name)`，返回新任务信息

### Step 0.5 — 图谱执行 WebSocket 路由

- [ ] 创建 `src/agentloom/api/routes/graph.py`，包含：
  - `WebSocket /ws/graph/{session_id}` — 实时事件流
  - 启动图谱：接收 `{"action": "start", "task_id": "..."}` → 在线程池中运行 `build_graph()` + stream
  - 将 `phase_event` / `interrupted` / `finished` / `error` 映射为 JSON 消息推送
  - 恢复执行：接收 `{"action": "resume", "feedback": "..."}` → `Command(resume=feedback)`
  - 核心逻辑：将 `GraphRunner._run_stream` 的同步流式逻辑改写为 async，通过 `asyncio.to_thread` 包装阻塞调用

### Step 0.6 — 验证 API 可运行

- [ ] 启动 `python -m agentloom.api.server`，验证：
  - `GET /docs` 能打开 Swagger UI
  - `GET /api/config/model-connections` 返回 JSON 列表
  - `GET /api/tasks` 返回任务列表
- [ ] **提交 Git**: `feat: add FastAPI REST + WebSocket API layer`

---

## Phase 1: Electron + React 项目脚手架

### Step 1.1 — 初始化前端项目

- [ ] 在项目根目录运行：
  ```bash
  npm create vite@latest client -- --template react-ts
  cd client && npm install
  ```
- [ ] 安装核心依赖：
  ```bash
  npm install tailwindcss @tailwindcss/vite
  npm install zustand framer-motion lucide-react
  npm install -D @types/node
  ```
- [ ] 安装 shadcn/ui（按官方 Vite 指南初始化）：
  ```bash
  npx shadcn@latest init
  ```
  选择: New York 风格 / Zinc 基色 / CSS variables: yes

### Step 1.2 — 安装并配置 Electron

- [ ] 安装 Electron 及构建工具：
  ```bash
  npm install -D electron electron-builder concurrently wait-on
  ```
- [ ] 创建 `client/electron/main.ts`：
  ```typescript
  import { app, BrowserWindow } from "electron";
  import path from "path";

  let mainWindow: BrowserWindow | null = null;

  function createWindow() {
    mainWindow = new BrowserWindow({
      width: 1440,
      height: 900,
      minWidth: 1024,
      minHeight: 700,
      frame: false,           // 无边框窗口，自定义标题栏
      titleBarStyle: "hidden",
      backgroundColor: "#09090f",
      webPreferences: {
        preload: path.join(__dirname, "preload.js"),
        contextIsolation: true,
        nodeIntegration: false,
      },
    });

    if (process.env.VITE_DEV_SERVER_URL) {
      mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL);
    } else {
      mainWindow.loadFile(path.join(__dirname, "../dist/index.html"));
    }
  }

  app.whenReady().then(createWindow);
  app.on("window-all-closed", () => app.quit());
  ```
- [ ] 创建 `client/electron/preload.ts`：
  ```typescript
  import { contextBridge, ipcRenderer } from "electron";

  contextBridge.exposeInMainWorld("electronAPI", {
    minimize: () => ipcRenderer.send("window:minimize"),
    maximize: () => ipcRenderer.send("window:maximize"),
    close: () => ipcRenderer.send("window:close"),
  });
  ```
- [ ] 在 `client/package.json` 中添加 Electron 开发脚本：
  ```json
  {
    "main": "electron/main.js",
    "scripts": {
      "dev": "vite",
      "dev:electron": "concurrently \"vite\" \"wait-on http://localhost:5173 && electron .\"",
      "build": "tsc && vite build",
      "build:electron": "npm run build && electron-builder"
    }
  }
  ```
- [ ] 配置 `client/electron-builder.yml`

### Step 1.3 — Tailwind 深色玻璃拟态主题

- [ ] 创建 `client/src/styles/globals.css`：
  ```css
  @import "tailwindcss";

  @theme {
    --color-bg-base: #09090f;
    --color-bg-surface: #13131a;
    --color-bg-elevated: rgba(255, 255, 255, 0.03);
    --color-border-subtle: rgba(255, 255, 255, 0.06);
    --color-border-default: rgba(255, 255, 255, 0.08);
    --color-text-primary: #e4e4e7;
    --color-text-secondary: #a1a1aa;
    --color-text-muted: #71717a;
    --color-text-disabled: #52525b;
    --color-brand-purple: #8b5cf6;
    --color-brand-blue: #3b82f6;
    --color-status-success: #22c55e;
    --color-status-warning: #fbbf24;
    --color-status-error: #ef4444;
    --color-status-info: #60a5fa;
    --radius-card: 12px;
  }

  body {
    background-color: var(--color-bg-base);
    color: var(--color-text-primary);
    font-family: "Inter", system-ui, -apple-system, sans-serif;
    -webkit-font-smoothing: antialiased;
  }

  /* 玻璃态表面 */
  .glass {
    background: var(--color-bg-elevated);
    border: 1px solid var(--color-border-subtle);
    border-radius: var(--radius-card);
    backdrop-filter: blur(12px);
  }

  .glass-hover:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: var(--color-border-default);
  }

  /* 品牌渐变 */
  .gradient-brand {
    background: linear-gradient(135deg, #8b5cf6, #3b82f6);
  }

  .gradient-brand-border {
    border: 1px solid transparent;
    background-clip: padding-box;
    position: relative;
  }
  .gradient-brand-border::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    padding: 1px;
    background: linear-gradient(135deg, #8b5cf6, #3b82f6);
    mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    mask-composite: exclude;
    pointer-events: none;
  }
  ```

### Step 1.4 — 验证脚手架运行

- [ ] `cd client && npm run dev` 确认 Vite 开发服务器启动
- [ ] `npm run dev:electron` 确认 Electron 窗口能加载 React 页面
- [ ] **提交 Git**: `feat: scaffold Electron + React + Tailwind client`

---

## Phase 2: 前端 API 通信层

### Step 2.1 — TypeScript 类型定义

- [ ] 创建 `client/src/types/index.ts`，从 Python Pydantic 模型 1:1 映射：
  ```typescript
  // 配置类型
  export interface ModelConnection {
    id: string;
    name: string;
    provider: "openai_compatible" | "anthropic";
    base_url: string;
    api_key: string;
    model: string;
    enabled: boolean;
  }

  export interface McpEntry {
    id: string;
    name: string | null;
    command: string | null;
    args: string[];
  }

  export interface SkillEntry {
    id: string;
    name: string | null;
    description: string | null;
    skill_dir: string;
    enabled: boolean;
    scope: "app" | "task";
  }

  export interface LlmSettings {
    default_model_connection_id: string | null;
    default_provider: "openai" | "anthropic";
    openai_api_key: string;
    anthropic_api_key: string;
    openai_model: string;
    anthropic_model: string;
  }

  // 任务类型
  export interface Task {
    id: string;
    name: string;
    path: string;
    modified_at: string;
    status: "idle" | "running" | "paused" | "completed";
  }

  // Agent 对话流事件
  export type ChatEventType =
    | "phase_start"
    | "agent_thinking"
    | "agent_output"
    | "hitl_interrupt"
    | "user_response"
    | "phase_complete"
    | "task_complete"
    | "error";

  export interface ChatEvent {
    type: ChatEventType;
    timestamp: string;
    phase?: string;
    agent?: AgentId;
    content?: string;
    metadata?: Record<string, unknown>;
  }

  export type AgentId =
    | "consultant"
    | "architect"
    | "hitl_blueprint"
    | "experts"
    | "reviewer";

  export const AGENT_META: Record<AgentId, {
    label: string;
    emoji: string;
    gradient: [string, string];
    nameColor: string;
  }> = {
    consultant:     { label: "Consultant",      emoji: "🔍", gradient: ["#8b5cf6", "#6366f1"], nameColor: "#c4b5fd" },
    architect:      { label: "Architect",        emoji: "📐", gradient: ["#3b82f6", "#06b6d4"], nameColor: "#93c5fd" },
    hitl_blueprint: { label: "HITL Blueprint",   emoji: "⏸",  gradient: ["#f59e0b", "#f97316"], nameColor: "#fcd34d" },
    experts:        { label: "Expert (Swarm)",   emoji: "⚡", gradient: ["#22c55e", "#10b981"], nameColor: "#86efac" },
    reviewer:       { label: "Reviewer",         emoji: "🔎", gradient: ["#ec4899", "#f43f5e"], nameColor: "#f9a8d4" },
  };
  ```

### Step 2.2 — REST API 客户端

- [ ] 创建 `client/src/services/api.ts`：
  ```typescript
  const BASE = "http://127.0.0.1:9800/api";

  async function request<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    return res.json();
  }

  // 模型连接
  export const modelConnectionsApi = {
    list: () => request<ModelConnection[]>("/config/model-connections"),
    create: (data: Omit<ModelConnection, "id">) =>
      request<ModelConnection>("/config/model-connections", {
        method: "POST", body: JSON.stringify(data),
      }),
    remove: (id: string) =>
      request<void>(`/config/model-connections/${id}`, { method: "DELETE" }),
    probe: (id: string) =>
      request<{ ok: boolean; message: string }>(
        `/config/model-connections/${id}/probe`, { method: "POST" }
      ),
  };

  // MCP 服务器
  export const mcpApi = {
    list: () => request<McpEntry[]>("/config/mcps"),
    create: (data: McpEntry) =>
      request<McpEntry>("/config/mcps", {
        method: "POST", body: JSON.stringify(data),
      }),
  };

  // 技能
  export const skillsApi = {
    list: () => request<SkillEntry[]>("/config/skills"),
    importSkill: (text: string) =>
      request<SkillEntry[]>("/config/skills/import", {
        method: "POST", body: JSON.stringify({ text }),
      }),
    remove: (id: string) =>
      request<void>(`/config/skills/${id}`, { method: "DELETE" }),
  };

  // LLM 设置
  export const llmSettingsApi = {
    get: () => request<LlmSettings>("/config/llm-settings"),
    update: (data: LlmSettings) =>
      request<LlmSettings>("/config/llm-settings", {
        method: "PUT", body: JSON.stringify(data),
      }),
  };

  // 任务
  export const tasksApi = {
    list: () => request<Task[]>("/tasks"),
    create: (name: string) =>
      request<Task>("/tasks", {
        method: "POST", body: JSON.stringify({ name }),
      }),
  };
  ```

### Step 2.3 — WebSocket 事件管理

- [ ] 创建 `client/src/services/websocket.ts`：
  ```typescript
  import type { ChatEvent } from "../types";

  type EventHandler = (event: ChatEvent) => void;

  export class GraphSocket {
    private ws: WebSocket | null = null;
    private handlers = new Set<EventHandler>();

    connect(sessionId: string) {
      this.ws = new WebSocket(`ws://127.0.0.1:9800/ws/graph/${sessionId}`);
      this.ws.onmessage = (e) => {
        const event: ChatEvent = JSON.parse(e.data);
        this.handlers.forEach((h) => h(event));
      };
      this.ws.onclose = () => { this.ws = null; };
    }

    send(data: Record<string, unknown>) {
      this.ws?.send(JSON.stringify(data));
    }

    subscribe(handler: EventHandler) {
      this.handlers.add(handler);
      return () => this.handlers.delete(handler);
    }

    disconnect() {
      this.ws?.close();
      this.ws = null;
    }
  }

  export const graphSocket = new GraphSocket();
  ```

### Step 2.4 — Zustand 状态管理

- [ ] 创建 `client/src/stores/taskStore.ts`：
  ```typescript
  import { create } from "zustand";
  import type { Task } from "../types";
  import { tasksApi } from "../services/api";

  interface TaskStore {
    tasks: Task[];
    activeTaskId: string | null;
    loading: boolean;
    fetchTasks: () => Promise<void>;
    createTask: (name: string) => Promise<void>;
    setActiveTask: (id: string) => void;
  }

  export const useTaskStore = create<TaskStore>((set) => ({
    tasks: [],
    activeTaskId: null,
    loading: false,
    fetchTasks: async () => {
      set({ loading: true });
      const tasks = await tasksApi.list();
      set({ tasks, loading: false });
    },
    createTask: async (name) => {
      const task = await tasksApi.create(name);
      set((s) => ({ tasks: [task, ...s.tasks], activeTaskId: task.id }));
    },
    setActiveTask: (id) => set({ activeTaskId: id }),
  }));
  ```
- [ ] 创建 `client/src/stores/chatStore.ts`：
  ```typescript
  import { create } from "zustand";
  import type { ChatEvent } from "../types";
  import { graphSocket } from "../services/websocket";

  interface ChatStore {
    events: ChatEvent[];              // 当前任务的对话流事件
    currentPhase: string | null;
    isRunning: boolean;
    isInterrupted: boolean;
    addEvent: (event: ChatEvent) => void;
    clearEvents: () => void;
    startGraph: (taskId: string) => void;
    resumeGraph: (feedback: string) => void;
  }

  export const useChatStore = create<ChatStore>((set, get) => ({
    events: [],
    currentPhase: null,
    isRunning: false,
    isInterrupted: false,
    addEvent: (event) =>
      set((s) => ({
        events: [...s.events, event],
        currentPhase:
          event.type === "phase_start" ? event.phase ?? s.currentPhase : s.currentPhase,
        isInterrupted: event.type === "hitl_interrupt",
        isRunning:
          event.type === "task_complete" || event.type === "error" ? false : s.isRunning,
      })),
    clearEvents: () =>
      set({ events: [], currentPhase: null, isRunning: false, isInterrupted: false }),
    startGraph: (taskId) => {
      const sessionId = crypto.randomUUID();
      graphSocket.connect(sessionId);
      graphSocket.subscribe((event) => get().addEvent(event));
      graphSocket.send({ action: "start", task_id: taskId });
      set({ isRunning: true, isInterrupted: false });
    },
    resumeGraph: (feedback) => {
      graphSocket.send({ action: "resume", feedback });
      set({ isInterrupted: false });
    },
  }));
  ```
- [ ] 创建 `client/src/stores/configStore.ts`（模型连接、MCP、技能的 CRUD 状态）
- [ ] **提交 Git**: `feat: add API client, WebSocket manager, and Zustand stores`

---

## Phase 3: 四栏布局 + 导航

### Step 3.1 — App 根布局

- [ ] 重写 `client/src/App.tsx`：
  ```typescript
  import { useState } from "react";
  import { IconSidebar, type NavPage } from "./components/layout/IconSidebar";
  import { TaskList } from "./components/layout/TaskList";
  import { RightPanel } from "./components/layout/RightPanel";
  import { ChatArea } from "./components/chat/ChatArea";
  import { ModelsPage } from "./components/config/ModelsPage";
  import { McpPage } from "./components/config/McpPage";
  import { SkillsPage } from "./components/config/SkillsPage";
  import { SettingsPage } from "./components/config/SettingsPage";

  export default function App() {
    const [page, setPage] = useState<NavPage>("tasks");
    const isTaskPage = page === "tasks";

    const mainContent: Record<NavPage, React.ReactNode> = {
      tasks: <ChatArea />,
      models: <ModelsPage />,
      mcp: <McpPage />,
      skills: <SkillsPage />,
      settings: <SettingsPage />,
    };

    return (
      <div className="flex h-screen w-screen overflow-hidden bg-bg-base">
        <IconSidebar activePage={page} onNavigate={setPage} />
        {isTaskPage && <TaskList />}
        <main className="flex-1 flex flex-col min-w-0">
          {mainContent[page]}
        </main>
        {isTaskPage && <RightPanel />}
      </div>
    );
  }
  ```

### Step 3.2 — 图标侧栏

- [ ] 创建 `client/src/components/layout/IconSidebar.tsx`：
  - 56px 固定宽度，深色玻璃态背景
  - 顶部: AgentLoom Logo（紫蓝渐变圆角方块 + "AL" 字母）
  - 导航图标: tasks / models / mcp / skills（使用 lucide-react 图标）
  - 底部: settings 图标
  - 激活态: 紫色背景 `bg-brand-purple/20` + 左侧 3px 紫色指示条

### Step 3.3 — 任务列表

- [ ] 创建 `client/src/components/layout/TaskList.tsx`：
  - 240px 宽度，右侧 1px 边框
  - 搜索框（玻璃态背景 + 搜索图标）
  - "+ 新建任务" 按钮（渐变边框）
  - 任务列表项：名称 / 阶段标签 / 更新时间 / 左侧状态圆点
  - 点击切换 `taskStore.setActiveTask()`

### Step 3.4 — 右侧面板

- [ ] 创建 `client/src/components/layout/RightPanel.tsx`：
  - 260px 固定宽度
  - 工作流进度：五阶段垂直时间线（圆形图标 + 连线 + 状态）
  - 活跃 Agent 卡片列表
  - 任务信息键值对
  - 从 `chatStore` 读取 `currentPhase` 高亮当前阶段

### Step 3.5 — 共享 UI 组件

- [ ] 创建 `client/src/components/shared/GlassCard.tsx`（`.glass` 样式封装）
- [ ] 创建 `client/src/components/shared/AgentAvatar.tsx`（渐变圆形头像，按 AgentId 映射颜色）
- [ ] 创建 `client/src/components/shared/StatusBadge.tsx`（状态标签：运行中/已暂停/已完成）
- [ ] **提交 Git**: `feat: implement 4-column layout with navigation`

---

## Phase 4: 群聊对话系统

### Step 4.1 — 对话区容器

- [ ] 创建 `client/src/components/chat/ChatArea.tsx`：
  - 顶部信息栏：任务名称 + 状态标签 + 操作按钮（运行图谱 / 继续）
  - 中间滚动区：渲染 `chatStore.events` 为不同消息类型组件
  - 底部输入区：`ChatInput` 组件
  - 自动滚动到底部（新消息时）

### Step 4.2 — 系统消息

- [ ] 创建 `client/src/components/chat/SystemMessage.tsx`：
  - 居中小标签，半透明背景
  - 任务启动: "任务已启动 · 阶段 1: Consultant"
  - 阶段切换: "→ 阶段 2: Architect"
  - 任务完成: "任务完成 · 5 个阶段 · 耗时 X 分 Y 秒"

### Step 4.3 — Agent 消息卡片

- [ ] 创建 `client/src/components/chat/AgentMessage.tsx`：
  - 左对齐布局：`AgentAvatar` + 消息体
  - 消息头：Agent 名称（带颜色）+ emoji + 时间戳
  - 消息气泡：玻璃态背景，`rounded-tl-sm` 左上角小圆角
  - 支持 Markdown 渲染（安装 `react-markdown`）
  - 打字动画：`agent_thinking` 事件显示三点脉冲

### Step 4.4 — 用户消息

- [ ] 创建 `client/src/components/chat/UserMessage.tsx`：
  - 右对齐布局
  - 略带紫色调的消息气泡 `bg-brand-purple/10`
  - 用户头像（默认灰色圆形 + 用户图标）

### Step 4.5 — HITL 中断卡片

- [ ] 创建 `client/src/components/chat/HITLCard.tsx`：
  - 黄色主题警告框 `border-status-warning/30`
  - 暂停图标 + "需要人工审核" 标题
  - 说明文字
  - 等待用户在底部输入框回复

### Step 4.6 — 输入区

- [ ] 创建 `client/src/components/chat/ChatInput.tsx`：
  - 玻璃态输入框 + 发送按钮（紫蓝渐变）
  - Placeholder: "输入消息与 Agent 对话..."
  - Enter 发送，Shift+Enter 换行
  - 发送时调用 `chatStore.resumeGraph(text)` 并添加 `user_response` 事件
  - HITL 中断时输入框获得焦点 + 提示文字变为 "回复 Agent..."

### Step 4.7 — 消息渲染路由

- [ ] 在 `ChatArea.tsx` 中按 `event.type` 分发：
  ```typescript
  {events.map((event, i) => {
    switch (event.type) {
      case "phase_start":
      case "phase_complete":
      case "task_complete":
        return <SystemMessage key={i} event={event} />;
      case "agent_thinking":
      case "agent_output":
        return <AgentMessage key={i} event={event} />;
      case "hitl_interrupt":
        return <HITLCard key={i} event={event} />;
      case "user_response":
        return <UserMessage key={i} event={event} />;
      case "error":
        return <ErrorCard key={i} event={event} />;
    }
  })}
  ```
- [ ] **提交 Git**: `feat: implement group chat system with Agent messages`

---

## Phase 5: 配置页面

### Step 5.1 — 模型管理页面

- [ ] 创建 `client/src/components/config/ModelsPage.tsx`：
  - 页面标题 "模型连接管理" + "+ 添加模型连接" 按钮
  - 2 列卡片网格
  - 每张卡片: 提供商图标 + 连接名称 + 模型名 + 状态圆点 + 标签（默认/备用）
  - 操作: 测试连接（调用 probe）/ 编辑 / 删除
  - 虚线占位卡片引导添加
- [ ] 创建 `client/src/components/config/ModelConnectionForm.tsx`：
  - 滑出式面板或内联表单
  - 字段: name / provider (select) / base_url / api_key (密码框) / model
  - 提交调用 `configStore.createModelConnection()`

### Step 5.2 — MCP 服务器页面

- [ ] 创建 `client/src/components/config/McpPage.tsx`：
  - 结构同模型管理，卡片显示: 名称 / command + args / 状态
  - MCP 编辑表单: name / command / args（多行）

### Step 5.3 — 技能管理页面

- [ ] 创建 `client/src/components/config/SkillsPage.tsx`：
  - 技能卡片网格: 名称 / 描述 / 范围标签 (app/task) / 启用开关
  - 导入功能: 输入 GitHub URL 或本地路径
  - 调用 `skillsApi.importSkill()`

### Step 5.4 — 设置页面

- [ ] 创建 `client/src/components/config/SettingsPage.tsx`：
  - 分组表单布局
  - 默认模型连接选择（下拉框，从模型连接列表中选择）
  - 默认提供商选择
  - API Key 快捷配置（OpenAI / Anthropic）
  - Shell 策略配置
- [ ] **提交 Git**: `feat: implement config pages (Models, MCP, Skills, Settings)`

---

## Phase 6: 动画与交互打磨

### Step 6.1 — Framer Motion 动画

- [ ] 页面切换动画：`AnimatePresence` + 淡入滑动
- [ ] 消息出现动画：从底部滑入 `y: 20 → 0` + 淡入 `opacity: 0 → 1`
- [ ] 状态变更：颜色渐变过渡 `transition: colors 300ms`
- [ ] 加载态：脉冲发光动画（工作流进度中"进行中"节点）
- [ ] 交互反馈：hover 时边框/背景微亮

### Step 6.2 — 自定义窗口标题栏

- [ ] 创建 `client/src/components/layout/TitleBar.tsx`：
  - 可拖拽区域 `-webkit-app-region: drag`
  - 最小化 / 最大化 / 关闭按钮，调用 `window.electronAPI`
  - 居中显示 "AgentLoom" 文字

### Step 6.3 — 响应式细节

- [ ] 窗口缩小时右侧面板自动折叠
- [ ] 任务列表支持拖拽调整宽度（可选）
- [ ] **提交 Git**: `feat: add animations and window title bar`

---

## Phase 7: Electron + Python 进程管理

### Step 7.1 — Python 子进程管理器

- [ ] 创建 `client/electron/python-manager.ts`：
  ```typescript
  import { spawn, ChildProcess } from "child_process";
  import path from "path";

  let pythonProcess: ChildProcess | null = null;

  export function startPythonBackend(): Promise<void> {
    return new Promise((resolve, reject) => {
      // 开发模式: 直接调用 python -m agentloom.api.server
      // 生产模式: 调用 PyInstaller 打包的可执行文件
      const isDev = process.env.NODE_ENV === "development";
      const cmd = isDev ? "python" : path.join(process.resourcesPath, "backend", "agentloom-api.exe");
      const args = isDev ? ["-m", "agentloom.api.server"] : [];

      pythonProcess = spawn(cmd, args, {
        cwd: isDev ? path.resolve(__dirname, "../../") : undefined,
        stdio: ["ignore", "pipe", "pipe"],
      });

      pythonProcess.stdout?.on("data", (data) => {
        if (data.toString().includes("Uvicorn running")) resolve();
      });

      pythonProcess.stderr?.on("data", (data) => {
        console.error("[Python]", data.toString());
      });

      pythonProcess.on("error", reject);

      // 超时 fallback
      setTimeout(resolve, 5000);
    });
  }

  export function stopPythonBackend() {
    pythonProcess?.kill();
    pythonProcess = null;
  }
  ```
- [ ] 在 `electron/main.ts` 中集成：
  ```typescript
  import { startPythonBackend, stopPythonBackend } from "./python-manager";

  app.whenReady().then(async () => {
    await startPythonBackend();
    createWindow();
  });

  app.on("before-quit", () => stopPythonBackend());
  ```

### Step 7.2 — 健康检查

- [ ] 在 FastAPI 添加 `GET /health` 端点
- [ ] 前端启动时轮询 `/health` 直到后端就绪，显示启动加载画面
- [ ] **提交 Git**: `feat: Electron Python process management`

---

## Phase 8: 构建与打包

### Step 8.1 — PyInstaller 后端打包

- [ ] 创建 `scripts/build-backend.py`（或 `.spec` 文件）
- [ ] 打包为单文件可执行程序 `agentloom-api.exe`
- [ ] 输出到 `client/resources/backend/`

### Step 8.2 — Electron Builder 配置

- [ ] 配置 `client/electron-builder.yml`：
  - Windows: NSIS 安装包
  - 打包 `resources/backend/` 目录
  - 应用图标、名称、版本

### Step 8.3 — 端到端验证

- [ ] 构建完整安装包
- [ ] 在干净环境测试安装和运行
- [ ] **提交 Git**: `chore: add build and packaging configuration`

---

## 执行顺序总结

| Phase | 描��� | 依赖 |
|-------|------|------|
| 0 | FastAPI 后端 API 层 | 无（可独立开发测试） |
| 1 | Electron + React 脚手架 | 无（可与 Phase 0 并行） |
| 2 | 前端 API 通信层 | Phase 0 + 1 |
| 3 | 四栏布局 + 导航 | Phase 1 |
| 4 | 群聊对话系统 | Phase 2 + 3 |
| 5 | 配置页面 | Phase 2 + 3 |
| 6 | 动画与交互打磨 | Phase 3 + 4 + 5 |
| 7 | Electron + Python 进程管理 | Phase 0 + 1 |
| 8 | 构建与打包 | 全部完成 |

Phase 0 和 Phase 1 可并行开发。Phase 4 和 Phase 5 可并行开发。
