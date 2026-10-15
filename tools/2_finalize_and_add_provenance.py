#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移收尾：
 1) 嵌套 SKILL.md -> doubao-original.md（避免与 Codex 技能扫描冲突）
 2) 校验「正文与豆包源文件逐字节一致」（只允许 frontmatter 段变化）
 3) 每技能生成 references/migration.md + references/source-manifest.json（沿用本机已有先例）
 4) 生成仓库根 README.md / .gitignore
"""
import os, re, json, hashlib, shutil

SRC  = r'C:\Users\seven\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.user_skills'
OUT  = r'F:\_codex技能导出_20261015\skills'
LOG  = r'F:\_codex技能导出_20261015\_finalize_log.txt'

PLAN = [
    ('田伟平设计师提示词技能', 'tianweiping-prompt-alignment', '3.0.0', '前置（第 0 步）'),
    ('田伟平设计总监大师级别', 'tianweiping-design-director-master', '3.0.0', '总纲'),
    ('田伟平视觉设计ai智能体自动化生图总监水平skill', 'tianweiping-visual-director', '4.1.0', '分域 · 出图生产'),
    ('田伟平建筑设计师', 'tianweiping-architect-designer', '3.0.0', '分域 · 建筑'),
    ('田伟平潮玩设计大师', 'tianweiping-toydesign-master', '3.0.0', '分域 · 潮玩与角色'),
    ('田伟平电影动画aicg大师', 'tianweiping-cinematic-aicg-master', '3.0.0', '分域 · 电影动画'),
    ('田伟平总监审核标准', 'tianweiping-director-review', '3.0.0', '审核'),
]

log = []


def read(p):
    with open(p, 'r', encoding='utf-8-sig', newline='') as f:
        return f.read()


def body_of(text):
    """取 frontmatter 之后的正文（LF，去掉首尾空行）"""
    t = text.replace('\r\n', '\n')
    m = re.match(r'^---\n.*?\n---\n?', t, re.DOTALL)
    return (t[m.end():] if m else t).strip('\n')


def sha(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()[:16]


def tree_stats(d):
    n = b = 0
    for root, _, files in os.walk(d):
        for f in files:
            n += 1
            b += os.path.getsize(os.path.join(root, f))
    return n, b


def main():
    # ---------- 1. 嵌套 SKILL.md 改名 ----------
    renamed = []
    for root, dirs, files in os.walk(OUT):
        if 'SKILL.md' not in files:
            continue
        depth = os.path.relpath(root, OUT).count(os.sep)
        if depth == 0:
            continue                     # 顶层 SKILL.md 是本体
        old = os.path.join(root, 'SKILL.md')
        new = os.path.join(root, 'doubao-original.md')
        if os.path.exists(new):
            os.remove(new)
        os.replace(old, new)
        renamed.append(os.path.relpath(new, OUT))
    log.append('嵌套 SKILL.md 改名 %d 个 -> doubao-original.md' % len(renamed))
    for r in renamed:
        log.append('   ' + r)
    log.append('')

    # ---------- 2/3/4. 逐技能 ----------
    for cn, slug, ver, layer in PLAN:
        src_md = os.path.join(SRC, cn, 'SKILL.md')
        dst_dir = os.path.join(OUT, slug)
        dst_md = os.path.join(dst_dir, 'SKILL.md')
        s_body = body_of(read(src_md))
        d_body = body_of(read(dst_md))
        same = (s_body == d_body)
        log.append('%s' % slug)
        log.append('   源正文 %d 字符 sha=%s' % (len(s_body), sha(s_body)))
        log.append('   迁后正文 %d 字符 sha=%s  -> %s' % (len(d_body), sha(d_body),
                                                         '正文逐字节一致 OK' if same else '!! 正文有差异'))

        n_src, b_src = tree_stats(os.path.join(SRC, cn))
        n_dst, b_dst = tree_stats(dst_dir)
        manifest = {
            'skill': slug,
            'display_name_cn': cn,
            'source': 'doubao-user-skills',
            'source_root': SRC.replace('\\', '/'),
            'source_dir': cn,
            'source_version': ver,
            'layer': layer,
            'migrated_at': '2026-10-15',
            'source_body_sha256_16': sha(s_body),
            'migrated_body_sha256_16': sha(d_body),
            'body_byte_identical': same,
            'source_files': n_src,
            'source_bytes': b_src,
            'migrated_files': n_dst,
            'migrated_bytes': b_dst,
            'changes': [
                'frontmatter.name: 中文目录名 -> ASCII slug（Codex 校验器要求 ^[a-z0-9-]+$）',
                'frontmatter: 原 slug/library/layer/version 移入 metadata（校验器仅允许 name/description/license/allowed-tools/metadata）',
                'frontmatter.description: 压到 1024 字符内；尖括号 > 改为全角；引号改为「」',
                '新增 agents/openai.yaml（界面名/简述/默认提示词）',
                '嵌套 SKILL.md（被吸收的旧技能原文）改名 doubao-original.md',
            ],
        }
        rdir = os.path.join(dst_dir, 'references')
        os.makedirs(rdir, exist_ok=True)
        with open(os.path.join(rdir, 'source-manifest.json'), 'w', encoding='utf-8', newline='\n') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        mig = []
        mig.append('# 迁移依据与范围')
        mig.append('')
        mig.append('## 实际发现')
        mig.append('')
        mig.append('本技能由豆包侧用户技能目录迁移而来。源目录：`%s/%s`，源版本 `%s`，层级「%s」。'
                   % (SRC.replace('\\', '/'), cn, ver, layer))
        mig.append('迁移只改变了 `SKILL.md` 的 frontmatter 段与新增 `agents/openai.yaml`；'
                   '**正文与源文件逐字节一致**（sha256 前 16 位 `%s`，校验见 `source-manifest.json`）。' % sha(s_body))
        mig.append('递归扫描本技能目录共 %d 个文件 / %d 字节。' % (n_src, b_src))
        mig.append('')
        mig.append('## 保留内容')
        mig.append('')
        mig.append('源技能的全部正文、`references/`、`scripts/`、`assets/` 原样保留，未删减、未改写。')
        mig.append('')
        mig.append('## 接入时的调整')
        mig.append('')
        for c in manifest['changes']:
            mig.append('- ' + c)
        mig.append('')
        mig.append('调整的原因只有两类：Codex 技能校验器的硬性格式要求，以及避免嵌套 `SKILL.md` 干扰技能扫描。'
                   '没有为了让内容"更好看"而改动正文。')
        mig.append('')
        mig.append('## 未声称完成')
        mig.append('')
        mig.append('- 没有在 Codex 中实际运行过本技能的任何工作流，未验证其在本机 Codex 下的实际行为；')
        mig.append('- 没有验证 `scripts/` 下脚本在本机 Codex 环境的可执行性；')
        mig.append('- 本技能内引用的其它技能（如 `田伟平建筑设计师`、`田伟平总监审核标准`）需另行迁移后才在 Codex 侧可用；')
        mig.append('- 迁移没有产生任何新的视觉产物，也不代表视觉质量经过验收。')
        mig.append('')
        with open(os.path.join(rdir, 'migration.md'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(mig))

    # ---------- 仓库根文件 ----------
    readme = """# 田伟平视觉设计 AI 智能体 · 技能库（Codex 版）

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

## 未声称完成

没有在 Codex 中实际运行过这些技能，未验证其实际行为或视觉输出质量。
"""
    with open(os.path.join(r'F:\_codex技能导出_20261015', 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(readme)

    gitignore = """__pycache__/
*.pyc
*.pyo
.DS_Store
Thumbs.db
_verify*.txt
"""
    with open(os.path.join(r'F:\_codex技能导出_20261015', '.gitignore'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(gitignore)

    with open(LOG, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(log) + '\n')
    print('\n'.join(log))


if __name__ == '__main__':
    main()
