# 田伟平视觉设计 AI 智能体 · 技能库（Codex 版）

由豆包侧「田伟平视觉技能库」迁移而来的 7 个 Codex 技能。

## 技能清单

| Codex 技能名 | 中文名 | 层级 | 源版本 |
|---|---|---|---|
| `tianweiping-prompt-alignment` | 田伟平设计师提示词技能 | 前置（第 0 步） | 3.0.0 |
| `tianweiping-design-director-master` | 田伟平设计总监大师级别 | 总纲 | 3.0.0 |
| `tianweiping-visual-director` | 田伟平视觉设计ai智能体自动化生图总监水平skill | 分域 · 出图生产 | 4.1.0 |
| `tianweiping-architect-designer` | 田伟平建筑设计师 | 分域 · 建筑 | 3.0.0 |
| `tianweiping-toydesign-master` | 田伟平潮玩设计大师 | 分域 · 潮玩与角色 | 3.0.0 |
| `tianweiping-cinematic-aicg-master` | 田伟平电影动画aicg大师 | 分域 · 电影动画 | 3.0.0 |
| `tianweiping-director-review` | 田伟平总监审核标准 | 审核 | 3.0.0 |

## 安装

把 `skills/` 下的 7 个目录复制到 `$CODEX_HOME/skills`（未设置时为 `~/.codex/skills`）。

## 迁移做了什么

- `frontmatter.name`：中文目录名 → ASCII slug（Codex 校验器要求 `^[a-z0-9-]+$`）
- 原 `slug` / `library` / `layer` / `version` 键移入 `metadata`（校验器只允许 `name` / `description` / `license` / `allowed-tools` / `metadata`）
- `description` 压到 1024 字符内、去掉尖括号
- 新增 `agents/openai.yaml`
- 被吸收的旧技能原文（嵌套 `SKILL.md`）改名 `doubao-original.md`

**正文与豆包源文件逐字节一致**，逐技能 sha256 记录在各自的
`references/source-manifest.json`，说明见 `references/migration.md`。

## 验证

```bash
python "$CODEX_HOME/skills/.system/skill-creator/scripts/quick_validate.py" skills/<skill-name>
```

## 仓库状态

此技能库已同步到两个 GitHub 仓库：

- 公开仓库：<https://github.com/seven8595/tianweipi-visual-skills>（默认分支 `main`）
- 私有仓库：<https://github.com/seven8595/tianweiping-visual-skills>（默认分支 `master`）

本次核对时，两边 HEAD 均为 `f547b3bb4d0c87283a5423ea053b407e5d476437`，文件路径集合与全部文件 blob SHA 一致。该结论只表示当前检查到的版本内容一致。

## 公开发布范围

仓库公开后，其中的技能正文、迁移原文、引用资料、配置、脚本和图片均可被任何人查看和下载。公开前请逐项确认：

- 图片、示例、角色或客户项目材料允许公开展示和再分发；
- 文档中提及的本地路径、设备、项目名称、工作流和账号信息可公开；
- 配置及脚本不包含凭据、个人数据或不应公开的内部操作细节。

目前仓库包含本机路径、项目名称/工作流信息、微信命名图片以及若干案例和参考图片。仓库内容本身不能证明这些材料的授权范围；需要素材权利人或资料负责人确认后，才能将其视为已获公开授权。公开仓库的修订提交也无法抹除既有 Git 历史或外部克隆。

### GitHub 推送脚本提示

`一键推送到GitHub.ps1` 面向本地仓库使用。它会在存在未提交变更时执行 `git add -A` 并尝试提交，运行前先检查工作树；不要把不准备发布的文件留在其中。

## 验证状态\n\n- README 中提供了 Codex 技能快速校验命令，但仓库没有记录这些技能后来是否在 Codex 中实际运行。\n- 尚无证据确认各技能脚本在目标 Codex/Windows 环境执行通过。请先按技能逐项运行快速校验，再对会访问本地服务、上传素材或更改系统设置的脚本单独做安全审阅和受控测试。\n- 上述内容状态以本次仓库检查为准；静态浏览不等同于运行验证。\n