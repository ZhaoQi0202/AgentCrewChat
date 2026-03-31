# AgentLoom 客户端 UI 重设计规格

## 概述

将 AgentLoom 从 PySide6 原生桌面应用迁移为 Electron + React 前端，实现现代 SaaS 风格的玻璃拟态深色 UI，以"多 Agent 群聊"为核心交互范式。

## 设计目标

- 视觉上达到产品级品质（玻璃拟态深色风，参考 Arc Browser / Warp Terminal）
- 交互逻辑清晰直观，消除当前"开发者工具"感
- 以对话流自然呈现多 Agent 协作的五阶段工作流
- 保持桌面客户端形态，本地数据隔离

## 语言规范

- **初版仅支持中文界面**
- 专业术语保留英文原文，包括但不限于：token、key、URL、API、Agent、MCP、WebSocket、Blueprint 等
- 示例：「模型连接管理」「API Key: sk-...7f2a」「新建任务」

## 技术架构

### 整体架构

```
Electron Shell
├── React SPA (Renderer Process)
│   ├── UI Framework: React 18 + TypeScript
│   ├── Styling: Tailwind CSS + 自定义深色玻璃拟态主题
│   ├── Components: shadcn/ui (深度定制样式)
│   ├── State: Zustand
│   ├── Animation: Framer Motion
│   └── 通信: WebSocket (实时事件) + HTTP (REST API)
│
├── Electron Main Process
│   ├── 启动/管理 Python 子进程
│   ├── 系统级操作 (文件系统、窗口管理、托盘)
│   └── IPC 桥接
│
└── Python Backend (FastAPI)
    ├── WebSocket: Agent 事件实时推送
    ├── REST API: CRUD (任务/模型/MCP/技能/设置)
    ├── LangGraph 状态机 + SQLite 持久化
    └── 本地环境调用 (文件系统、命令执行)
```

### 通信协议

- **WebSocket**: Agent 实时事件流（阶段变更、Agent 消息、HITL 中断、错误等）
- **REST API**: 配置管理 CRUD（模型连接、MCP 服务器、技能、任务管理）
- **Electron IPC**: 系统级操作（窗口控制、文件对话框、托盘菜单）

### Python 后端打包

Electron Main Process 通过 `child_process.spawn` 启动 PyInstaller 打包的 Python 可执行文件，或内嵌 Python runtime。通信走 localhost HTTP/WebSocket。

## 视觉风格

### 玻璃拟态深色风 (Glassmorphism Dark)

- **背景**: 深色底 `#09090f` ~ `#13131a`，极低明度
- **表面层**: `rgba(255,255,255,0.02~0.04)` 半透明，`backdrop-filter: blur()`
- **边框**: `rgba(255,255,255,0.06~0.08)` 微光边框
- **渐变光效**: 紫蓝渐变 `#8b5cf6 → #3b82f6` 用于品牌色和强调元素
- **圆角**: 大圆角 `10px~14px`
- **文字层级**:
  - 主标题: `#e4e4e7`
  - 正文: `#d4d4d8`
  - 次要: `#a1a1aa`
  - 辅助: `#71717a`
  - 禁用: `#52525b` / `#3f3f46`
- **状态色**:
  - 运行中/成功: `#22c55e` (绿)
  - 等待/警告: `#fbbf24` (黄)
  - 活跃/品牌: `#8b5cf6` (紫)
  - 信息: `#3b82f6` / `#60a5fa` (蓝)
  - 错误: `#ef4444` (红)

### 动画

- 页面切换: `Framer Motion` 淡入滑动
- 消息出现: 从底部滑入 + 淡入
- 状态变更: 颜色渐变过渡
- 加载态: 脉冲发光动画
- 交互反馈: hover 时边框/背景微亮

## 页面结构

### 整体布局：经典 SaaS 四栏

```
┌──────┬───────────┬──────────────────────┬──────────┐
│ 图标 │ 任务列表  │      主区域          │  右侧    │
│ 侧栏 │ / 配置   │  (对话 / 配置页面)    │  面板    │
│      │  列表     │                      │          │
│      │           │                      │          │
│ 56px │  240px    │     flex: 1          │  260px   │
└──────┴───────────┴──────────────────────┴──────────┘
```

