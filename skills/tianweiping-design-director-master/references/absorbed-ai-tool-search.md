---
name: taaft-ai-tool-search
description: TAAFT AI工具搜索引擎。搜索AI工具、MCP服务器、AI模型、公司、开发者、产品对比。触发词：找AI工具、AI推荐、有什么AI、搜AI、TAAFT、AI工具对比。
---

# TAAFT AI工具搜索

## 基本信息
- 名称：There's An AI For That
- 端点：https://theresanaiforthat.com/mcp-server/
- 认证：无需认证
- 协议：Streamable HTTP
- 限制：30次/分钟，1000次/天

## 可用工具（28个）

### 搜索类
| 分类 | 搜索工具 | 详情工具 |
|---|---|---|
| AI工具 | search_tools | get_tool |
| MCP服务器 | search_mcps | get_mcp |
| 任务/场景 | search_tasks | get_task |
| AI模型 | search_models | get_model |
| 公司 | search_companies | get_company |
| 机器人 | search_robots | get_robot |
| 设备 | search_devices | get_device |
| 组织 | search_organizations | get_organization |
| 投资人 | search_investors | get_investor |
| 国家 | search_countries | get_country |
| 活动 | search_events | get_event |
| 融资轮次 | search_fundraises | get_fundraise |
| 论文 | search_papers | get_paper |
| 代码仓库 | search_repositories | get_repository |

## 使用方法
1. 用户问"有什么AI工具做XX" → 用search_tools
2. 用户问"这个AI工具怎么样" → 用get_tool
3. 用户问"有什么MCP服务器" → 用search_mcps
4. 返回结果时保留原始URL和推荐理由

## 适用场景
- 找免费AI工具
- 找视频生成/图片生成/写作工具
- 对比同类AI产品
- 发现新出的AI工具
