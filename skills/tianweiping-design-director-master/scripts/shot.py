#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""shot.py —— 豆包视觉计算内核 · 镜头规格编译器

解决的问题：同一句话生成十次，出来十种风格 —— 因为提示词里没有「槽位」。
本工具把一次生成拆成固定槽位（景别/机位/焦段/光圈/光位/色温/调色板/质感/运动/比例/禁止项），
编译成结构化提示词，并且：

  · --from-image ref.png  直接从参考图取调色板写进「锁色」槽（闭环 1）
  · --spec s.json         批量编译一组镜头，并自动生成「一致性锁」段
  · verify <img>          出图后校验它有没有按规格来（闭环 2，调用 vqc 的调色板提取）

子命令
  build  --subject "..." [--action ...] [--shot 特写] [--angle 平视] [--lens 85]
         [--aperture 2] [--light 侧逆光] [--wb 暖] [--texture 胶片颗粒]
         [--motion 推] [--mood ...] [--ratio 16:9] [--palette "#E4744A,#2E4756"]
         [--from-image ref.png] [--extra "..."] [--avoid "..."] [--profile poster]
         [--json] [--out prompt.txt]
  spec   --file shots.json -o outdir        批量：每个镜头一个 .txt + 一份 locks.md
  verify <img...> --palette "#..,#.." [--tol 26] [--json]
         --spec shot.json
  list   打印所有可选槽位取值
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

g_shot = {
    "大远景": "extreme wide shot, tiny subject in vast landscape",
    "远景": "wide shot, subject in full environment",
    "全景": "full shot, whole body visible",
    "中景": "medium shot, waist up",
    "中近景": "medium close-up, chest up",
    "近景": "close-up, head and shoulders",
    "特写": "close-up, face or object fills frame",
    "大特写": "extreme close-up, macro detail",
    "微距": "macro shot, texture fills the frame",
}
g_angle = {
    "平视": "eye-level", "俯视": "high angle looking down", "仰视": "low angle looking up",
    "过肩": "over-the-shoulder", "主观": "first-person POV", "顶俯": "top-down bird's eye",
    "荷兰角": "dutch tilt", "背面": "from behind",
}
g_lens = {"14": "14mm ultra wide, strong perspective", "24": "24mm wide",
          "35": "35mm natural documentary", "50": "50mm standard, no distortion",
          "85": "85mm portrait, gentle compression", "135": "135mm telephoto, heavy compression",
          "微距": "100mm macro"}
g_aperture = {"1.4": "f/1.4 paper-thin depth of field", "2": "f/2 shallow depth of field",
              "2.8": "f/2.8 soft background separation", "4": "f/4 moderate depth of field",
              "5.6": "f/5.6 balanced", "8": "f/8 deep focus, everything sharp",
              "11": "f/11 maximum depth of field"}
g_light = {
    "顺光": "flat frontal light", "侧光": "side light, strong form shadow",
    "侧逆光": "rim light from behind-side, glowing edge",
    "逆光": "backlit, silhouette edge glow", "顶光": "top light, dramatic shadow",
    "窗光": "soft window light from one side", "柴火": "warm firelight from below",
    "烛光": "candlelight, small warm pool", "阴天": "overcast diffuse light, no hard shadow",
    "黄金时刻": "golden hour, long warm shadow", "蓝调": "blue hour, cool ambient",
    "棚拍": "studio softbox, even clean light",
}
g_wb = {"暖": "warm 2800-3400K", "暖中性": "slightly warm 4200K", "中性": "neutral 5600K",
        "冷中性": "slightly cool 6500K", "冷": "cool 7500-9000K"}
g_motion = {"固定": "static camera, locked off", "推": "slow dolly in",
            "拉": "slow dolly out", "摇": "slow pan", "移": "lateral truck",
            "跟": "tracking shot following subject", "升降": "crane up",
            "手持": "handheld, subtle shake", "环绕": "slow orbit around subject",
            "手持跟随": "handheld following, documentary energy"}
g_texture = {
    "胶片颗粒": "fine film grain", "哑光": "matte finish, no specular hotspot",
    "水彩": "watercolor wash, visible paper grain", "蜡笔": "crayon texture, waxy edge",
    "陶瓷": "glazed ceramic, soft specular", "木纹": "visible wood grain",
    "布纹": "fabric weave texture", "蒸汽": "haze and steam in air",
    "塑料感": "", "干净数码": "clean digital, no grain",
}
g_ratio = {"16:9": "16:9 landscape", "9:16": "9:16 vertical", "1:1": "1:1 square",
           "4:3": "4:3", "3:4": "3:4 portrait", "21:9": "21:9 cinematic",
           "2.39:1": "2.39:1 anamorphic scope"}

