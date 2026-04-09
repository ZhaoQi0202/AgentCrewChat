# 文档索引

| 文件 | 内容 |
|------|------|
| [product.md](./product.md) | **主规格单**：产品定位、Agent 角色、四阶段流程、功能清单、实现索引、已知差距 |
| [frontend.md](./frontend.md) | 客户端界面风格、布局、组件约定、Electron 规范 |
| [backend.md](./backend.md) | 后端分层、LLM 配置、执行规范、安全与路径约定 |

## 实现规格（Batch 分期）

| Batch | 文件 | 范围 | 状态 |
|-------|------|------|------|
| Batch 1 | [batch1-agent-identity-llm-design.md](./superpowers/specs/2026-04-09-batch1-agent-identity-llm-design.md) | F-03/F-07/G1/G5：Agent 身份系统、四阶段 LLM 分配、工具注册对齐 | **已完成** |
| Batch 2 | [batch2-executor-personality-chat-history-panel.md](./superpowers/specs/2026-04-09-batch2-executor-personality-chat-history-panel.md) | F-08/F-09/F-10/F-11：执行 Agent 个性、@主题色渲染、聊天持久化、右侧面板 | 待执行 |
| Batch 3 | [batch3-execution-control.md](./superpowers/specs/2026-04-09-batch3-execution-control.md) | F-12/F-13/F-14/G2/G3：暂停、审核超限选项卡、局部重规划 | 待执行 |
| Batch 4 | [batch4-packaging-and-polish.md](./superpowers/specs/2026-04-09-batch4-packaging-and-polish.md) | F-15/F-16/G4：安装包、Skills 开关、WS 断线续跑 | 待执行 |

**AI 开发规则**：对话中新定案的结论，直接写入上面对应文件的相关小节，不要只留在对话里。
