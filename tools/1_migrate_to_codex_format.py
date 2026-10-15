#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把豆包侧的「田伟平」主技能迁移成 Codex 技能格式。
规则来自 C:\\Users\\seven\\.codex\\skills\\.system\\skill-creator\\
  1. name 必须 ^[a-z0-9-]+$  -> 用原 frontmatter 的 slug
  2. frontmatter 只允许 name/description/license/allowed-tools/metadata
     -> 原 slug/library/layer/version 收进 metadata
  3. description <= 1024 字符，且不得含 < 或 >
  4. 文件行尾必须 LF
  5. 生成 agents/openai.yaml
不修改任何源文件；全部输出到 OUT。
"""
import os, re, shutil, sys, json, unicodedata

SRC = r'C:\Users\seven\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.user_skills'
OUT = r'F:\_codex技能导出_20261015\skills'
LOG = r'F:\_codex技能导出_20261015\_build_log.txt'

# (豆包目录名, codex slug, 界面中文名, codex 默认提示词)
PLAN = [
    ('田伟平设计师提示词技能', 'tianweiping-prompt-alignment', '田伟平设计师提示词对齐',
     '使用 $tianweiping-prompt-alignment，先把这次设计任务的 brief 按四句公式补全，再动手。'),
    ('田伟平设计总监大师级别', 'tianweiping-design-director-master', '田伟平设计总监总纲',
     '使用 $tianweiping-design-director-master，判断这个视觉任务该走哪个分域、用哪套标准。'),
    ('田伟平视觉设计ai智能体自动化生图总监水平skill', 'tianweiping-visual-director', '田伟平自动化生图总监',
     '使用 $tianweiping-visual-director，把这句话需求转成可执行的出图方案并本地出图。'),
    ('田伟平建筑设计师', 'tianweiping-architect-designer', '田伟平建筑设计师',
     '使用 $tianweiping-architect-designer，按建筑 6 步管线做建筑/室内视觉。'),
    ('田伟平潮玩设计大师', 'tianweiping-toydesign-master', '田伟平潮玩设计大师',
     '使用 $tianweiping-toydesign-master，做角色 IP / 潮玩 / 插画视觉。'),
    ('田伟平电影动画aicg大师', 'tianweiping-cinematic-aicg-master', '田伟平电影动画AIGC大师',
     '使用 $tianweiping-cinematic-aicg-master，做电影感画面、动画电影或漫剧视觉。'),
    ('田伟平总监审核标准', 'tianweiping-director-review', '田伟平总监审核标准',
     '使用 $tianweiping-director-review，按 12 维 checklist 审这一稿并给出 SMART REPAIR。'),
]

SKIP_DIRS = {'__pycache__', '.git', '_reference_pack'}  # _reference_pack 走单独判断
DESC_BUDGET = 980   # 留余量，硬上限 1024


def read_text(p):
    with open(p, 'r', encoding='utf-8-sig', newline='') as f:
        return f.read()


def norm_lf(s):
    return s.replace('\r\n', '\n').replace('\r', '\n')


def split_frontmatter(text):
    """返回 (frontmatter_text, body, ok)"""
    if not text.startswith('---\n'):
        return None, text, False
    m = re.match(r'^---\n(.*?)\n---\n?', text, re.DOTALL)
    if not m:
        return None, text, False
    return m.group(1), text[m.end():], True


def get_scalar(fm, key):
    """从 frontmatter 取标量键值（只处理 key: value 单行）"""
    for line in fm.split('\n'):
        m = re.match(r'^' + re.escape(key) + r'\s*:\s*(.+)$', line.strip())
        if m and not m.group(1).strip().startswith('>'):
            return m.group(1).strip().strip('"').strip("'")
    return None


def get_block(fm, key):
    """取 `key: >` 折叠块的正文"""
    lines = fm.split('\n')
    out, hit = [], False
    for line in lines:
        if not hit:
            if re.match(r'^\s*' + re.escape(key) + r'\s*:\s*>', line):
                hit = True
                rest = re.sub(r'^\s*' + re.escape(key) + r'\s*:\s*>[-+]?\s*', '', line)
                if rest.strip():
                    out.append(rest)
            continue
        if re.match(r'^\S+\s*:', line):   # 下一个顶层键
            break
        out.append(line)
    return '\n'.join(out) if hit else None


def sanitize_desc(txt):
    """折叠成单行；去掉 YAML/校验器不接受的字符"""
    t = norm_lf(txt)
    t = re.sub(r'[ \t]+', ' ', t)
    t = t.replace('\n', ' ')
    t = re.sub(r'\s{2,}', ' ', t).strip()
    # 校验器禁止尖括号
    t = t.replace(' > ', ' 优于 ').replace('>', '＞').replace('<', '＜')
    t = t.replace('**', '')            # description 里不留 markdown 星号
    # 成对引号：左引号→「，右引号→」（不要两边都换成「）
    t = t.replace('\u201c', '「').replace('\u201d', '」')
    t = t.replace('\u2018', '『').replace('\u2019', '』')
    return t


def clip_desc(t, budget=DESC_BUDGET):
    """超长时在「触发词」前保留定位句，触发词按逗号截断"""
    if len(t) <= budget:
        return t, False
    marker = '触发词：'
    if marker in t:
        head, tail = t.split(marker, 1)
        head = head.rstrip()
        # 触发词按 顿号/逗号 切，逐段加直到接近预算
        parts = [p for p in re.split(r'[，、]', tail) if p.strip()]
        keep, cur = [], head + marker
        for p in parts:
            cand = cur + ('，' if keep else '') + p
            if len(cand) + 6 > budget:
                break
            cur = cand
            keep.append(p)
        return cur + '（其余触发词见正文）', True
    # 没有触发词标记：按句号截
    cut = t[:budget]
    idx = max(cut.rfind('。'), cut.rfind('；'))
    if idx > budget * 0.5:
        return cut[:idx + 1], True
    return cut, True


def main():
    log = []
    os.makedirs(OUT, exist_ok=True)
    for cn, slug, disp, prompt in PLAN:
        src = os.path.join(SRC, cn)
        dst = os.path.join(OUT, slug)
        if not os.path.isdir(src):
            log.append('缺失源目录: %s' % cn)
            continue
        if os.path.exists(dst):
            shutil.rmtree(dst)
        # 复制整棵目录（排除缓存）
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        md = os.path.join(dst, 'SKILL.md')
        fm, body, ok = split_frontmatter(norm_lf(read_text(md)))
        if not ok:
            log.append('frontmatter 解析失败: %s' % cn)
            continue
        orig_slug = get_scalar(fm, 'slug') or slug
        library = get_scalar(fm, 'library') or ''
        layer = get_scalar(fm, 'layer') or ''
        version = get_scalar(fm, 'version') or ''
        if orig_slug != slug:
            log.append('! slug 不一致 %s -> %s (原 %s)' % (cn, slug, orig_slug))
        raw_desc = get_block(fm, 'description') or ''
        desc = sanitize_desc(raw_desc)
        desc, clipped = clip_desc(desc)
        short = re.split(r'。', desc)[0][:78]

        # 逐行写回（显式 LF）
        lines = []
        lines.append('---')
        lines.append('name: %s' % slug)
        lines.append('description: >-')
        lines.append('  %s' % desc)
        lines.append('metadata:')
        lines.append('  display_name_cn: "%s"' % cn)
        lines.append('  original_slug: %s' % orig_slug)
        if library:
            lines.append('  library: %s' % library)
        if layer:
            lines.append('  layer: %s' % layer)
        if version:
            lines.append('  source_version: "%s"' % version)
        lines.append('  source: doubao-user-skills')
        lines.append('  migrated_at: "2026-10-15"')
        lines.append('---')
        new = '\n'.join(lines) + '\n\n' + body.lstrip('\n')
        with open(md, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new)

        # agents/openai.yaml
        adir = os.path.join(dst, 'agents')
        os.makedirs(adir, exist_ok=True)
        y = []
        y.append('interface:')
        y.append('  display_name: "%s"' % disp)
        y.append('  short_description: "%s"' % short.replace('"', '「'))
        y.append('  default_prompt: "%s"' % prompt)
        with open(os.path.join(adir, 'openai.yaml'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(y) + '\n')

        nfile = sum(len(fs) for _, _, fs in os.walk(dst))
        log.append('OK %-34s desc %4d%s  文件 %3d  行 %4d' % (
            slug, len(desc), '(截断)' if clipped else '      ', nfile, len(new.split('\n'))))

    with open(LOG, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(log) + '\n')
    print('\n'.join(log))


if __name__ == '__main__':
    main()