DEFAULT_AVOID = ["多余的手指", "肢体错位", "文字乱码", "水印", "logo 变形",
                 "过饱和", "塑料感", "模糊", "过曝"]

PARAMS = {
    "poster": {"分辨率": "长边 ≥ 2480（A3 300dpi）", "步数": "28-34", "CFG": "5-7",
               "一次出图": "4 张候选，用 vqc pick 选", "后期": "autolevel → unsharp 轻"},
    "product": {"分辨率": "≥ 1600×1600", "步数": "26-32", "CFG": "5-7",
                "一次出图": "4-6 张", "后期": "chroma 去色噪 → unsharp 轻 → grain 2"},
    "illustration": {"分辨率": "长边 ≥ 2000", "步数": "24-30", "CFG": "6-8",
                     "一次出图": "4 张", "后期": "unify 到参考图保证成套"},
    "video": {"分辨率": "原生 720p 先出，再 Lanczos 放大", "帧率": "文戏 12fps / 动作 24fps",
              "时长": "单镜 3-5s，长镜优于多切", "后期": "vframe 查闪烁 → 再决定是否重出"},
}


def palette_from_image(path, n=5):
    import numpy as np
    from PIL import Image
    import vqc
    im = Image.open(path).convert("RGB")
    if max(im.size) > 1024:
        r = 1024 / max(im.size)
        im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    pal = vqc.palette_of(np.asarray(im, np.float32) / 255.0, k=n)
    return [c["hex"] for c in pal["colors"]]


def compile_prompt(sp):
    s = sp.get
    shot = g_shot.get(s("shot", "近景"), s("shot", ""))
    angle = g_angle.get(s("angle", "平视"), "")
    lens = g_lens.get(str(s("lens", "50")), f"{s('lens')}mm")
    ap = g_aperture.get(str(s("aperture", "")), "")
    light = g_light.get(s("light", ""), s("light", ""))
    wb = g_wb.get(s("wb", ""), "")
    tex = g_texture.get(s("texture", ""), s("texture", ""))
    motion = g_motion.get(s("motion") or "", "")
    ratio = g_ratio.get(s("ratio", "16:9"), s("ratio", ""))

    cam = " · ".join([x for x in [s("shot", ""), s("angle", ""),
                                  (f"{s('lens')}mm" if s("lens") else ""),
                                  (f"f/{s('aperture')}" if s("aperture") else "")] if x])
    lightline = " · ".join([x for x in [s("light", ""), (s("wb", "") + "色温" if s("wb") else "")] if x])
    pal = sp.get("palette") or []
    pal_line = ""
    if pal:
        pal_line = "锁定调色板 " + " ".join(pal) + f"（共 {len(pal)} 色，单色面积不超过 60%）"

    zh = []
    zh.append(f"【主体】{s('subject', '')}")
    if s("action"):
        zh.append(f"【动作】{s('action')}")
    if cam:
        zh.append(f"【镜头】{cam}")
    if s("light") or s("wb"):
        zh.append(f"【光】{s('light','')}" + (f" · {s('wb')}色温" if s("wb") else ""))
    if pal_line:
        zh.append(f"【色】{pal_line}")
    if s("texture"):
        zh.append(f"【质感】{s('texture')}")
    if s("motion"):
        zh.append(f"【运动】{s('motion')}")
    if s("mood"):
        zh.append(f"【情绪】{s('mood')}")
    if ratio:
        zh.append(f"【画面】{ratio}")
    if s("extra"):
        zh.append(f"【补充】{s('extra')}")
    avoid = sp.get("avoid") or DEFAULT_AVOID
    zh.append("【禁止】" + "、".join(avoid))

    en = ", ".join([x for x in [
        s("subject", ""),
        s("action", ""),
        shot, angle,
        f"{s('lens')}mm" if s("lens") else "",
        ap, light, wb, tex, motion,
        ("limited palette: " + " ".join(pal)) if pal else "",
        ratio,
        s("mood", ""),
    ] if x])

    return {
        "zh": "\n".join(zh),
        "en": en,
        "negative": ", ".join(avoid),
        "slots": {"shot": s("shot"), "angle": s("angle"), "lens": s("lens"),
                  "aperture": s("aperture"), "light": s("light"), "wb": s("wb"),
                  "texture": s("texture"), "motion": s("motion"), "ratio": s("ratio"),
                  "palette": pal, "mood": s("mood")},
        "params": PARAMS.get(s("profile", "illustration"), PARAMS["illustration"]),
    }


