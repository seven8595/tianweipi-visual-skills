#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vqc.py —— 豆包视觉计算内核 · 画面质量量化（本地运算，不联网不调模型）

设计原则（很重要，别把它当万能打分器）
  1. 只对「绝对可判」的指标设硬门槛：分辨率、高光溢出、暗部死黑、过饱和、噪点、文字对比度。
  2. 「清晰度 / 塑料感 / 构图」这类和内容强相关的指标，用绝对阈值会误判 ——
     所以它们要么走相对比较（--baseline / compare），要么只降权做提示。
  3. 真正的用法是「一次生成 N 张 → pick 排序 → 对赢家做定向修复 → 复评」，
     而不是拿一个分数去审判一张图。

子命令
  score    <img...>  [--profile poster] [--baseline ref.png] [--json]
  pick     <a.png> <b.png> ...  [--profile poster] [--json]      # 候选排序，直接给赢家
  compare  <ref.png> <cand.png> [...]  [--json]                  # 与参考图逐项比
  palette  <img> [--n 6] [--swatch out.png] [--json]
  series   <dir|glob...> [--json]                                # 成套一致性
  textsafe <img> --box x,y,w,h [--text "#2E4756"] [--json]
  report   <dir|glob...> -o out/report.html [--profile poster]

退出码  0=通过  3=未达标（可直接当质量门用）
"""
import argparse
import json
import math
import os
import sys
import glob as _glob

import numpy as np
from PIL import Image

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass
try:
    Image.MAX_IMAGE_PIXELS = None
except Exception:
    pass

ANALYZE_SIDE = 1024
GRADE_CUT = [("A", 85), ("B", 72), ("C", 58), ("D", 0)]


# ============================================================ 基础工具

def load_rgb(path, max_side=ANALYZE_SIDE):
    im = Image.open(path)
    src_w, src_h = im.size
    im = im.convert("RGB")
    if max_side and max(im.size) > max_side:
        r = max_side / float(max(im.size))
        im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    return np.asarray(im, dtype=np.float32) / 255.0, (src_w, src_h)


def luma_of(rgb):
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def hsv_of(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = np.max(rgb, axis=-1)
    mn = np.min(rgb, axis=-1)
    d = mx - mn
    s = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0.0)
    h = np.zeros_like(mx)
    nz = d > 1e-6
    i = nz & (mx == r); h[i] = ((g - b)[i] / d[i]) % 6
    i = nz & (mx == g); h[i] = ((b - r)[i] / d[i]) + 2
    i = nz & (mx == b); h[i] = ((r - g)[i] / d[i]) + 4
    return (h * 60.0) % 360.0, s, mx


def saturate(v, lo, hi):
    return 0.0 if hi <= lo else float(min(1.0, max(0.0, (v - lo) / (hi - lo))))


def band(v, lo, hi, soft=0.35):
    if lo <= v <= hi:
        return 1.0
    span = max(hi - lo, 1e-6)
    return float(max(0.0, 1.0 - ((lo - v) if v < lo else (v - hi)) / (span * soft + 1e-6)))


def band_graded(v, lo, hi, ideal=None):
    """有理想点的梯度评分：理想点 100，带边缘 78，带外继续衰减到 0。
    平台型 band() 会让「勉强合格」和「刚刚好」都拿 100，没有区分度，所以软指标一律用这个。"""
    if ideal is None:
        ideal = (lo + hi) / 2.0
    span = max(hi - lo, 1e-6)
    if lo <= v <= hi:
        half = max(max(ideal - lo, hi - ideal), 1e-6)
        return float(1.0 - 0.22 * min(1.0, abs(v - ideal) / half))
    out = (lo - v) if v < lo else (v - hi)
    return float(max(0.0, 0.78 - out / (span * 0.60 + 1e-6)))


def r4(x):
    try:
        return round(float(x), 4)
    except Exception:
        return x


def circ_stats(h, s):
    w = s.reshape(-1)
    a = np.deg2rad(h.reshape(-1))
    c = float((np.cos(a) * w).sum())
    si = float((np.sin(a) * w).sum())
    tot = float(w.sum()) + 1e-9
    mean = math.degrees(math.atan2(si, c)) % 360.0 if (abs(c) + abs(si)) > 1e-9 else 0.0
    R = min(1.0, max(1e-6, math.hypot(c, si) / tot))
    return mean, math.degrees(math.sqrt(-2.0 * math.log(R)))


# ============================================================ 指标

def m_sharp(g):
    gy, gx = np.gradient(g)
    ten = float(np.mean(gx * gx + gy * gy))
    lap = g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:] - 4 * g[1:-1, 1:-1]
    return ten, float(np.var(lap)), lap


def m_expo(g):
    n = g.size
    return {"mean_luma": float(g.mean()),
            "clip_high": float((g > 0.985).sum() / n),
            "clip_low": float((g < 0.015).sum() / n),
            "p01": float(np.percentile(g, 1)), "p99": float(np.percentile(g, 99))}


def m_contrast(g):
    return {"std": float(g.std()),
            "range95": float(np.percentile(g, 95) - np.percentile(g, 5))}


def m_color(rgb, h, s):
    rg = rgb[..., 0] - rgb[..., 1]
    yb = 0.5 * (rgb[..., 0] + rgb[..., 1]) - rgb[..., 2]
    hm, hs = circ_stats(h, s)
    return {"colorfulness": float(math.sqrt(rg.std() ** 2 + yb.std() ** 2) +
                                  0.3 * math.sqrt(rg.mean() ** 2 + yb.mean() ** 2)),
            "mean_sat": float(s.mean()),
            "over_sat": float((s > 0.90).sum() / s.size),
            "hue_mean": hm, "hue_std": hs}


def m_compose(g):
    """构图不判绝对值，只给出可比较的量：
       thirds_dist 视觉重心到最近三分点的归一化距离
       center_dist 到画面中心的距离
       border_ratio 边缘 6% 区域的梯度能量占比（主体被切掉会偏高）
       symmetry_diff 左右翻转平均差（对称为主的画面应偏低）"""
    gy, gx = np.gradient(g)
    e = gx * gx + gy * gy
    tot = float(e.sum()) + 1e-9
    ys, xs = np.mgrid[0:g.shape[0], 0:g.shape[1]]
    cx = float((e * xs).sum() / tot) / max(1, g.shape[1] - 1)
    cy = float((e * ys).sum() / tot) / max(1, g.shape[0] - 1)
    thirds = [(1 / 3, 1 / 3), (2 / 3, 1 / 3), (1 / 3, 2 / 3), (2 / 3, 2 / 3)]
    d3 = min(math.hypot(cx - tx, cy - ty) for tx, ty in thirds) / math.hypot(1 / 3, 1 / 3)
    dc = math.hypot(cx - 0.5, cy - 0.5) / math.hypot(0.5, 0.5)
    h, w = g.shape
    bw, bh = max(1, int(w * 0.06)), max(1, int(h * 0.06))
    border = (e[:bh, :].sum() + e[-bh:, :].sum() + e[:, :bw].sum() + e[:, -bw:].sum()) / tot
    sym = float(np.mean(np.abs(g - g[:, ::-1])))
    return {"centroid_x": cx, "centroid_y": cy, "thirds_dist": min(1.0, d3),
            "center_dist": min(1.0, dc), "border_ratio": float(border),
            "symmetry_diff": sym}


def m_surface(g, ten, lap):
    mad = float(np.median(np.abs(lap - np.median(lap))))
    sigma = mad / 0.6745 / math.sqrt(6.0)
    bs = 16
    h, w = g.shape
    hh, ww = (h // bs) * bs, (w // bs) * bs
    if hh >= bs * 4 and ww >= bs * 4:
        gy, gx = np.gradient(g[:hh, :ww])
        e = (gx * gx + gy * gy).reshape(hh // bs, bs, ww // bs, bs).mean(axis=(1, 3)).ravel()
        flat, edge = float(np.percentile(e, 20)), float(np.percentile(e, 90))
    else:
        flat = edge = 0.0
    return {"noise_sigma": sigma, "flat_energy": flat, "edge_energy": edge,
            "plastic_ratio": float(flat / (edge + 1e-9))}


# ============================================================ 调色板（纯 RGB+YCbCr，不碰 PIL LAB）

def kmeans_palette(rgb, k=6, iters=26, seed=7):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    y = 0.299 * r + 0.587 * g + 0.114 * b
    cb = (b - y) * 1.6
    cr = (r - y) * 1.6
    X = np.stack([y, cb, cr], -1).reshape(-1, 3).astype(np.float32)
    step = max(1, X.shape[0] // 30000)
    X = X[::step]
    rng = np.random.default_rng(seed)
    C = [X[rng.integers(0, X.shape[0])]]
    for _ in range(k - 1):
        d = np.min(((X[:, None, :] - np.array(C)[None, :, :]) ** 2).sum(-1), axis=1)
        C.append(X[rng.choice(X.shape[0], p=d / (d.sum() + 1e-12))])
    C = np.array(C, np.float32)
    for _ in range(iters):
        a = ((X[:, None, :] - C[None, :, :]) ** 2).sum(-1).argmin(1)
        for j in range(k):
            m = a == j
            if m.any():
                C[j] = X[m].mean(0)
    cnt = np.bincount(a, minlength=k).astype(np.float32)
    return C, cnt, y, cb, cr


def ycbcr_to_rgb(y, cb, cr):
    r = y + 1.402 * cr
    g = y - 0.344136 * cb - 0.714136 * cr
    b = y + 1.772 * cb
    return [int(np.clip(v * 255, 0, 255)) for v in (r, g, b)]


def palette_of(rgb, k=6):
    C, cnt, _, _, _ = kmeans_palette(rgb, k=k)
    order = np.argsort(-cnt)
    cols = []
    for j in order:
        if cnt[j] <= 0:
            continue
        y, cb, cr = C[j]
        R, G, B = ycbcr_to_rgb(y, cb / 1.6, cr / 1.6)
        hh, ss, _ = hsv_of(np.array([[[R / 255.0, G / 255.0, B / 255.0]]], np.float32))
        cols.append({"hex": "#%02X%02X%02X" % (R, G, B),
                     "share": r4(cnt[j] / cnt.sum()),
                     "hue": r4(float(hh[0, 0])), "sat": r4(float(ss[0, 0]))})
    hs = [c["hue"] for c in cols if c["sat"] > 0.14]
    if len(hs) >= 2:
        a = np.deg2rad(np.array(hs))
        R_ = math.hypot(float(np.cos(a).mean()), float(np.sin(a).mean()))
        spread = math.degrees(math.sqrt(-2 * math.log(min(1.0, max(1e-6, R_)))))
    else:
        spread = 0.0
    return {"colors": cols, "hue_spread": r4(spread), "chromatic_count": len(hs),
            "top_share": cols[0]["share"] if cols else 0.0}


# ============================================================ 全量指标

def metrics(path):
    rgb, (W, H) = load_rgb(path)
    g = luma_of(rgb)
    h, s, _ = hsv_of(rgb)
    ten, lv, lap = m_sharp(g)
    pal = palette_of(rgb)
    return {
        "file": os.path.abspath(path), "name": os.path.basename(path),
        "width": W, "height": H, "aspect": r4(W / float(H)),
        "megapixels": r4(W * H / 1e6),
        "sharp": {"tenengrad": r4(ten), "laplacian_var": r4(lv),
                  "log_ten": r4(math.log10(ten + 1e-9))},
        "expo": {k: r4(v) for k, v in m_expo(g).items()},
        "contrast": {k: r4(v) for k, v in m_contrast(g).items()},
        "color": {k: r4(v) for k, v in m_color(rgb, h, s).items()},
        "compose": {k: r4(v) for k, v in m_compose(g).items()},
        "surface": {k: r4(v) for k, v in m_surface(g, ten, lap).items()},
        "palette": pal,
    }


# ============================================================ 评分

# 硬门槛：绝对可判，不达标就是错
# noise_sigma 门槛按本机实测重新标定：干净交付物实测 0.005–0.015
# （绘本插图 0.0074–0.0124，海报 0.0095，加 grain 后 0.0124）。
# 原先把 illustration 定到 0.034 太松，会让「加噪版」在排序里赢过干净版 —— 自检抓到的真 bug。
HARD = {
    "poster": {"clip_high": ("max", 0.020), "clip_low": ("max", 0.030),
               "over_sat": ("max", 0.045), "noise_sigma": ("max", 0.018),
               "min_side": ("min", 1200)},
    "product": {"clip_high": ("max", 0.022), "clip_low": ("max", 0.022),
                "over_sat": ("max", 0.050), "noise_sigma": ("max", 0.016),
                "min_side": ("min", 1000)},
    "illustration": {"clip_high": ("max", 0.045), "clip_low": ("max", 0.040),
                     "over_sat": ("max", 0.070), "noise_sigma": ("max", 0.022),
                     "min_side": ("min", 800)},
    "video_frame": {"clip_high": ("max", 0.028), "clip_low": ("max", 0.040),
                    "over_sat": ("max", 0.055), "noise_sigma": ("max", 0.026),
                    "min_side": ("min", 512)},
}
HARD["default"] = HARD["illustration"]

# 软带：(下限, 上限, 理想值) —— 用梯度评分，不是平台分
SOFT = {
    "poster": {"mean_luma": (0.40, 0.92, 0.62), "range95": (0.42, 0.95, 0.74),
               "mean_sat": (0.12, 0.62, 0.34), "hue_spread": (0.0, 100.0, 10.0)},
    "product": {"mean_luma": (0.40, 0.90, 0.60), "range95": (0.34, 0.92, 0.68),
                "mean_sat": (0.12, 0.62, 0.36), "hue_spread": (0.0, 110.0, 12.0)},
    "illustration": {"mean_luma": (0.38, 0.92, 0.62), "range95": (0.28, 0.92, 0.62),
                     "mean_sat": (0.10, 0.62, 0.32), "hue_spread": (0.0, 130.0, 15.0)},
    "video_frame": {"mean_luma": (0.28, 0.86, 0.55), "range95": (0.28, 0.92, 0.62),
                    "mean_sat": (0.08, 0.62, 0.30), "hue_spread": (0.0, 120.0, 12.0)},
}
SOFT["default"] = SOFT["illustration"]

WEIGHTS = {"clip_high": 1.4, "clip_low": 1.4, "over_sat": 1.1, "noise_sigma": 1.0,
           "min_side": 1.0, "mean_luma": 1.2, "range95": 1.1, "mean_sat": 0.9,
           "hue_spread": 1.2, "sharp": 0.5, "compose": 0.7}

ADVICE = {
    "clip_high": "高光溢出：提示词删掉「强光/发光/过曝/逆光光斑」，或 vfix.py autolevel --white 96 收回高光。",
    "clip_low": "暗部死黑：提示词补「暗部保留细节」，或 vfix.py autolevel --black 3 抬暗部。",
    "over_sat": "过饱和：主色铺得太多。减少该色面积，或 vfix.py sat --gain 0.9 整体降 10%。",
    "noise_sigma": "噪点偏高：先 vfix.py chroma（只去色噪，别整体磨皮），再复评。",
    "min_side": "分辨率不够：长边低于门槛，先按 vfix.py resize 用 Lanczos 放大再补 unsharp。",
    "mean_luma": "整体偏亮或偏暗：vfix.py autolevel 一步到位，再复评。",
    "range95": "对比度不足或过猛：调 autolevel 的分位（black 0.5→3，white 99.5→96）。",
    "mean_sat": "饱和度偏离：提示词里写死调色板，并注明低饱和 / 高饱和。",
    "hue_spread": "调色板不收敛、画面发花：先定 3 色板再生成，或 vfix.py unify 统一到参考图。",
    "sharp": "清晰度低于参考：提示词加「细节/纹理/微距」并调低降噪；后处理 vfix.py unsharp。",
    "plastic_ratio": "AI 塑料感：平坦区几乎没细节。提示词加「胶片颗粒/皮肤纹理/纸张质感」，后处理 vfix.py grain --amount 4。",
    "compose": "构图提示：主体既不居中也不在三分点，或边缘能量过高（主体被切）。重出时明确主体位置与留白方向。",
}


def _get(m, key):
    if key == "sharp":
        return m["sharp"]["log_ten"]
    if key == "compose":
        return None
    if key in ("clip_high", "clip_low", "mean_luma"):
        return m["expo"][key]
    if key in ("range95",):
        return m["contrast"][key]
    if key in ("over_sat", "mean_sat"):
        return m["color"][key]
    if key == "hue_spread":
        return m["palette"]["hue_spread"]
    if key in ("noise_sigma", "plastic_ratio"):
        return m["surface"][key]
    if key == "min_side":
        return min(m["width"], m["height"])
    return None


def compose_score(m):
    c = m["compose"]
    place = max(band_graded(c["thirds_dist"], 0.0, 0.30, 0.10),
                band_graded(c["center_dist"], 0.0, 0.16, 0.0))
    border = band_graded(c["border_ratio"], 0.0, 0.70, 0.25)
    return round((place * 0.55 + border * 0.45) * 100, 1)


def score(m, profile="default", baseline=None):
    P = profile if profile in HARD else "default"
    H, S = HARD[P], SOFT[P]
    parts, issues = {}, []

    for key, (kind, thr) in H.items():
        v = _get(m, key)
        if v is None:
            continue
        ok = (v <= thr) if kind == "max" else (v >= thr)
        s = 100.0 if ok else max(0.0, 100.0 - (abs(v - thr) / (thr + 1e-9)) * 260)
        parts[key] = {"raw": r4(v), "score": round(s, 1), "hard": True}
        if not ok:
            issues.append({"key": key, "raw": r4(v), "score": round(s, 1),
                           "hard": True, "advice": ADVICE[key]})

    for key, (lo, hi, ideal) in S.items():
        v = _get(m, key)
        if v is None:
            continue
        s = band_graded(v, lo, hi, ideal) * 100
        parts[key] = {"raw": r4(v), "score": round(s, 1), "hard": False,
                      "ideal": ideal}
        if s < 78:
            issues.append({"key": key, "raw": r4(v), "score": round(s, 1),
                           "hard": False, "advice": ADVICE[key]})

    # 清晰度：有 baseline 就走相对，没有就给极宽的带只做提示
    if baseline is not None:
        d_db = 10 * math.log10((m["sharp"]["tenengrad"] + 1e-9) /
                               (baseline["sharp"]["tenengrad"] + 1e-9))
        s = saturate(d_db, -3.0, 0.0) * 100
        parts["sharp"] = {"raw": r4(d_db), "score": round(s, 1), "hard": False,
                          "note": "相对参考图的 dB 差（≥0 为不劣于参考）"}
        if s < 72:
            issues.append({"key": "sharp", "raw": r4(d_db), "score": round(s, 1),
                           "hard": False, "advice": ADVICE["sharp"]})
    else:
        parts["sharp"] = {"raw": r4(m["sharp"]["log_ten"]),
                          "score": round(band_graded(m["sharp"]["log_ten"], -4.8, -1.2, -2.6) * 100, 1),
                          "hard": False, "note": "无参考图，仅记录原始值，不作硬判"}

    cs = compose_score(m)
    parts["compose"] = {"raw": r4(m["compose"]["thirds_dist"]), "score": cs,
                        "hard": False, "note": "构图启发式，别当硬指标"}
    if cs < 60:
        issues.append({"key": "compose", "raw": r4(m["compose"]["thirds_dist"]),
                       "score": cs, "hard": False, "advice": ADVICE["compose"]})

    num = sum(parts[k]["score"] * WEIGHTS.get(k, 1.0) for k in parts)
    den = sum(WEIGHTS.get(k, 1.0) for k in parts) or 1.0
    total = round(num / den, 1)
    hard_fail = [i for i in issues if i.get("hard")]
    g = "D"
    for name, cut in GRADE_CUT:
        if total >= cut:
            g = name
            break
    if len(hard_fail) >= 2:
        g = "D" if g in ("A", "B") else g
    issues.sort(key=lambda x: (not x.get("hard"), x["score"]))
    return {"profile": P, "total": total, "grade": g, "hard_fail": len(hard_fail),
            "parts": parts, "issues": issues[:5]}


# ============================================================ 输出

def brief(m, s, show_palette=True):
    lines = [f"{m['name']}  {m['width']}×{m['height']}",
             f"  总分 {s['total']} ({s['grade']})"
             + (f"  硬门槛未过 {s['hard_fail']} 项" if s["hard_fail"] else "")]
    if show_palette:
        lines.append("  调色板 " + " ".join(c["hex"] for c in m["palette"]["colors"]))
    for k, v in sorted(s["parts"].items(), key=lambda kv: kv[1]["score"]):
        flag = "硬" if v.get("hard") else "  "
        lines.append(f"    [{flag}] {k:<13}{v['score']:>6.1f}   raw={v['raw']}")
    for it in s["issues"]:
        lines.append(f"   ! {it['key']}: {it['advice']}")
    return "\n".join(lines)


def cmd_score(a):
    files = expand(a.paths)
    base = metrics(a.baseline) if a.baseline else None
    rows = []
    for p in files:
        m = metrics(p)
        s = score(m, a.profile, base)
        rows.append({"file": m["file"], "size": [m["width"], m["height"]],
                     "palette": [c["hex"] for c in m["palette"]["colors"]],
                     "total": s["total"], "grade": s["grade"],
                     "hard_fail": s["hard_fail"], "parts": s["parts"],
                     "issues": [i["key"] for i in s["issues"]]})
        if not a.json:
            print(brief(m, s) + "\n")
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    return 0 if all(r["hard_fail"] == 0 and r["total"] >= 72 for r in rows) else 3


def cmd_pick(a):
    files = expand(a.paths)
    if len(files) < 2:
        print("pick 至少要两张候选图")
        return 2
    base = metrics(a.baseline) if a.baseline else None
    cands = []
    for p in files:
        m = metrics(p)
        s = score(m, a.profile, base)
        cands.append((m, s))
    # 排序：先看硬门槛，再看总分
    cands.sort(key=lambda t: (t[1]["hard_fail"], -t[1]["total"]))
    win_m, win_s = cands[0]
    out = {"profile": a.profile, "winner": win_m["file"], "winner_total": win_s["total"],
           "winner_grade": win_s["grade"],
           "ranking": [{"file": m["file"], "total": s["total"], "grade": s["grade"],
                        "hard_fail": s["hard_fail"],
                        "palette": [c["hex"] for c in m["palette"]["colors"]],
                        "issues": [i["key"] for i in s["issues"]]} for m, s in cands],
           "fix_plan": win_s["issues"]}
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print(f"候选 {len(cands)} 张 · profile={a.profile}\n")
        for i, (m, s) in enumerate(cands):
            tag = "★ 选它" if i == 0 else f"  #{i+1}"
            print(f"{tag}  {s['total']:>5.1f} {s['grade']}  {m['name']}"
                  + (f"   (硬门槛 {s['hard_fail']} 项未过)" if s["hard_fail"] else ""))
            print(f"        {' '.join(c['hex'] for c in m['palette']['colors'][:5])}")
        print(f"\n→ 用 {win_m['name']}，接着按下面修：")
        for it in win_s["issues"]:
            print(f"   ! {it['key']}: {it['advice']}")
        if not win_s["issues"]:
            print("   没有需要修的项，直接交付。")
    return 0 if win_s["hard_fail"] == 0 else 3


def cmd_compare(a):
    ref = metrics(a.ref)
    out = {"ref": ref["file"], "items": []}
    for p in expand(a.cands):
        m = metrics(p)
        s = score(m, a.profile, ref)
        deltas = {}
        for k in ("mean_luma", "range95", "mean_sat", "over_sat", "noise_sigma",
                  "hue_spread", "clip_high", "clip_low"):
            a_, b_ = _get(ref, k), _get(m, k)
            if a_ is None or b_ is None:
                continue
            better = (b_ < a_) if k in ("over_sat", "noise_sigma", "hue_spread",
                                        "clip_high", "clip_low") else abs(b_ - 0.5) < abs(a_ - 0.5)
            deltas[k] = {"ref": r4(a_), "cand": r4(b_), "delta": r4(b_ - a_),
                         "better": bool(better)}
        d_db = 10 * math.log10((m["sharp"]["tenengrad"] + 1e-9) /
                               (ref["sharp"]["tenengrad"] + 1e-9))
        deltas["sharp_db"] = {"delta": r4(d_db), "better": d_db >= 0}
        out["items"].append({"file": m["file"], "total": s["total"], "grade": s["grade"],
                             "win": sum(1 for v in deltas.values() if v["better"]),
                             "lose": sum(1 for v in deltas.values() if not v["better"]),
                             "deltas": deltas, "issues": [i["key"] for i in s["issues"]]})
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print(f"参考 {ref['name']}\n")
        for it in out["items"]:
            print(f"{os.path.basename(it['file'])}  总分 {it['total']} ({it['grade']})  "
                  f"胜 {it['win']} / 负 {it['lose']}")
            for k, v in it["deltas"].items():
                mark = "✔" if v["better"] else "✘"
                if "ref" in v:
                    print(f"   {mark} {k:<12} {v['ref']} → {v['cand']}   Δ{v['delta']:+}")
                else:
                    print(f"   {mark} {k:<12} Δ{v['delta']:+} dB")
    return 0


def cmd_palette(a):
    rgb, _ = load_rgb(a.image)
    pal = palette_of(rgb, k=a.n)
    if a.json:
        print(json.dumps(pal, ensure_ascii=False, indent=1))
    else:
        print(a.image)
        for c in pal["colors"]:
            print(f"  {c['hex']}  {c['share']*100:5.1f}%  {'█'*max(1,int(c['share']*40))}"
                  f"  hue={c['hue']:.0f}° sat={c['sat']:.2f}")
        print(f"  色相跨度 {pal['hue_spread']:.1f}°  有彩色 {pal['chromatic_count']} 个"
              f"  主色占 {pal['top_share']*100:.1f}%")
    if a.swatch:
        rgbim = Image.open(a.image).convert("RGB")
        rgbim.thumbnail((900, 900))
        CW, CH = 900, 150 + 90
        im = Image.new("RGB", (CW, CH), (251, 245, 233))
        from PIL import ImageDraw, ImageFont
        d = ImageDraw.Draw(im)
        try:
            fo = ImageFont.truetype(os.path.join(os.environ.get("WINDIR", r"C:\Windows"),
                                                 "Fonts", "msyh.ttc"), 20)
        except Exception:
            fo = ImageFont.load_default()
        x = 0
        for c in pal["colors"]:
            w = max(8, int(CW * c["share"]))
            d.rectangle([x, 0, x + w - 2, 148],
                        fill=tuple(int(c["hex"][i:i + 2], 16) for i in (1, 3, 5)))
            if w > 90:
                d.text((x + 8, 156), c["hex"], font=fo, fill=(46, 71, 86))
                d.text((x + 8, 182), f"{c['share']*100:.0f}%", font=fo, fill=(118, 105, 90))
            x += w
            if x > CW - 10:
                break
        os.makedirs(os.path.dirname(os.path.abspath(a.swatch)) or ".", exist_ok=True)
        im.save(a.swatch)
        print("色卡 ->", a.swatch)
    return 0


def cmd_series(a):
    files = expand(a.paths)
    ms = [metrics(p) for p in files]
    if len(ms) < 2:
        print("至少两张才能算一致性")
        return 2
    lums = np.array([m["expo"]["mean_luma"] for m in ms], np.float32)
    sats = np.array([m["color"]["mean_sat"] for m in ms], np.float32)
    hues = np.array([m["color"]["hue_mean"] for m in ms], np.float32)
    ten = np.array([m["sharp"]["log_ten"] for m in ms], np.float32)
    a_ = np.deg2rad(hues)
    R = math.hypot(float(np.cos(a_).mean()), float(np.sin(a_).mean()))
    hue_conc = math.degrees(math.sqrt(-2 * math.log(min(1.0, max(1e-6, R)))))
    reps = []
    for m in ms:
        s = score(m, a.profile)
        reps.append({"file": m["file"], "total": s["total"], "grade": s["grade"],
                     "palette": [c["hex"] for c in m["palette"]["colors"]],
                     "issues": [i["key"] for i in s["issues"]]})
    cons = (saturate(1.0 - float(lums.std()) / 0.14, 0, 1) * 0.35 +
            saturate(1.0 - float(sats.std()) / 0.13, 0, 1) * 0.25 +
            saturate(1.0 - hue_conc / 55.0, 0, 1) * 0.25 +
            saturate(1.0 - float(ten.std()) / 0.55, 0, 1) * 0.15)
    out = {"count": len(ms), "profile": a.profile,
           "consistency": r4(cons * 100),
           "score_avg": r4(float(np.mean([r["total"] for r in reps]))),
           "score_min": r4(float(np.min([r["total"] for r in reps]))),
           "luma_std": r4(lums.std()), "luma_range": [r4(lums.min()), r4(lums.max())],
           "sat_std": r4(sats.std()), "hue_concentration_deg": r4(hue_conc),
           "sharp_std": r4(ten.std()), "items": reps}
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print(f"共 {out['count']} 张 · profile={a.profile}")
        print(f"  一致性 {out['consistency']}/100   平均分 {out['score_avg']}   最低 {out['score_min']}")
        print(f"  亮度离散 {out['luma_std']} ({out['luma_range'][0]}–{out['luma_range'][1]})"
              f"   饱和离散 {out['sat_std']}   色相集中 {out['hue_concentration_deg']}°"
              f"   清晰度离散 {out['sharp_std']}")
        for r in sorted(reps, key=lambda x: x["total"]):
            print(f"    {r['total']:>5.1f} {r['grade']}  {os.path.basename(r['file']):<32}"
                  f"{' '.join(r['palette'][:4])}")
        if out["consistency"] < 70:
            print("  ! 不成套：vfix.py unify --ref <最好那张> 统一亮度与调色板，再 series 复评。")
    return 0 if out["consistency"] >= 70 else 3


def srgb_lin(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def wcag_lum(rgb):
    """WCAG 相对亮度（必须做 sRGB 反 gamma，否则对比度会被严重低估）"""
    r, g, b = srgb_lin(rgb[..., 0]), srgb_lin(rgb[..., 1]), srgb_lin(rgb[..., 2])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def hex_to_rgb01(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)


def cmd_textsafe(a):
    im = Image.open(a.image).convert("RGB")
    x, y, w, h = [int(v) for v in a.box.split(",")]
    x2, y2 = min(im.width, x + w), min(im.height, y + h)
    crop = np.asarray(im.crop((max(0, x), max(0, y), x2, y2)), np.float32) / 255.0
    if crop.size == 0:
        print("box 超出画面")
        return 2
    # 背景色：逐通道中位数（比整体均值更接近真实底色）
    flat = crop.reshape(-1, 3)
    bg_rgb = np.median(flat, axis=0)
    bg_l = float(wcag_lum(bg_rgb))
    txt_rgb = hex_to_rgb01(a.text)
    txt_l = float(wcag_lum(txt_rgb))
    ratio = (max(bg_l, txt_l) + 0.05) / (min(bg_l, txt_l) + 0.05)
    # 底噪只量「背景像素」：取离中位色最近的 55%，否则文字笔画本身会把 std 顶高
    dist = np.linalg.norm(flat - bg_rgb, axis=1)
    bg_mask = dist <= np.percentile(dist, 55)
    busy = float(wcag_lum(flat[bg_mask]).std()) if bg_mask.any() else 0.0
    verdict = "ok" if (ratio >= 4.5 and busy < 0.10) else ("warn" if ratio >= 3.0 else "bad")
    out = {"box": [x, y, w, h],
           "bg_hex": "#%02X%02X%02X" % tuple(int(v * 255) for v in bg_rgb),
           "text_hex": a.text if a.text.startswith("#") else "#" + a.text,
           "bg_lum": r4(bg_l), "text_lum": r4(txt_l),
           "contrast_ratio": r4(ratio), "bg_busy": r4(busy),
           "wcag_aa": bool(ratio >= 4.5), "wcag_aa_large": bool(ratio >= 3.0),
           "verdict": verdict,
           "advice": ("文字可读性没问题。" if verdict == "ok" else
                      ("底太花，文字会被吃掉：给文字加 0.75 以上不透明度的衬底，"
                       "或换到更干净的区块。" if busy >= 0.10 else
                       "对比度不足：换更深的文字色，或加深色衬底。"))}
    print(json.dumps(out, ensure_ascii=False, indent=1) if a.json else
          f"底 {out['bg_hex']}(L={out['bg_lum']})  字 {out['text_hex']}(L={out['text_lum']})\n"
          f"对比度 {out['contrast_ratio']}:1  底噪 {out['bg_busy']}  → {verdict}"
          f"  (AA 4.5:1 {'过' if out['wcag_aa'] else '不过'})\n  {out['advice']}")
    return 0 if verdict == "ok" else 3


def cmd_report(a):
    files = expand(a.paths)
    outdir = os.path.dirname(os.path.abspath(a.out))
    os.makedirs(os.path.join(outdir, "thumbs"), exist_ok=True)
    rows = []
    for i, p in enumerate(files):
        m = metrics(p)
        s = score(m, a.profile)
        t = Image.open(p).convert("RGB")
        t.thumbnail((420, 420), Image.LANCZOS)
        tn = f"thumbs/{i:03d}.jpg"
        t.save(os.path.join(outdir, tn), quality=82)
        rows.append((m, s, tn))
    rows.sort(key=lambda r: r[1]["total"])
    h = ["<!doctype html><meta charset='utf-8'><title>vqc 报告</title>",
         "<style>body{font:14px/1.6 'Microsoft YaHei',sans-serif;background:#FBF5E9;"
         "color:#40372E;margin:0;padding:24px}h1{font-size:20px}"
         ".c{display:flex;gap:16px;background:#fff;border-radius:10px;padding:14px;margin:10px 0;"
         "box-shadow:0 4px 14px rgba(64,55,46,.10)}img{width:300px;height:auto;border-radius:6px}"
         ".g{display:inline-block;padding:2px 10px;border-radius:99px;color:#fff;font-weight:700}"
         ".A{background:#5C7658}.B{background:#7E9B76}.C{background:#E4744A}.D{background:#C9483D}"
         "table{border-collapse:collapse;font-size:13px}td{padding:2px 10px 2px 0}"
         ".i{color:#C9483D}</style>",
         f"<h1>画面质量报告 · profile={a.profile} · {len(rows)} 张</h1>"]
    for m, s, tn in rows:
        parts = "".join(f"<tr><td>{k}</td><td><b>{v['score']:.0f}</b></td>"
                        f"<td>= {v['raw']}</td></tr>"
                        for k, v in sorted(s["parts"].items(), key=lambda kv: kv[1]["score"]))
        iss = "".join(f"<li class='i'>{it['key']} — {it['advice']}</li>" for it in s["issues"])
        h.append(f"<div class='c'><img src='{tn}'><div>"
                 f"<div><span class='g {s['grade']}'>{s['grade']}</span> "
                 f"<b style='font-size:18px'>{s['total']}</b> "
                 f"<span style='color:#76695A'>{m['name']} · {m['width']}×{m['height']} · "
                 f"{' '.join(c['hex'] for c in m['palette']['colors'][:5])}</span></div>"
                 f"<table>{parts}</table><ul>{iss}</ul></div></div>")
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(h))
    print("报告 ->", a.out)
    return 0


def expand(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            for ext in ("png", "jpg", "jpeg", "webp", "bmp", "tif", "tiff"):
                out += sorted(_glob.glob(os.path.join(p, f"*.{ext}")))
                out += sorted(_glob.glob(os.path.join(p, f"*.{ext.upper()}")))
        elif any(ch in p for ch in "*?["):
            out += sorted(_glob.glob(p, recursive=True))
        else:
            out.append(p)
    seen, res = set(), []
    for p in out:
        k = os.path.abspath(p)
        if k not in seen and os.path.isfile(p):
            seen.add(k)
            res.append(p)
    return res


def main():
    ap = argparse.ArgumentParser(description="豆包视觉计算内核 · 画面质量量化")
    sub = ap.add_subparsers(dest="cmd", required=True)
    prof = ["default", "poster", "product", "illustration", "video_frame"]

    p = sub.add_parser("score"); p.add_argument("paths", nargs="+")
    p.add_argument("--profile", default="default", choices=prof)
    p.add_argument("--baseline"); p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_score)

    p = sub.add_parser("pick"); p.add_argument("paths", nargs="+")
    p.add_argument("--profile", default="default", choices=prof)
    p.add_argument("--baseline"); p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_pick)

    p = sub.add_parser("compare"); p.add_argument("ref"); p.add_argument("cands", nargs="+")
    p.add_argument("--profile", default="default", choices=prof)
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_compare)

    p = sub.add_parser("palette"); p.add_argument("image")
    p.add_argument("--n", type=int, default=6); p.add_argument("--swatch")
    p.add_argument("--json", action="store_true"); p.set_defaults(fn=cmd_palette)

    p = sub.add_parser("series"); p.add_argument("paths", nargs="+")
    p.add_argument("--profile", default="default", choices=prof)
    p.add_argument("--json", action="store_true"); p.set_defaults(fn=cmd_series)

    p = sub.add_parser("textsafe"); p.add_argument("image")
    p.add_argument("--box", required=True); p.add_argument("--text", default="#2E4756")
    p.add_argument("--json", action="store_true"); p.set_defaults(fn=cmd_textsafe)

    p = sub.add_parser("report"); p.add_argument("paths", nargs="+")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--profile", default="default", choices=prof)
    p.set_defaults(fn=cmd_report)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
