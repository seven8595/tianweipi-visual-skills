---
name: agent-radar
description: Agent Radar AI工具评分推荐库。搜索AI工具、查看详细评分卡、获取任务匹配推荐、了解风险和权限。比TAAFT更专业，带证据和评分。触发词：AI工具评分、AI推荐、哪个AI好用、AI工具风险、Agent Radar。
---

# Agent Radar AI工具评分推荐

## 基本信息
- 名称：Agent Radar
- 端点：https://agent-radar.zation1.workers.dev/api/mcp
- 认证：可选（recommend_tools需要API key）
- 协议：Streamable HTTP

## 核心能力

### 4个工具
| 工具 | 功能 |
|---|---|
| search_tools | 搜索AI工具/Agent/Skill/MCP/CLI/框架 |
| get_tool_card | 查看工具详细评分卡（功能/限制/权限/风险） |
| recommend_tools | 根据任务推荐最合适的工具 |
| explain_rating | 解释评分理由 |

### 推荐结果类型
| 标记 | 含义 |
|---|---|
| use | 可以用，有边界 |
| compare | 多个选项需要对比 |
| ask_human | 需要人确认权限/账号/生产环境 |
| avoid | 安全/质量问题不建议 |
| no_reliable_match | 没有可靠匹配 |

## 评分维度
- 任务匹配度
- 维护活跃度
- 文档质量
- 集成成本
- 安全风险
- 证据质量

## 与TAAFT区别
- TAAFT：大而全的AI工具目录，偏搜索发现
- Agent Radar：带评分和风险评估，偏决策推荐

## 使用场景
- 选AI工具做具体任务
- 评估某个AI工具靠不靠谱
- 了解工具权限和安全风险
- 对比多个AI工具哪个适合
