# 迁移依据与范围

## 实际发现

本技能由豆包侧用户技能目录迁移而来。源目录：`C:/Users/seven/AppData/Local/Doubao/User Data/Default/.doubao/agent_mode/workspace/.user_skills/田伟平视觉设计ai智能体自动化生图总监水平skill`，源版本 `4.1.0`，层级「分域 · 出图生产」。
迁移只改变了 `SKILL.md` 的 frontmatter 段与新增 `agents/openai.yaml`；**正文与源文件逐字节一致**（sha256 前 16 位 `abfde78498c2b908`，校验见 `source-manifest.json`）。
递归扫描本技能目录共 43 个文件 / 1902548 字节。

## 保留内容

源技能的全部正文、`references/`、`scripts/`、`assets/` 原样保留，未删减、未改写。

## 接入时的调整

- frontmatter.name: 中文目录名 -> ASCII slug（Codex 校验器要求 ^[a-z0-9-]+$）
- frontmatter: 原 slug/library/layer/version 移入 metadata（校验器仅允许 name/description/license/allowed-tools/metadata）
- frontmatter.description: 压到 1024 字符内；尖括号 > 改为全角；引号改为「」
- 新增 agents/openai.yaml（界面名/简述/默认提示词）
- 嵌套 SKILL.md（被吸收的旧技能原文）改名 doubao-original.md

调整的原因只有两类：Codex 技能校验器的硬性格式要求，以及避免嵌套 `SKILL.md` 干扰技能扫描。没有为了让内容"更好看"而改动正文。

## 未声称完成

- 没有在 Codex 中实际运行过本技能的任何工作流，未验证其在本机 Codex 下的实际行为；
- 没有验证 `scripts/` 下脚本在本机 Codex 环境的可执行性；
- 本技能内引用的其它技能（如 `田伟平建筑设计师`、`田伟平总监审核标准`）需另行迁移后才在 Codex 侧可用；
- 迁移没有产生任何新的视觉产物，也不代表视觉质量经过验收。