def _has_en(txt):
    return any(ord(c) < 128 for c in txt)


def lock_block(slots):
    lines = ["# 一致性锁（同场景每个镜头都原样复制这段）", "",
             f"- 景别/机位：{slots.get('shot','-')} · {slots.get('angle','-')}",
             f"- 焦段/光圈：{slots.get('lens') or '-'}mm · f/{slots.get('aperture') or '-'}",
             f"- 光位/色温：{slots.get('light') or '-'} · {slots.get('wb') or '-'}",
             f"- 质感：{slots.get('texture') or '-'}",
             f"- 画面比例：{slots.get('ratio') or '-'}"]
    if slots.get("palette"):
        lines.append("- 调色板：" + " ".join(slots["palette"]))
    lines += ["", "> 只改「主体」和「动作」两行，其余保持逐字一致 —— "
                  "这是让同一场戏看起来像同一个人拍的唯一可靠办法。"]
    return "\n".join(lines)


# ============================================================ 子命令

def cmd_build(a):
    sp = {"subject": a.subject, "action": a.action, "shot": a.shot, "angle": a.angle,
          "lens": a.lens, "aperture": a.aperture, "light": a.light, "wb": a.wb,
          "texture": a.texture, "motion": a.motion, "mood": a.mood, "ratio": a.ratio,
          "extra": a.extra, "profile": a.profile,
          "palette": [c.strip() for c in a.palette.split(",") if c.strip()] if a.palette else None,
          "avoid": [c.strip() for c in a.avoid.split("、") if c.strip()] if a.avoid else None}
    if a.from_image:
        pal = palette_from_image(a.from_image, n=a.palette_n)
        if sp["palette"]:
            merged = []
            for c in list(sp["palette"]) + pal:
                if c.upper() not in [m.upper() for m in merged]:
                    merged.append(c)
            pal = merged[:max(a.palette_n, len(sp["palette"]))]
        sp["palette"] = pal
    out = compile_prompt(sp)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("─" * 62)
        print(out["zh"])
        print("─" * 62)
        print("\nEN:", out["en"])
        print("\nNEGATIVE:", out["negative"])
        print("\n参数建议：")
        for k, v in out["params"].items():
            print(f"  {k:<8}{v}")
        print("\n" + lock_block(out["slots"]))
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(out["zh"] + "\n\n[EN]\n" + out["en"] + "\n\n[NEGATIVE]\n"
                     + out["negative"] + "\n\n" + lock_block(out["slots"]) + "\n")
        print("\n写入 ->", a.out)
    return 0


def cmd_spec(a):
    with open(a.file, encoding="utf-8-sig") as fh:
        doc = json.load(fh)
    shots = doc.get("shots") or []
    base = doc.get("base") or {}
    os.makedirs(a.outdir, exist_ok=True)
    compiled = []
    for i, sh in enumerate(shots, 1):
        sp = dict(base)
        sp.update(sh)
        sp.setdefault("profile", doc.get("profile", "illustration"))
        if sp.get("from_image") and not sp.get("palette"):
            sp["palette"] = palette_from_image(sp["from_image"])
        out = compile_prompt(sp)
        name = sh.get("name") or f"shot{i:02d}"
        p = os.path.join(a.outdir, f"{i:02d}_{name}.txt")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(out["zh"] + "\n\n[EN]\n" + out["en"] + "\n\n[NEGATIVE]\n" + out["negative"] + "\n")
        compiled.append({"name": name, "file": p, "zh": out["zh"], "slots": out["slots"]})
        print(f"  ok {p}")
    if compiled:
        locks = lock_block(compiled[0]["slots"])
        with open(os.path.join(a.outdir, "_locks.md"), "w", encoding="utf-8") as fh:
            fh.write(locks + "\n")
        print(f"  一致性锁 -> {os.path.join(a.outdir, '_locks.md')}")
    print(f"共 {len(compiled)} 个镜头 -> {a.outdir}")
    return 0