### Column 1: 图标侧栏 (56px)

固定在最左侧，垂直排列：

- **顶部**: AgentLoom Logo（紫蓝渐变圆角方块 + 白色字母 "A"）
- **导航图标**（从上到下）:
  - 任务工作区 — 四格网格图标
  - 模型管理 — 太阳/齿轮图标
  - MCP 服务器 — 插件/连接图标
  - 技能管理 — 星形图标
- **底部**: 设置 — 齿轮图标
- **激活态**: 紫色背景 + 左侧 3px 紫色指示条

### Column 2: 任务列表 (240px)

仅在「任务工作区」导航激活时显示。切换到其他页面时此列隐藏，主区域扩展。

- **顶部**: 搜索框（玻璃态背景 + 搜索图标），placeholder: "搜索任务..."
- **新建任务按钮**: 紫蓝渐变边框，居中文字 "+ 新建任务"
- **任务列表项**:
  - 激活任务: 紫色背景高亮 + 左侧状态圆点（绿=运行中，蓝=等待中，空心=未开始，绿+删除线=已完成）
  - 显示: 任务名称、当前阶段标签、最后更新时间
  - 点击切换主区域内容

### Column 3: 主区域 (flex: 1)

#### 任务工作区模式

##### 顶部信息栏
- 任务名称（大字体加粗）
- 状态标签（运行中 / 已暂停 / 已完成）
- 操作按钮：运行图谱、继续（玻璃态按钮）

##### 对话区（核心交互 — "群聊"模式）

所有 Agent 活动和人机交互在同一条时间线上展示：

1. **系统消息**（居中小标签）:
   - 任务启动: "任务已启动 · 阶段 1: Consultant"
   - 阶段切换: "→ 阶段 2: Architect"
   - 任务完成: "任务完成 · 5 个阶段 · 耗时 3 分 20 秒"

2. **Agent 消息卡片**（左对齐，带头像）:
   - 圆形头像（每个 Agent 独立渐变色）
   - Agent 名称（对应颜色）+ 时间戳
   - 消息气泡（玻璃态背景，左上角小圆角）
   - Agent 接收任务时发消息说明工作内容
   - Agent 完成任务时发消息汇报结果

3. **HITL 中断卡片**（黄色主题警告框）:
   - 暂停图标 + "需要人工审核"
   - 说明文字描述需要人工做什么
   - 等待用户在输入框回复

4. **用户消息**（右对齐）:
   - 用户头像 + 消息气泡（略带紫色调）

##### 底部输入区
- 玻璃态输入框 + 发送按钮（紫蓝渐变圆角方块 + 发送图标）
- Placeholder: "输入消息与 Agent 对话..."

#### 配置页面模式（模型/MCP/技能页面激活时）

任务列表列隐藏，主区域扩展为全宽配置页面：

- **页面标题** + **添加按钮**（紫蓝渐变边框）
- **卡片网格布局**（2 列 grid），每张卡片:
  - 品牌图标 + 名称 + 型号/描述
  - 连接状态（绿色圆点 + "已连接"）
  - 标签（默认 / 备用 等）
  - 操作按钮（测试 / 编辑 / 删除）
- **虚线占位卡片**引导添加新项

### Column 4: 右侧面板 (260px)

仅在「任务工作区」导航激活时显示：

#### 工作流进度
- 五阶段垂直时间线
- 每个阶段: 圆形图标 + 名称 + 状态文字
- 连线颜色: 已完成=绿色，当前=黄色脉冲，未开始=灰色
- 阶段状态:
  - 已完成: 绿色对勾 + 耗时
  - 进行中: 黄色脉冲圆点 + "等待审核" / "运行中..."
  - 未开始: 灰色序号

#### 活跃 Agent
- Agent 卡片列表
- 每张: 渐变头像 + 名称 + 状态（活跃 / 已完成 / 等待中）

#### 任务信息
- 键值对列表: 创建时间、使用模型、技能数量 等

## 页面清单

| 页面 | 侧栏图标 | 描述 |
|------|----------|------|
| 任务工作区 | 任务 | 四栏布局，群聊式 Agent 交互 |
| 模型管理 | 模型 | 模型连接管理，卡片网格 |
| MCP 服务器 | MCP | MCP 服务器配置，卡片网格 |
| 技能管理 | 技能 | 技能管理，卡片网格 + 导入 |
| 设置 | 设置 | 通用设置，分组表单 |

