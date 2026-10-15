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

## 推送到 GitHub（未执行）

本地仓库已 `git init` 并提交，分支 `master`。**尚未创建远程仓库、尚未推送。**

首次推送需要一次 GitHub 登录（本机没有任何 git 凭据）：

```powershell
cd F:\_codex技能导出_20261015
.\一键推送到GitHub.ps1 -Repo tianweiping-visual-skills
```

脚本会打开 GitHub 新建仓库页面，你建好仓库后回车，Git Credential Manager
会弹出登录窗口，登录一次即可。

> 注意：GitHub 的 `create_or_update_file` / `push_files` 接口只接受文本 `content`
> （官方接口原文写明「Do not base64-encode it」），**二进制图片会被破坏**，
> 所以 26 张案例图（8.49 MB）只能走 git 推送，不能走 API。
> 这也是没有把仓库拆成「纯文本快照」的原因。

## 未声称完成

- 没有在 Codex 中实际运行过这些技能，未验证其在本机的实际行为或视觉输出质量；
- 没有验证各技能 `scripts/` 下脚本在 Codex 环境的可执行性；
- 没有创建 GitHub 远程仓库，没有推送（本地提交已完成）。
