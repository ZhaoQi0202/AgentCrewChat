# 客户端规范（界面风格与实现约定）

**技术栈**：React 19、TypeScript、Vite、Tailwind CSS v4、Framer Motion、lucide-react、Electron

---

## 1. 视觉规范

### 1.1 整体风格

- **浅色玻璃态**：面板使用 `globals.css` 中的 `.glass` / `GlassCard`，白紫半透明 + 细紫边 + 轻模糊
- 禁止大面积随意纯色块

### 1.2 颜色

- **只用设计令牌**：使用 Tailwind 映射（如 `bg-bg-base`、`text-text-primary`、`border-border-subtle`、`gradient-brand`），**禁止**在组件里写死 `#hex`
- **品牌色**：紫 `#8b5cf6`、蓝 `#3b82f6`；渐变只做强调（按钮、小徽标、描边），不要整屏渐变
- **文字层级**：primary / body / secondary / muted，与现有一致
- **状态色**：`status-success | status-warning | status-error | status-info`

### 1.3 形状与字体

- **圆角**：卡片级约 12px（`rounded-xl` / `--radius-card`）；小控件 8px（`--radius-sm`）
- **字体**：沿用 body 栈（Inter、PingFang SC、Microsoft YaHei 等），聊天与配置页统一，不单独换字体族

---

## 2. 布局结构

- **禁止拆 `App.tsx` 骨架**：顶栏 `TitleBar`（`h-8`、`drag-region`，按钮加 `no-drag`）→ 下为 `IconSidebar`（`w-14`）+ 可选 `TaskList` + `main` + 右侧面板
- **滚动**：仅内部区域滚动，`body` 已 `overflow: hidden`
- **图标**：统一 lucide-react，线风格，尺寸与侧栏现有条目一致

---

## 3. 组件约定

### 3.1 通用

- 可点击卡片：`GlassCard` 或 `glass` + `glass-hover`
- **主按钮**：`gradient-brand` + 白字
- **次按钮**：浅底 + 默认边框
- **动效**：150–250ms；页面切换用短 `opacity` / `x`；聊天列表不要每行持续脉冲动画
- **品牌缩写徽标**：`AC`（不用 `AL`）

### 3.2 聊天消息气泡

- Agent 消息：左侧头像（圆形，渐变背景）+ 名称（主题色）+ 时间戳 + 气泡（白色半透明）
- 工具调用消息：琥珀色气泡，等宽字体，区分于普通输出
- 用户消息：右对齐
- 系统消息（阶段切换、Agent 入群）：居中小字
- HITL 卡片：单独组件，含确认/反馈输入
- **`@名称` 渲染规则**：解析消息内容中的 `@名称`，**只匹配已知 Agent 名字列表**（晓柔、明哲、铁口 + 当前项目组的动态执行 Agent 名），用对应 Agent 主题色高亮渲染，不使用通用正则

### 3.3 右侧状态面板（重构方案）

- **重构现有 RightPanel**，将「工作流进度」区域改为四阶段分栏卡片设计
- 四阶段分栏卡片，每栏对应一个阶段（需求收集 / 架构规划 / 执行 / 审核）
- 卡片内展示该阶段 Agent 的头像 + 名称（使用中文名：晓柔/明哲/铁口/小某）
- 执行阶段按实际拆分的 Agent 数量动态展示
- 每个 Agent 右上角状态点：灰（未开始）/ 黄脉冲（进行中）/ 绿（已完成）/ 红（有问题）

### 3.4 审核超限交互

- 铁口的超限说明消息在群聊中正常显示为 `agent_output` 气泡
- 用户输入框区域显示**三个快捷回复按钮**：`跳过继续` / `交还明哲` / `终止执行`
- 快捷按钮点击后直接发送对应文本，同时隐藏按钮
- 用户也可忽略按钮，直接在输入框输入自由文本回复

### 3.5 设置页 — 四阶段 LLM 分配

- 在 SettingsPage 中新增「阶段模型分配」区域
- 布局：**四行下拉框**，每行左侧为阶段名（需求收集 / 架构规划 / 执行 / 审核），右侧为已配置的模型连接下拉选择器
- 每个下拉框默认选项为「跟随默认」（使用全局默认连接）
- 下拉选项列表来自已配置的模型连接（ModelsPage 中的条目）

---

## 4. Electron 相关

- 依赖 `window.electronAPI` 的 UI 需判断存在再渲染
- 浏览器访问走拦截页逻辑（`BrowserBlocked.tsx`），除非 `VITE_ALLOW_BROWSER=true`
- 标题栏拖拽区（`drag-region`）不可被新组件破坏

---

## 5. AI 做界面自检

完成界面开发后自检以下几点：

- [ ] 无新裸色值（无 `#hex` 硬编码）
- [ ] 新面板走 glass 风格
- [ ] 未破坏标题栏拖拽区
- [ ] 文案与 AgentCrewChat 命名一致（品牌缩写用 `AC`）
- [ ] `@名称` 渲染使用对应 Agent 主题色
- [ ] 聊天气泡中无裸 JSON

---

## 6. 路径速查

| 区域 | 路径 |
|------|------|
| 群聊 UI | `client/src/components/chat/` |
| 右侧状态面板 | `client/src/components/layout/RightPanel.tsx` |
| 配置页面 | `client/src/components/config/` |
| 状态与请求 | `client/src/stores/`、`client/src/services/` |
| 设计令牌 | `client/src/styles/globals.css` |
| Agent 元数据 | `client/src/types/` 中的 `AGENT_META` |
| Electron 壳 | `client/electron/python-manager.cjs`、`client/src/main.tsx` |