## Agent 对话流事件类型

WebSocket 推送的事件映射为对话流中的不同消息类型：

| 事件类型 | 对话流展示 |
|----------|-----------|
| `phase_start` | 系统消息: "→ 阶段 N: AgentName" |
| `agent_thinking` | Agent 消息气泡 + 打字动画 |
| `agent_output` | Agent 消息卡片（完整内容） |
| `hitl_interrupt` | 黄色 HITL 中断卡片 |
| `user_response` | 用户消息（右对齐） |
| `phase_complete` | Agent 消息: "已完成，结果如下..." |
| `task_complete` | 系统消息: "任务完成" |
| `error` | 红色错误卡片 |

## 各 Agent 视觉标识

| Agent | 头像渐变 | 名称颜色 | Emoji |
|-------|---------|---------|-------|
| Consultant | `#8b5cf6 → #6366f1` | `#c4b5fd` | 🔍 |
| Architect | `#3b82f6 → #06b6d4` | `#93c5fd` | 📐 |
| HITL Blueprint | `#f59e0b → #f97316` | `#fcd34d` | ⏸ |
| Expert (Swarm) | `#22c55e → #10b981` | `#86efac` | ⚡ |
| Reviewer | `#ec4899 → #f43f5e` | `#f9a8d4` | 🔎 |

## 交互规则

1. **任务切换**: 点击左侧任务列表切换当前任务，主区域加载对应对话历史
2. **新建任务**: 点击 "+ 新建任务"，弹出轻量输入框（不是模态对话框），输入任务描述后立即创建
3. **运行图谱**: 点击「运行图谱」启动当前任务的 LangGraph 执行
4. **继续执行**: HITL 中断后，用户在输入框输入反馈，点击发送即相当于"继续"
5. **配置页面导航**: 点击侧栏图标切换到对应配置页面，任务列表和右侧面板隐藏
6. **返回任务**: 点击任务图标回到任务工作区

## 目录结构（前端）

```
client/
├── package.json
├── electron/
│   ├── main.ts              # Electron 主进程
│   ├── preload.ts            # 预加载脚本
│   └── python-manager.ts     # Python 子进程管理
├── src/
│   ├── main.tsx              # React 入口
│   ├── App.tsx               # 路由 + 全局布局
│   ├── styles/
│   │   └── globals.css       # Tailwind + 自定义主题变量
│   ├── components/
│   │   ├── ui/               # shadcn/ui 定制组件
│   │   ├── layout/
│   │   │   ├── IconSidebar.tsx
│   │   │   ├── TaskList.tsx
│   │   │   └── RightPanel.tsx
│   │   ├── chat/
│   │   │   ├── ChatArea.tsx
│   │   │   ├── AgentMessage.tsx
│   │   │   ├── UserMessage.tsx
│   │   │   ├── SystemMessage.tsx
│   │   │   ├── HITLCard.tsx
│   │   │   └── ChatInput.tsx
│   │   ├── config/
│   │   │   ├── ModelsPage.tsx
│   │   │   ├── McpPage.tsx
│   │   │   ├── SkillsPage.tsx
│   │   │   └── SettingsPage.tsx
│   │   └── shared/
│   │       ├── AgentAvatar.tsx
│   │       ├── StatusBadge.tsx
│   │       └── GlassCard.tsx
│   ├── stores/
│   │   ├── taskStore.ts
│   │   ├── chatStore.ts
│   │   └── configStore.ts
│   ├── services/
│   │   ├── api.ts            # REST API 客户端
│   │   └── websocket.ts      # WebSocket 事件管理
│   └── types/
│       └── index.ts          # TypeScript 类型定义
└── electron-builder.yml      # 打包配置
```

## 不在范围内

- 多语言/国际化（初版仅中文，专业术语保留英文）
- 多窗口支持
- 插件/扩展系统
- 用户账号/登录系统
- 云同步
- Blueprint 可视化编辑器（后续迭代）
- Expert Swarm 并行执行详情面板（后续迭代）
