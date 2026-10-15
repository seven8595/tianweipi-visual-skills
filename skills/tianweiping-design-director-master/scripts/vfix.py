#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vfix.py —— 豆包视觉计算内核 · 定向修复（本地后处理，不重生成）

和 vqc.py 配对使用：vqc 告诉你哪儿不对，vfix 只修那一处，然后再跑 vqc 复评。
所有操作都是确定性的、可复现的，参数写死在命令行里，方便回滚。

子命令
  autolevel <in> -o <out> [--black 0.5] [--white 99.5] [--per-channel]
            按分位拉伸色阶：修整体偏亮/偏暗/发灰/暗部死黑
  unsharp   <in> -o <out> [--radius 2.0] [--amount 80] [--threshold 3]
            USM 锐化：修清晰度不足，别过量（超过 amount 120 会出白边）
  chroma    <in> -o <out> [--size 5] [--strength 0.6]
            只对色度去噪（YCbCr 的 Cb/Cr 做中值），保留亮度细节，不磨皮
  sat       <in> -o <out> [--gain 0.9] [--vibrance 0.0]
            饱和度调整：gain 为整体倍数，vibrance 只补低饱和区
  unify     <in...> -o <outdir> --ref ref.png [--strength 1.0] [--use-lab]
            把一批图统一到参考图的亮度/色彩分布（Reinhard 迁移）→ 成套一致
  grain     <in> -o <out> [--amount 4] [--mono]
            补细颗粒，治 AI 塑料感（amount 2-6 微量即可）
  resize    <in> -o <out> --long 2048 [--sharpen 60]
            Lanczos 放大 + 补锐化（比 AI 超分省算力，先用它兜底）
  recipe    <in> -o <out> --steps "autolevel:black=1;chroma:size=5;unsharp:amount=70;grain:amount=3"
            一串处理按顺序执行，一条命令搞定
  batch     <dir|glob...> -o <outdir> --recipe-file r.json [--profile poster]
            批量套同一套修复，输出到 outdir（不改原图）

约定
  · 永远不覆盖输入文件（除非 in 和 out 相同，会拒绝执行）
  · 所有输出保留原分辨率与格式（PNG 无损 / JPEG q=95）
  · --dry-run 只打印将要执行的操作