def cmd_verify(a):
    import numpy as np
    from PIL import Image
    import vqc
    if a.spec:
        with open(a.spec, encoding="utf-8-sig") as fh:
            doc = json.load(fh)
        want = (doc.get("base") or {}).get("palette") or (doc.get("shots") or [{}])[0].get("palette")
    else:
        want = [c.strip() for c in (a.palette or "").split(",") if c.strip()]
    if not want:
        raise SystemExit("要给 --palette 或 --spec")
    want_rgb = []
    for h in want:
        h = h.lstrip("#")
        want_rgb.append([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])
    want_rgb = np.array(want_rgb, np.float32)

    rows = []
    for p in a.images:
        im = Image.open(p).convert("RGB")
        if max(im.size) > 1024:
            r = 1024 / max(im.size)
            im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
        arr = np.asarray(im, np.float32) / 255.0
        pal = vqc.palette_of(arr, k=max(5, len(want)))
        got = []
        for c in pal["colors"]:
            h = c["hex"].lstrip("#")
            got.append([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])
        got_rgb = np.array(got, np.float32)
        # 每个规格色到最近的实际主色的距离（RGB 0-255 尺度）
        d = np.sqrt(((want_rgb[:, None, :] - got_rgb[None, :, :]) ** 2).sum(-1)) * 255
        nearest = d.min(1)
        hit = int((nearest <= a.tol).sum())
        cover = float(sum(c["share"] for i, c in enumerate(pal["colors"])
                          if nearest.min() <= a.tol and False) or 0.0)
        verdict = ("ok" if hit >= max(1, math.ceil(len(want) * 0.6)) else
                   ("warn" if hit >= 1 else "off"))
        rows.append({"file": p, "spec_colors": want, "actual": [c["hex"] for c in pal["colors"]],
                     "matched": hit, "of": len(want),
                     "nearest_dist": [round(float(x), 1) for x in nearest],
                     "verdict": verdict})
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    else:
        for r in rows:
            print(f"{os.path.basename(r['file'])}  {r['verdict']}  命中 {r['matched']}/{r['of']}")
            print(f"   规格色 {' '.join(r['spec_colors'])}")
            print(f"   实际   {' '.join(r['actual'][:6])}")
            print(f"   最近距离 {r['nearest_dist']}（容差 {a.tol}）")
            if r["verdict"] != "ok":
                print("   → 画面没按锁色走：把调色板写进提示词的【色】槽，并降低主色外颜色的描述强度。")
    return 0 if all(r["verdict"] == "ok" for r in rows) else 3


def cmd_list(a):
    for title, table in [("景别 shot", g_shot), ("机位 angle", g_angle), ("焦段 lens", g_lens),
                         ("光圈 aperture", g_aperture), ("光位 light", g_light),
                         ("色温 wb", g_wb), ("运动 motion", g_motion),
                         ("质感 texture", g_texture), ("比例 ratio", g_ratio)]:
        print(f"\n{title}")
        print("  " + "  ".join(table.keys()))
    print("\n参数档 profile：", "  ".join(PARAMS.keys()))
    return 0


def main():
    ap = argparse.ArgumentParser(description="豆包视觉计算内核 · 镜头规格编译器")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("build")
    p.add_argument("--subject", required=True)
    p.add_argument("--action", default="")
    p.add_argument("--shot", default="近景")
    p.add_argument("--angle", default="平视")
    p.add_argument("--lens", default="50")
    p.add_argument("--aperture", default="2.8")
    p.add_argument("--light", default="")
    p.add_argument("--wb", default="")
    p.add_argument("--texture", default="")
    p.add_argument("--motion", default="固定")
    p.add_argument("--mood", default="")
    p.add_argument("--ratio", default="16:9")
    p.add_argument("--palette")
    p.add_argument("--from-image")
    p.add_argument("--palette-n", type=int, default=5)
    p.add_argument("--extra", default="")
    p.add_argument("--avoid")
    p.add_argument("--profile", default="illustration", choices=list(PARAMS))
    p.add_argument("--out")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_build)

    p = sub.add_parser("spec")
    p.add_argument("--file", required=True)
    p.add_argument("-o", "--outdir", required=True)
    p.set_defaults(fn=cmd_spec)

    p = sub.add_parser("verify")
    p.add_argument("images", nargs="+")
    p.add_argument("--palette")
    p.add_argument("--spec")
    p.add_argument("--tol", type=float, default=26.0)
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_verify)

    p = sub.add_parser("list")
    p.set_defaults(fn=cmd_list)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