"""
import argparse
import glob as _glob
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass
try:
    Image.MAX_IMAGE_PIXELS = None
except Exception:
    pass


# ============================================================ 基础

def open_rgb(path):
    im = Image.open(path)
    fmt = im.format or "PNG"
    return im.convert("RGB"), fmt


def save_rgb(im, out, fmt="PNG"):
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    ext = os.path.splitext(out)[1].lower()
    if ext in (".jpg", ".jpeg"):
        im.save(out, quality=95, subsampling=0, optimize=True, progressive=True)
    elif ext == ".webp":
        im.save(out, quality=95, method=6)
    else:
        im.save(out, "PNG", optimize=True)
    return out


def guard(src, dst):
    if os.path.abspath(src) == os.path.abspath(dst):
        raise SystemExit("拒绝执行：输出不能覆盖输入，请另给 -o 路径")


# ============================================================ 各操作

def op_autolevel(im, black=0.5, white=99.5, per_channel=False):
    a = np.asarray(im, np.float32)
    if per_channel:
        out = np.empty_like(a)
        for c in range(3):
            lo, hi = np.percentile(a[..., c], [black, white])
            out[..., c] = np.clip((a[..., c] - lo) / max(hi - lo, 1e-6), 0, 1) * 255
    else:
        g = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
        lo, hi = np.percentile(g, [black, white])
        scale = 255.0 / max(hi - lo, 1e-6)
        out = np.clip((a - lo) * scale, 0, 255)
    return Image.fromarray(out.astype(np.uint8), "RGB")


def op_unsharp(im, radius=2.0, amount=80, threshold=3):
    return im.filter(ImageFilter.UnsharpMask(radius=float(radius),
                                             percent=int(amount),
                                             threshold=int(threshold)))


def op_chroma(im, size=5, strength=0.6):
    """只处理 Cb/Cr：中值滤波去色噪，亮度通道原样保留"""
    ycc = im.convert("YCbCr")
    y, cb, cr = ycc.split()
    k = int(size) | 1
    cb2 = cb.filter(ImageFilter.MedianFilter(k))
    cr2 = cr.filter(ImageFilter.MedianFilter(k))
    if strength < 1.0:
        cb = Image.blend(cb, cb2, float(strength))
        cr = Image.blend(cr, cr2, float(strength))
    else:
        cb, cr = cb2, cr2
    return Image.merge("YCbCr", (y, cb, cr)).convert("RGB")


def op_sat(im, gain=0.9, vibrance=0.0):
    hsv = np.asarray(im.convert("HSV"), np.float32)
    s = hsv[..., 1] / 255.0
    s = s * float(gain)
    if vibrance:
        # 只抬低饱和区，高饱和区不动 —— 比整体加饱和更不容易脏
        s = s + float(vibrance) * (1.0 - s) * s
    hsv[..., 1] = np.clip(s * 255, 0, 255)
    return Image.fromarray(hsv.astype(np.uint8), "HSV").convert("RGB")


def _lab_stats(a):
    return a.reshape(-1, 3).mean(0), a.reshape(-1, 3).std(0) + 1e-6


# ---- 自己实现 CIELAB：PIL 的 "LAB" 模式往返会产出霓虹色，不能用 ----
_M_RGB2XYZ = np.array([[0.4124564, 0.3575761, 0.1804375],
                       [0.2126729, 0.7151522, 0.0721750],
                       [0.0193339, 0.1191920, 0.9503041]], np.float64)
_M_XYZ2RGB = np.linalg.inv(_M_RGB2XYZ)
_WP = np.array([0.95047, 1.0, 1.08883], np.float64)
_EPS = 216.0 / 24389.0
_KAP = 24389.0 / 27.0


def _srgb_to_linear(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _linear_to_srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def rgb_to_lab(rgb):
    """rgb: (H,W,3) float 0..1  ->  lab: L 0..100, a/b 约 -128..127"""
    xyz = _srgb_to_linear(rgb) @ _M_RGB2XYZ.T / _WP
    f = np.where(xyz > _EPS, np.cbrt(np.maximum(xyz, 0)), (_KAP * xyz + 16) / 116.0)
    return np.stack([116 * f[..., 1] - 16,
                     500 * (f[..., 0] - f[..., 1]),
                     200 * (f[..., 1] - f[..., 2])], -1)


def lab_to_rgb(lab):
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    fy = (L + 16) / 116.0
    fx, fz = fy + a / 500.0, fy - b / 200.0
    fx3, fy3, fz3 = fx ** 3, fy ** 3, fz ** 3
    xr = np.where(fx3 > _EPS, fx3, (116 * fx - 16) / _KAP)
    yr = np.where(L > _KAP * _EPS, fy3, L / _KAP)
    zr = np.where(fz3 > _EPS, fz3, (116 * fz - 16) / _KAP)
    xyz = np.stack([xr, yr, zr], -1) * _WP
    return _linear_to_srgb(xyz @ _M_XYZ2RGB.T)


def op_unify(im, ref_im, strength=1.0):
    """Reinhard 色彩迁移（真 CIELAB）：把候选图的均值/方差对齐到参考图。
    用于把一批生成的图拉成同一套观感 —— 比逐张手调快，也比调提示词稳。"""
    a = rgb_to_lab(np.asarray(im, np.float32) / 255.0)
    b = rgb_to_lab(np.asarray(ref_im.convert("RGB"), np.float32) / 255.0)
    ma, sa = _lab_stats(a)
    mb, sb = _lab_stats(b)
    s = float(strength)
    out = (a - ma) / sa * (sa + (sb - sa) * s) + (ma + (mb - ma) * s)
    return Image.fromarray((np.clip(lab_to_rgb(out), 0, 1) * 255).astype(np.uint8), "RGB")


def op_grain(im, amount=4, mono=True, seed=7, soft=True):
    a = np.asarray(im, np.float32)
    rng = np.random.default_rng(seed)
    h, w = a.shape[:2]
    n = rng.normal(0, 1, (h, w)).astype(np.float32)
    if soft:
        g = Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8), "L")
        g = g.filter(ImageFilter.GaussianBlur(0.6))
        n = (np.asarray(g, np.float32) / 255.0 - 0.5) * 2.0
    if mono:
        a = a + (n * amount)[..., None]
    else:
        a = a + np.stack([n, np.roll(n, 1, 0), np.roll(n, 2, 0)], -1) * amount
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


def op_resize(im, long_side=None, w=None, h=None, sharpen=60):
    if w and h:
        tw, th = int(w), int(h)
    elif long_side:
        r = float(long_side) / max(im.size)
        tw, th = max(1, int(round(im.width * r))), max(1, int(round(im.height * r)))
    else:
        return im
    out = im.resize((tw, th), Image.LANCZOS)
    if sharpen:
        out = op_unsharp(out, radius=1.1, amount=sharpen, threshold=2)
    return out


# ============================================================ 配方

OPS = {
    "autolevel": (op_autolevel, {"black": float, "white": float, "per_channel": "flag"}),
    "unsharp": (op_unsharp, {"radius": float, "amount": int, "threshold": int}),
    "chroma": (op_chroma, {"size": int, "strength": float}),
    "sat": (op_sat, {"gain": float, "vibrance": float}),
    "grain": (op_grain, {"amount": float, "mono": "flag", "seed": int, "soft": "flag"}),
    "resize": (op_resize, {"long_side": int, "w": int, "h": int, "sharpen": int}),
    "unify": (op_unify, {"strength": float}),
}

RECIPES = {
    # 常用配方：症状 → 一条命令
    "gray":    "autolevel:black=0.8,white=99.2",
    "dark":    "autolevel:black=0.2,white=99.0",
    "bright":  "autolevel:black=1.5,white=97.0",
    "soft":    "unsharp:radius=1.6,amount=90,threshold=2",
    "blurry":  "unsharp:radius=2.2,amount=120,threshold=1",
    "noisy":   "chroma:size=5,strength=0.8;unsharp:radius=1.2,amount=50,threshold=3",
    "plastic": "grain:amount=4;unsharp:radius=1.4,amount=45,threshold=2",
    "harsh":   "sat:gain=0.92,vibrance=0.05;autolevel:black=1.0,white=98.5",
    "4k":      "resize:long_side=3840,sharpen=55",
    "web":     "resize:long_side=2048,sharpen=45;unsharp:radius=1.0,amount=35,threshold=2",
}


def parse_steps(s):
    """'autolevel:black=1;unsharp:amount=70' → [(name, kwargs), ...]"""
    steps = []
    for raw in s.split(";"):
        raw = raw.strip()
        if not raw:
            continue
        if ":" in raw:
            name, kv = raw.split(":", 1)
        else:
            name, kv = raw, ""
        name = name.strip()
        if name not in OPS:
            raise SystemExit(f"未知操作 {name}，可用：{', '.join(OPS)}")
        kwargs = {}
        for pair in [p for p in kv.split(",") if p.strip()]:
            k, v = pair.split("=", 1)
            k, v = k.strip(), v.strip()
            spec = OPS[name][1].get(k)
            if spec is None:
                raise SystemExit(f"{name} 不支持参数 {k}，可用：{list(OPS[name][1])}")
            if spec == "flag":
                kwargs[k] = v.lower() in ("1", "true", "yes", "on")
            else:
                kwargs[k] = spec(float(v)) if spec is float else spec(int(float(v)))
        steps.append((name, kwargs))
    return steps


def run_steps(im, steps, ref_im=None):
    for name, kw in steps:
        fn = OPS[name][0]
        if name == "unify":
            if ref_im is None:
                raise SystemExit("unify 需要 --ref 参考图")
            im = fn(im, ref_im, **kw)
        else:
            im = fn(im, **kw)
    return im


# ============================================================ 子命令

def _single(a, fn):
    guard(a.image, a.out)
    if getattr(a, "dry_run", False):
        print(f"[dry-run] {fn.__name__} {a.image} -> {a.out}")
        return 0
    im, fmt = open_rgb(a.image)
    out = fn(im)
    save_rgb(out, a.out, fmt)
    print(f"{fn.__name__}  {a.image} -> {a.out}  {out.width}×{out.height}")
    return 0


def cmd_recipe(a):
    guard(a.image, a.out)
    steps = parse_steps(RECIPES[a.preset] if a.preset else a.steps)
    ref = None
    if any(n == "unify" for n, _ in steps):
        if not a.ref:
            raise SystemExit("配方里含 unify，需要 --ref")
        ref, _ = open_rgb(a.ref)
    if a.dry_run:
        print("[dry-run]", a.image, "->", a.out)
        for n, k in steps:
            print("   ", n, k)
        return 0
    im, fmt = open_rgb(a.image)
    out = run_steps(im, steps, ref)
    save_rgb(out, a.out, fmt)
    print("recipe", " ; ".join(f"{n}({k})" for n, k in steps))
    print("  ", a.image, "->", a.out, f"{out.width}×{out.height}")
    return 0


def cmd_batch(a):
    files = expand(a.paths)
    if not files:
        print("没有匹配到文件")
        return 2
    steps = parse_steps(RECIPES[a.preset] if a.preset else a.steps)
    ref = None
    if any(n == "unify" for n, _ in steps):
        if not a.ref:
            raise SystemExit("配方里含 unify，需要 --ref")
        ref, _ = open_rgb(a.ref)
    os.makedirs(a.outdir, exist_ok=True)
    for p in files:
        base = os.path.splitext(os.path.basename(p))[0]
        ext = os.path.splitext(p)[1].lower() or ".png"
        dst = os.path.join(a.outdir, base + ext)
        if a.dry_run:
            print("[dry-run]", p, "->", dst)
            continue
        im, fmt = open_rgb(p)
        save_rgb(run_steps(im, steps, ref), dst, fmt)
        print("  ok", os.path.basename(dst))
    print(f"完成 {len(files)} 张 -> {a.outdir}")
    return 0


def cmd_unify(a):
    ref, _ = open_rgb(a.ref)
    os.makedirs(a.outdir or ".", exist_ok=True)
    files = expand(a.images)
    for p in files:
        base = os.path.splitext(os.path.basename(p))[0]
        ext = os.path.splitext(p)[1].lower() or ".png"
        dst = os.path.join(a.outdir or ".", base + ext)
        if a.dry_run:
            print("[dry-run]", p, "->", dst)
            continue
        im, fmt = open_rgb(p)
        save_rgb(op_unify(im, ref, a.strength), dst, fmt)
        print("  unified", os.path.basename(dst))
    print(f"统一 {len(files)} 张 -> {a.outdir}")
    return 0


def cmd_recipes(a):
    for k, v in RECIPES.items():
        print(f"  {k:<9}{v}")
    return 0


def expand(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            seen_ext = set()
            for ext in ("png", "jpg", "jpeg", "webp", "bmp", "tif", "tiff"):
                if ext in seen_ext:
                    continue
                seen_ext.add(ext)
                out += sorted(_glob.glob(os.path.join(p, f"*.{ext}")))
        elif any(ch in p for ch in "*?["):
            out += sorted(_glob.glob(p, recursive=True))
        else:
            out.append(p)
    seen, res = set(), []          # Windows 下 glob 不区分大小写，必须去重
    for p in out:
        k = os.path.abspath(p).lower()
        if k not in seen and os.path.isfile(p):
            seen.add(k)
            res.append(p)
    return res


def main():
    ap = argparse.ArgumentParser(description="豆包视觉计算内核 · 定向修复")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def single(name, fn, extra=None):
        p = sub.add_parser(name)
        p.add_argument("image"); p.add_argument("-o", "--out", required=True)
        p.add_argument("--dry-run", action="store_true")
        if extra:
            extra(p)
        p.set_defaults(fn=lambda a: _single(a, fn))

    single("autolevel", lambda im, **k: op_autolevel(im, **k),
           lambda p: (p.add_argument("--black", type=float, default=0.5),
                      p.add_argument("--white", type=float, default=99.5),
                      p.add_argument("--per-channel", action="store_true")))
    single("unsharp", lambda im, **k: op_unsharp(im, **k),
           lambda p: (p.add_argument("--radius", type=float, default=2.0),
                      p.add_argument("--amount", type=int, default=80),
                      p.add_argument("--threshold", type=int, default=3)))
    single("chroma", lambda im, **k: op_chroma(im, **k),
           lambda p: (p.add_argument("--size", type=int, default=5),
                      p.add_argument("--strength", type=float, default=0.6)))
    single("sat", lambda im, **k: op_sat(im, **k),
           lambda p: (p.add_argument("--gain", type=float, default=0.9),
                      p.add_argument("--vibrance", type=float, default=0.0)))
    single("grain", lambda im, **k: op_grain(im, **k),
           lambda p: (p.add_argument("--amount", type=float, default=4),
                      p.add_argument("--mono", action="store_true", default=True),
                      p.add_argument("--seed", type=int, default=7)))
    single("resize", lambda im, **k: op_resize(im, **k),
           lambda p: (p.add_argument("--long", dest="long_side", type=int, default=2048),
                      p.add_argument("--w", type=int), p.add_argument("--h", type=int),
                      p.add_argument("--sharpen", type=int, default=60)))

    p = sub.add_parser("recipe"); p.add_argument("image"); p.add_argument("-o", "--out", required=True)
    p.add_argument("--steps"); p.add_argument("--preset", choices=list(RECIPES))
    p.add_argument("--ref"); p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_recipe)

    p = sub.add_parser("batch"); p.add_argument("paths", nargs="+")
    p.add_argument("-o", "--outdir", required=True)
    p.add_argument("--steps"); p.add_argument("--preset", choices=list(RECIPES))
    p.add_argument("--ref"); p.add_argument("--profile"); p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_batch)

    p = sub.add_parser("unify"); p.add_argument("images", nargs="+")
    p.add_argument("-o", "--outdir", required=True); p.add_argument("--ref", required=True)
    p.add_argument("--strength", type=float, default=1.0); p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_unify)

    p = sub.add_parser("recipes"); p.set_defaults(fn=cmd_recipes)

    a = ap.parse_args()
    if a.cmd in ("recipe", "batch") and not (getattr(a, "steps", None) or getattr(a, "preset", None)):
        raise SystemExit("要给 --steps 或 --preset；用 `vfix.py recipes` 看预置配方")
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
