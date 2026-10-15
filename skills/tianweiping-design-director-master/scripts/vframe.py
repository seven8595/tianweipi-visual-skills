#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""豆包视觉计算内核 —— 视频帧质检脚本 (vframe.py)

用途
----
AI 生成的视频常见几类「肉眼能看出、但说不清在第几帧」的毛病：帧间亮度/色相跳变
（闪烁）、卡帧（画面连续几帧不动）、整体偏色或逐渐变暗、局部撕裂。本脚本把视频
抽成 PNG 帧序列，逐帧量化光色统计量，再差分定位问题帧，让人不看视频也能定位。

四个子命令
----------
1) extract  抽帧      : 用 ffmpeg 把视频按 --fps 抽成 %05d.png 序列
2) analyze  帧序列分析: 逐帧算 luma / 饱和度 / 色相直方图，做相邻帧差分，给判定
3) sheet    联络表    : 把帧拼成网格图，用来一眼通览全片
4) strip    定点抽帧  : 按给定秒数各抽一帧，用于逐点对比

指标含义（analyze）
------------------
* luma            : 亮度。线性 sRGB 系数 0.2126R + 0.7152G + 0.0722B 在整帧上的均值，
                    取值 0~1。用的是逐帧均值，所以对整帧忽明忽暗最敏感。
* dluma           : 相邻帧亮度差绝对值 |luma[i] - luma[i-1]|，单位同 luma；dluma[0] 恒为 0.0
                    （首帧没有前一帧可比，只是占位，不参与闪烁/卡帧判定）。
                    它本身就是「闪烁」的度量：画面内容正常推进时 dluma 很小，
                    只有整帧亮度被整体抬升/压低时才会突然变大。
* sat             : 饱和度均值，逐像素 max(R,G,B) - min(R,G,B) 的均值，0~1。
* hue             : 色相。按饱和度加权做 12 桶直方图后再取圆均值（单位：度，
                    0~360），不是简单算术平均 —— 色相是角度量，跳过 0/360 边界
                    时算术平均会给出完全错误的答案（350° 和 10° 的算术平均是
                    180°，圆均值才是 0°）。
* hue_std         : 色相序列的圆标准差（度）。由圆统计的合成向量长度 R 反推：
                    std = sqrt(-2 ln R)（弧度）→ 角度。R 越接近 1 说明全片色相
                    越稳定；偏色漂移会让它变大。
* luma_drift      : 末帧 luma - 首帧 luma。正数=整体变亮，负数=整体变暗。
* hue_jump_max    : 相邻帧色相的最大跳变量（度，圆夹角 0~180）。hue_std 是全片统计量，
                    单帧偏色闪一下会被它平均掉；这一项专门兜住「就那一帧发紫」的情况。
* luma_trend      : 对 luma 序列做最小二乘拟合得到的斜率（每帧变化量）。
                    它比 luma_drift 稳健：中间抖一下不会带偏趋势。
* flicker_frames  : dluma > --flicker 的帧号列表（1-based 帧序号）。第 i 帧被列出，
                    表示「第 i 帧相对第 i-1 帧亮度跳变超标」，即一次亮度跳变的落点帧。
                    一段连续 n 帧的高/低亮度（滤镜 between(n,a,b) 那种）会在进入和退出
                    各留下一个落点帧，所以通常成对出现，例如 [4, 7]。
* freeze_runs     : 卡帧区间，报告成 [起帧, 止帧]（1-based）。判据是「连续 >= --freeze-run
                    帧两两之间 dluma < --freeze」，即画面连续 N 帧没动；区间长度就是
                    不动的帧数。例：帧 1,2,3 完全一样、帧 4 才变，--freeze-run 3 报 [1, 3]。
* worst_frames    : dluma 最大的前 5 帧（帧号 + 数值），无论阈值如何都给出，
                    便于给「差得最狠的地方」排优先级。
* verdict         : ok / warn / bad，判定规则写死在 _verdict() 里并在该函数注释中说明。

环境
----
* Python 3.12 + numpy + Pillow，仅用标准库 + numpy + PIL，ffmpeg/ffprobe 走 subprocess。
* 全部 subprocess 都用列表参数、shell=False、UTF-8 解码、errors="replace"，
  路径含中文/空格也能跑通。
* 所有对外输出的数值统一保留 4 位小数（JSON 里用定点记法，不会出现科学计数法）。
"""

from __future__ import annotations

import argparse
import glob as globmod
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
from PIL import Image, ImageDraw

# ---------------------------------------------------------------------------
# 外部工具绝对路径
# ---------------------------------------------------------------------------
PYTHON_EXE = r"C:\Users\seven\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
FFMPEG_DIR = (
    r"C:\Users\seven\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-9.0.2-full_build\bin"
)
FFMPEG = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
FFPROBE = os.path.join(FFMPEG_DIR, "ffprobe.exe")

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
ANALYZE_MAX_SIDE = 512          # analyze 时逐帧缩到长边 <= 512
LUMA_W = (0.2126, 0.7152, 0.0722)
HUE_BINS = 12                   # 色相直方图桶数
HUE_BIN_DEG = 360.0 / HUE_BINS  # 每桶 30 度
SHEET_CELL_DEFAULT = 320
SHEET_COLS_DEFAULT = 6
SHEET_GAP = 4                   # 格间距 4px
SHEET_BG = (251, 245, 233)      # #FBF5E9
DEFAULT_TIMEOUT = 600           # 单次 ffmpeg/ffprobe 调用的超时（秒）
NDIGITS = 4                     # 所有外部数值统一 4 位小数


# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------
def _setup_io() -> None:
    """Windows 控制台是 GBK，含中文/符号的输出会炸，统一切 UTF-8。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass


def _child_env() -> dict:
    """子进程环境：强制 Python 子进程不要用 GBK，避免中文路径乱码。"""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8:replace"
    env["PYTHONUTF8"] = "1"
    return env


def _run(cmd: Sequence[str], timeout: int = DEFAULT_TIMEOUT) -> subprocess.CompletedProcess:
    """统一的外部命令调用：列表参数 + shell=False + UTF-8 + errors=replace。"""
    result = subprocess.run(
        list(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        env=_child_env(),
    )
    # 显式解码，绕开 locale；errors="replace" 保证任何脏字节都不会抛 UnicodeDecodeError
    result.out = result.stdout.decode("utf-8", errors="replace")  # type: ignore[attr-defined]
    result.err = result.stderr.decode("utf-8", errors="replace")  # type: ignore[attr-defined]
    return result


def _tool(path: str, name: str) -> str:
    if not os.path.isfile(path):
        raise SystemExit(f"[vframe] 找不到 {name}：{path}")
    return path


def _tail(text: str, lines: int = 12) -> str:
    parts = [ln for ln in (text or "").splitlines() if ln.strip()]
    return "\n".join(parts[-lines:])


def _run_ffmpeg(args: Sequence[str], timeout: int = DEFAULT_TIMEOUT) -> None:
    """跑一次 ffmpeg；失败时把 ffmpeg 的 stderr 尾部带出来，方便定位。"""
    cmd = [_tool(FFMPEG, "ffmpeg"), "-hide_banner", "-nostdin", "-loglevel", "error"] + list(args)
    try:
        result = _run(cmd, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise SystemExit(f"[vframe] ffmpeg 超时（>{timeout}s）：{' '.join(cmd)}")
    if result.returncode != 0:
        raise SystemExit(
            "[vframe] ffmpeg 执行失败（exit=%d）\n命令: %s\n%s"
            % (result.returncode, " ".join(cmd), _tail(result.err))
        )


def _probe_size(video: str, timeout: int = DEFAULT_TIMEOUT) -> tuple[int | None, int | None]:
    """用 ffprobe 读视频宽高，读不到返回 (None, None)。"""
    cmd = [
        _tool(FFPROBE, "ffprobe"),
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json",
        video,
    ]
    try:
        result = _run(cmd, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return None, None
    if result.returncode != 0:
        return None, None
    try:
        streams = json.loads(result.out).get("streams") or []
        if not streams:
            return None, None
        width = int(streams[0].get("width") or 0)
        height = int(streams[0].get("height") or 0)
    except (ValueError, TypeError, json.JSONDecodeError):
        return None, None
    if width <= 0 or height <= 0:
        return None, None
    return width, height


def _probe_duration(video: str, timeout: int = DEFAULT_TIMEOUT) -> float | None:
    """用 ffprobe 读视频时长（秒），读不到返回 None。"""
    cmd = [
        _tool(FFPROBE, "ffprobe"),
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        video,
    ]
    try:
        result = _run(cmd, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return None
    if result.returncode != 0:
        return None
    try:
        raw = (json.loads(result.out).get("format") or {}).get("duration")
        value = float(raw)
    except (ValueError, TypeError, json.JSONDecodeError):
        return None
    if not math.isfinite(value) or value <= 0:
        return None
    return value


def _scale_filter(scale: int, src_w: int | None, src_h: int | None) -> str | None:
    """按长边缩放：scale>0 且能探测到源尺寸时返回 ffmpeg scale 滤镜表达式。

    宽高都向偶数取整（yuv420p 要求偶数，libx264 遇到奇数会直接报错）。
    """
    if scale <= 0 or not src_w or not src_h:
        return None
    long_side = max(src_w, src_h)
    factor = float(scale) / float(long_side)
    out_w = max(2, int(round(src_w * factor)))
    out_h = max(2, int(round(src_h * factor)))
    out_w -= out_w % 2
    out_h -= out_h % 2
    out_w = max(2, out_w)
    out_h = max(2, out_h)
    return f"scale={out_w}:{out_h}:flags=lanczos"


def _fmt(value: float) -> float:
    """所有对外数值统一保留 4 位小数。"""
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return 0.0
    return round(float(value), NDIGITS)


def _fmt_list(values: Iterable[float]) -> list[float]:
    return [_fmt(v) for v in values]


class _FixedFloatEncoder(json.JSONEncoder):
    """固定 4 位小数的 JSON 编码器：保证 0.06 写成 0.0600，比对时不用心算位数。"""

    def default(self, o: Any) -> Any:  # pragma: no cover - 兜底
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return _fmt(float(o))
        if isinstance(o, np.ndarray):
            return [_fmt(float(v)) for v in o.tolist()]
        return super().default(o)

    def encode(self, o: Any) -> str:
        return super().encode(_round_tree(o))


def _round_tree(obj: Any) -> Any:
    if isinstance(obj, float):
        return _Fixed4(obj)
    if isinstance(obj, dict):
        return {k: _round_tree(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_round_tree(v) for v in obj]
    if isinstance(obj, (np.floating,)):
        return _Fixed4(float(obj))
    if isinstance(obj, (np.integer,)):
        return int(obj)
    return obj


class _Fixed4(float):
    """round(x, 4) 的 float 子类，把 JSON 里的 repr 固定成 4 位小数定点写法。"""

    def __repr__(self) -> str:
        return f"{self:.{NDIGITS}f}"


def _dump_json(obj: Any) -> str:
    return json.dumps(_round_tree(obj), ensure_ascii=False, cls=_FixedFloatEncoder, indent=2)


# ---------------------------------------------------------------------------
# 帧文件发现 / 排序
# ---------------------------------------------------------------------------
def _natural_key(name: str) -> tuple:
    """自然排序键：s2 < s10（纯字典序会反过来）。"""
    parts = re.split(r"(\d+)", name)
    key = []
    for part in parts:
        if part.isdigit():
            key.append((1, int(part), ""))
        elif part:
            key.append((0, 0, part.lower()))
    return tuple(key)


def _frame_sort_key(path: str) -> tuple:
    """优先用文件名里最后一串数字排序（抽帧结果都是 00001.png 这种）。

    这样 1.png / 2.png / 10.png 与 00001.png / 00010.png 都能排对。
    """
    stem = Path(path).stem
    nums = re.findall(r"\d+", stem)
    if nums:
        return (0, int(nums[-1]), _natural_key(Path(path).name))
    return (1, 0, _natural_key(Path(path).name))


def _collect_frames(target: str) -> list[str]:
    """<dir|glob> -> 排序后的帧文件列表。目录取 *.png（大小写不敏感）。"""
    expanded = os.path.expanduser(os.path.expandvars(target))
    if os.path.isdir(expanded):
        found = globmod.glob(os.path.join(expanded, "*.png"))
        found += globmod.glob(os.path.join(expanded, "*.PNG"))
        found = list(dict.fromkeys(found))
    else:
        found = globmod.glob(expanded, recursive=True)
        if not found:
            found = globmod.glob(os.path.join(expanded, "*.png"))
    files = [f for f in found if os.path.isfile(f)]
    if not files:
        raise SystemExit(f"[vframe] 没有匹配到任何帧文件：{target}")
    return sorted(files, key=_frame_sort_key)


def _find_pngs(directory: str) -> list[str]:
    found = globmod.glob(os.path.join(directory, "*.png"))
    found += globmod.glob(os.path.join(directory, "*.PNG"))
    return sorted(list(dict.fromkeys(found)), key=_frame_sort_key)


# ---------------------------------------------------------------------------
# 逐帧光色统计
# ---------------------------------------------------------------------------
def load_frame(path: str, max_side: int = ANALYZE_MAX_SIDE) -> np.ndarray:
    """读一帧 -> 长边缩到 <= max_side -> float32 RGB，取值 [0, 1]。"""
    with Image.open(path) as img:
        img = img.convert("RGB")
        width, height = img.size
        long_side = max(width, height)
        if long_side > max_side:
            factor = max_side / float(long_side)
            new_size = (max(1, int(round(width * factor))), max(1, int(round(height * factor))))
            img = img.resize(new_size, Image.LANCZOS)
        array = np.asarray(img, dtype=np.float32) / 255.0
    if array.ndim == 2:  # 灰度图兜底
        array = np.stack([array] * 3, axis=-1)
    return array


def frame_stats(rgb: np.ndarray) -> dict:
    """单帧统计：luma 均值、饱和度均值、色相直方图 + 直方图圆均值。"""
    luma = float(np.mean(rgb[..., 0] * LUMA_W[0] + rgb[..., 1] * LUMA_W[1] + rgb[..., 2] * LUMA_W[2]))

    r = rgb[..., 0]
    g = rgb[..., 1]
    b = rgb[..., 2]
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    sat = mx - mn                                                  # HSV 的 S（V=1 时）
    sat_mean = float(np.mean(sat))

    delta = mx - mn
    hue = np.zeros_like(mx)
    nz = delta > 1e-6                                              # 灰色像素无色相，权重为 0
    if np.any(nz):
        rn, gn, bn, dn = r[nz], g[nz], b[nz], delta[nz]
        h = np.zeros_like(dn)
        mr = (mx[nz] == rn)
        mg = (mx[nz] == gn) & (~mr)
        mb = (~mr) & (~mg)
        h[mr] = ((gn[mr] - bn[mr]) / dn[mr]) % 6.0
        h[mg] = ((bn[mg] - rn[mg]) / dn[mg]) + 2.0
        h[mb] = ((rn[mb] - gn[mb]) / dn[mb]) + 4.0
        hue[nz] = (h * 60.0) % 360.0

    weights = sat[nz]
    hist, _ = np.histogram(
        hue[nz],
        bins=HUE_BINS,
        range=(0.0, 360.0),
        weights=weights,
    )
    total = float(hist.sum())
    if total > 0:
        hist = hist / total                                       # 归一化，便于跨帧比较

    return {
        "luma": luma,
        "sat": sat_mean,
        "hue": _hist_circular_mean(hist),
        "hist": hist,
    }


def _hist_circular_mean(hist: np.ndarray) -> float:
    """12 桶色相直方图 -> 圆均值（度）。权重是各桶的饱和度加权占比。

    桶 i 的中心角 = i * 30 度。先算合成向量 (C, S)，再 atan2 回角度。
    合成向量长度为 0（例如整帧全灰）时返回 0.0。
    """
    centres = (np.arange(HUE_BINS) + 0.5) * HUE_BIN_DEG
    rad = np.deg2rad(centres)
    c = float(np.sum(hist * np.cos(rad)))
    s = float(np.sum(hist * np.sin(rad)))
    if abs(c) < 1e-12 and abs(s) < 1e-12:
        return 0.0
    return float(math.degrees(math.atan2(s, c)) % 360.0)


def _circular_std_deg(hues: Sequence[float], weights: Sequence[float] | None = None) -> float:
    """角度序列的圆标准差（度）。

    R = |加权合成向量| / 总权重；std = sqrt(-2 ln R)（弧度）换算成度。
    R -> 1 表示方向高度一致（std -> 0），R -> 0 表示方向散乱（std 变大）。
    """
    if len(hues) == 0:
        return 0.0
    rad = np.deg2rad(np.asarray(hues, dtype=np.float64))
    w = np.ones(len(hues), dtype=np.float64) if weights is None else np.asarray(weights, dtype=np.float64)
    total = float(w.sum())
    if total <= 0:
        return 0.0
    c = float(np.sum(w * np.cos(rad)) / total)
    s = float(np.sum(w * np.sin(rad)) / total)
    r = math.hypot(c, s)
    if r >= 1.0:
        return 0.0
    if r <= 1e-12:
        return 180.0
    return float(math.degrees(math.sqrt(-2.0 * math.log(r))))


def _hue_diff_deg(a: float, b: float) -> float:
    """两角度的最短夹角（0~180 度），处理 0/360 边界。"""
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


def _least_squares_slope(series: Sequence[float]) -> float:
    """最小二乘斜率（每帧变化量）。点数 < 2 或 x 无变化时返回 0。"""
    n = len(series)
    if n < 2:
        return 0.0
    x = np.arange(n, dtype=np.float64)
    y = np.asarray(series, dtype=np.float64)
    xm = float(x.mean())
    ym = float(y.mean())
    denom = float(np.sum((x - xm) ** 2))
    if denom <= 0:
        return 0.0
    return float(np.sum((x - xm) * (y - ym)) / denom)


# ---------------------------------------------------------------------------
# 判定
# ---------------------------------------------------------------------------
def _verdict(
    n: int,
    flicker_frames: Sequence[int],
    freeze_runs: Sequence[Sequence[int]],
    luma_trend: float,
    hue_std: float,
    saturation_mean: float,
    hue_jump_max: float,
    flicker_thr: float,
    freeze_thr: float,
    freeze_run: int,
) -> tuple[str, list[str]]:
    """写死的判定规则（返回 verdict 和触发的规则说明）。

    bad（任一命中）：
      R1 闪烁帧占比 > 5%                       —— 大面积帧间亮度跳变
      R2 卡帧区间总长（帧数之和）> 总帧数 20%  —— 画面大段不动
      R3 |luma_trend| > 0.010 且 |luma_drift| > 0.05
                                               —— 明显单调变暗/变亮（趋势陡 + 总位移大）
      R4 hue_std > 25 度 且 饱和度均值 > 0.05  —— 全片色相明显漂移/翻转（低饱和时不算）
      R5 最长单个卡帧区间 > 总帧数 35%         —— 单次超长静止
      R6 相邻帧色相最大跳变 > 30 度 且 有色彩  —— 单帧偏色闪一下（hue_std 会被平均掉，靠这条兜住）
    warn（未 bad 时任一命中）：
      W1 闪烁帧占比 > 1%
      W2 存在卡帧区间（>= 1 段）
      W3 |luma_trend| > 0.002
      W4 hue_std > 8 度 且 饱和度均值 > 0.05
      W5 相邻帧色相最大跳变 > 15 度 且 有色彩
    否则 ok。规则是保守的：先把最刺眼的 bad 抓出来，边缘情况降级到 warn。
    """
    notes: list[str] = []
    if n <= 1:
        return "ok", ["帧数不足 2，无法做帧间差分"]

    flicker_ratio = len(flicker_frames) / float(n)
    freeze_total = sum(int(run[1]) - int(run[0]) + 1 for run in freeze_runs)
    freeze_ratio = freeze_total / float(n)
    longest_run = max((int(run[1]) - int(run[0]) + 1 for run in freeze_runs), default=0)

    bad = False
    warn = False

    if flicker_ratio > 0.05:
        bad = True
        notes.append(f"R1 闪烁帧占比 {flicker_ratio * 100:.1f}% > 5%")
    elif flicker_ratio > 0.01:
        warn = True
        notes.append(f"W1 闪烁帧占比 {flicker_ratio * 100:.1f}% > 1%")

    if freeze_ratio > 0.20:
        bad = True
        notes.append(f"R2 卡帧区间总长占比 {freeze_ratio * 100:.1f}% > 20%")
    elif freeze_runs:
        warn = True
        notes.append(f"W2 存在 {len(freeze_runs)} 段卡帧（合计 {freeze_total} 帧 / {freeze_ratio * 100:.1f}%）")

    drift = float(luma_trend) * max(1, n - 1)
    if abs(luma_trend) > 0.010 and abs(drift) > 0.05:
        bad = True
        notes.append(f"R3 亮度趋势陡（trend={luma_trend:+.4f}/帧，全程约 {drift:+.4f}）")
    elif abs(luma_trend) > 0.002:
        warn = True
        notes.append(f"W3 亮度有缓慢漂移（trend={luma_trend:+.4f}/帧）")

    if hue_std > 25.0 and saturation_mean > 0.05:
        bad = True
        notes.append(f"R4 色相不稳定（hue_std={hue_std:.1f} 度 > 25 度，且有色彩）")
    elif hue_std > 8.0 and saturation_mean > 0.05:
        warn = True
        notes.append(f"W4 色相有波动（hue_std={hue_std:.1f} 度）")

    if longest_run > 0.35 * n:
        bad = True
        notes.append(f"R5 单段卡帧长达 {longest_run} 帧 > 总帧数 35%")

    if hue_jump_max > 30.0 and saturation_mean > 0.05:
        bad = True
        notes.append(f"R6 相邻帧色相最大跳变 {hue_jump_max:.1f} 度 > 30 度（单帧偏色）")
    elif hue_jump_max > 15.0 and saturation_mean > 0.05:
        warn = True
        notes.append(f"W5 相邻帧色相最大跳变 {hue_jump_max:.1f} 度 > 15 度")

    if bad:
        return "bad", notes
    if warn:
        return "warn", notes
    return "ok", ["各项指标均在阈值内"]


# ---------------------------------------------------------------------------
# analyze
# ---------------------------------------------------------------------------
def analyze(
    target: str,
    flicker_thr: float = 0.06,
    freeze_thr: float = 0.004,
    freeze_run: int = 3,
    max_side: int = ANALYZE_MAX_SIDE,
) -> dict:
    """<dir|glob> -> 质检报告 dict（字段名即 CLI 约定）。"""
    if freeze_run < 2:
        raise SystemExit("[vframe] --freeze-run 必须 >= 2（要判定「连续 N 帧没动」至少要比 1 帧多）")
    files = _collect_frames(target)
    n = len(files)

    lumas: list[float] = []
    sats: list[float] = []
    hues: list[float] = []
    hists: list[np.ndarray] = []
    for path in files:
        stats = frame_stats(load_frame(path, max_side=max_side))
        lumas.append(stats["luma"])
        sats.append(stats["sat"])
        hues.append(stats["hue"])
        hists.append(stats["hist"])

    # 相邻帧差分：dluma[k] 对应第 (k+2) 帧相对第 (k+1) 帧的变化，首帧记为 0
    dluma = [0.0] * n
    for i in range(1, n):
        dluma[i] = abs(lumas[i] - lumas[i - 1])

    flicker_frames = [i + 1 for i in range(1, n) if dluma[i] > flicker_thr]

    # 卡帧区间。约定（全脚本统一，1-based 帧号）：
    #   dluma[i] = |luma[i] - luma[i-1]|，即「第 i 帧相对第 i-1 帧的跳变量」，
    #   dluma[0] 恒为 0.0（首帧没有前一帧可比，它只是一个占位值，不参与任何判定）。
    #   "帧 i 与帧 i-1 是同一画面"  <=>  dluma[i] < freeze_thr。
    #   于是 freeze_run 个连续同画面帧 = (freeze_run - 1) 个连续小 dluma。
    # 所以这里判 run_len >= freeze_run - 1，并把 run 前面的那帧一起圈进区间：
    #   帧 1,2,3 全同、帧 4 变  -> 区间 [1, 3]（长度 3 = freeze_run，画面确实 3 帧没动）
    #   9 帧全同                -> 区间 [1, 9]
    # 首帧不会被漏掉：run_len 从 1 开始计（隐含 dluma[0] 这个占位值视为"没跳"），
    # 但只有当 dluma[1] 也 < 阈值时才可能凑够 freeze_run-1。
    # 另外绝不能每满一个窗口就 push 一段，否则会出现 [1,3] [1,4] 这种重叠段。
    freeze_runs: list[list[int]] = []
    run_len = 1                                   # 隐含占位：当前这段已有 1 帧（第 i 帧自己）
    for i in range(1, n):
        if dluma[i] < freeze_thr:
            run_len += 1                          # 同画面，延长当前段
            if run_len >= freeze_run:
                start = i - run_len + 2           # 段首帧（1-based）
                end = i + 1                       # 段尾帧（1-based）
                if run_len == freeze_run:
                    freeze_runs.append([start, end])         # 首次达标：新开一段
                else:
                    freeze_runs[-1][1] = end                 # 之后每帧延长上一段
        else:
            run_len = 1                           # 断了，从当前帧重新起一段
    freeze_runs_l = [[int(a), int(b)] for a, b in freeze_runs]

    luma_drift = lumas[-1] - lumas[0] if n >= 2 else 0.0
    luma_trend = _least_squares_slope(lumas)
    hue_std = _circular_std_deg(hues)

    # 相邻帧色相跳变（圆夹角，处理 0/360 边界）。低饱和帧的 hue 没意义，跳过不计。
    hue_jump_max = 0.0
    hue_jump_frames: list[list[int]] = []
    for i in range(1, n):
        if sats[i] <= 0.05 or sats[i - 1] <= 0.05:
            continue
        diff = _hue_diff_deg(hues[i], hues[i - 1])
        if diff > hue_jump_max:
            hue_jump_max = diff
        if diff > 15.0:
            hue_jump_frames.append([i + 1, _fmt(diff)])

    order = sorted(range(1, n), key=lambda i: dluma[i], reverse=True)[:5]
    worst_frames = [[i + 1, _fmt(dluma[i])] for i in order]

    mean_luma = float(np.mean(lumas)) if lumas else 0.0
    mean_sat = float(np.mean(sats)) if sats else 0.0
    verdict, notes = _verdict(
        n, flicker_frames, freeze_runs_l, luma_trend, hue_std, mean_sat, hue_jump_max,
        flicker_thr, freeze_thr, freeze_run,
    )

    report: dict[str, Any] = {
        "frames": n,
        "dir": os.path.dirname(os.path.abspath(files[0])).replace("\\", "/"),
        "flicker_frames": [int(v) for v in flicker_frames],
        "freeze_runs": freeze_runs_l,
        "luma_drift": _fmt(luma_drift),
        "luma_trend": _fmt(luma_trend),
        "hue_std": _fmt(hue_std),
        "worst_frames": worst_frames,
        "verdict": verdict,
        # 以下为佐证/调参用的附加字段
        "hue_jump_max": _fmt(hue_jump_max),
        "hue_jump_frames": hue_jump_frames,
        "mean_luma": _fmt(mean_luma),
        "mean_sat": _fmt(mean_sat),
        "luma_min": _fmt(min(lumas) if lumas else 0.0),
        "luma_max": _fmt(max(lumas) if lumas else 0.0),
        "luma_series": _fmt_list(lumas),
        "dluma_series": _fmt_list(dluma),
        "sat_series": _fmt_list(sats),
        "hue_series": _fmt_list(hues),
        "hue_hist": [
            {"bin": b + 1, "hue": _fmt((b + 0.5) * HUE_BIN_DEG), "w": _fmt(float(np.mean([h[b] for h in hists])))}
            for b in range(HUE_BINS)
        ],
        "thresholds": {
            "flicker": _fmt(flicker_thr),
            "freeze": _fmt(freeze_thr),
            "freeze_run": int(freeze_run),
            "max_side": int(max_side),
        },
        "notes": notes,
    }
    return report


def _print_analyze_text(report: dict, files: Sequence[str]) -> None:
    """人类可读表格 + 一行结论。"""
    print(f"[vframe] 分析目录 : {report['dir']}")
    print(f"[vframe] 帧数     : {report['frames']}")
    print(f"[vframe] 缩放长边 : {report['thresholds']['max_side']}  (逐帧 PIL LANCZOS)")
    print(
        f"[vframe] 阈值     : flicker dluma>{report['thresholds']['flicker']}  "
        f"freeze dluma<{report['thresholds']['freeze']} 连续>={report['thresholds']['freeze_run']} 帧"
    )
    print("")

    header = f"{'idx':>5} {'luma':>8} {'dluma':>8} {'sat':>8} {'hue(deg)':>10}  {'flag':<16}"
    print(header)
    print("-" * len(header))
    flicker_set = set(report["flicker_frames"])
    freeze_marks: dict[int, str] = {}
    for a, b in report["freeze_runs"]:
        for idx in range(a, b + 1):
            freeze_marks[idx] = f"freeze[{a}-{b}]"
    luma_series = report["luma_series"]
    dluma_series = report["dluma_series"]
    sat_series = report["sat_series"]
    hue_series = report["hue_series"]
    for i in range(len(files)):
        flags = []
        if (i + 1) in flicker_set:
            flags.append("FLICKER")
        if (i + 1) in freeze_marks:
            flags.append(freeze_marks[i + 1])
        name = os.path.basename(files[i])
        print(
            f"{i + 1:>5} {luma_series[i]:>8.4f} {dluma_series[i]:>8.4f} "
            f"{sat_series[i]:>8.4f} {hue_series[i]:>10.4f}  {','.join(flags) if flags else '-':<16} {name}"
        )

    print("")
    print(f"luma_drift : {report['luma_drift']:+.4f}   （末帧 - 首帧，负=整体变暗）")
    print(f"luma_trend : {report['luma_trend']:+.4f}/帧 （最小二乘斜率）")
    print(f"hue_std    : {report['hue_std']:.4f} 度 （色相圆标准差）")
    print(f"hue_jump   : {report['hue_jump_max']:.4f} 度 （相邻帧色相最大跳变）")
    print(f"flicker    : {len(report['flicker_frames'])} 帧 {report['flicker_frames']}")
    print(f"freeze     : {len(report['freeze_runs'])} 段 {report['freeze_runs']}")
    if report["worst_frames"]:
        worst = ", ".join(f"#{f}({v:.4f})" for f, v in report["worst_frames"])
        print(f"worst      : {worst}")
    print("")
    print(f"结论: {report['verdict'].upper()}  —— " + "；".join(report["notes"]))


# ---------------------------------------------------------------------------
# extract / strip
# ---------------------------------------------------------------------------
def extract(
    video: str,
    out_dir: str,
    fps: float = 2.0,
    scale: int = 0,
    start: float = 0.0,
    dur: float = 0.0,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """用 ffmpeg 抽帧到 out_dir/%05d.png，返回 {"frames": N, "dir": ...}。"""
    if not os.path.isfile(video):
        raise SystemExit(f"[vframe] 找不到视频：{video}")
    if fps <= 0:
        raise SystemExit("[vframe] --fps 必须 > 0")
    os.makedirs(out_dir, exist_ok=True)

    src_w = src_h = None
    if scale > 0:
        src_w, src_h = _probe_size(video, timeout=timeout)
        if not src_w:
            print("[vframe] 警告: ffprobe 未取到分辨率，--scale 退化为不缩放", file=sys.stderr)

    args: list[str] = ["-y"]
    if start > 0:
        args += ["-ss", f"{start:.3f}"]
    args += ["-i", video]
    if dur > 0:
        args += ["-t", f"{dur:.3f}"]
    filters = []
    scale_expr = _scale_filter(scale, src_w, src_h)
    if scale_expr:
        filters.append(scale_expr)
    filters.append(f"fps={fps:g}")
    args += ["-vf", ",".join(filters), "-an", "-sn", "-fps_mode", "passthrough", "-start_number", "1"]
    args += [os.path.join(out_dir, "%05d.png")]

    _run_ffmpeg(args, timeout=timeout)
    pngs = _find_pngs(out_dir)
    return {"frames": len(pngs), "dir": os.path.abspath(out_dir).replace("\\", "/")}


def strip(
    video: str,
    times: Sequence[float],
    out_dir: str,
    scale: int = 0,
    timeout: int = DEFAULT_TIMEOUT,
) -> list[str]:
    """按给定秒数各抽一帧，文件名 t1.200.png 这种。返回实际写出的文件列表。"""
    if not os.path.isfile(video):
        raise SystemExit(f"[vframe] 找不到视频：{video}")
    os.makedirs(out_dir, exist_ok=True)

    # 用「输入后置 -ss」= 精确 seek：先解码再定位，取到的就是给定秒数对应的那一帧。
    # （输入前置 -ss 是快速 seek，会跳到最近关键帧，秒数对不上，所以这里不用。）
    # --scale 需要源尺寸，先探一次复用。
    src_size = _probe_size(video, timeout=timeout) if scale > 0 else (None, None)
    duration = _probe_duration(video, timeout=timeout)

    written: list[str] = []
    for t in times:
        sec = max(0.0, float(t))
        target = os.path.join(out_dir, f"t{sec:.3f}.png")
        # 秒数正好落在片尾（或越界）时精确 seek 会抽不到帧：容器时长 6.000s 并不代表
        # 6.000s 处还有帧（末帧通常落在 5.5s 那种位置）。所以准备一串退让时间，
        # 由近到远依次重试，第一个抽出文件的就算数。
        attempts = [sec]
        if duration and sec >= duration - 1e-9:
            attempts += [duration - 0.05, duration - 0.5, duration - 1.0, 0.0]
        elif duration is None:
            attempts += [max(0.0, sec - 0.05), max(0.0, sec - 0.5), 0.0]
        attempts = [max(0.0, a) for a in attempts]

        note = ""
        for attempt in attempts:
            if os.path.exists(target):
                os.remove(target)          # 别把上一轮/上次运行留下的旧图当成成功
            args = ["-y", "-i", video, "-ss", f"{attempt:.3f}", "-frames:v", "1"]
            scale_expr = _scale_filter(scale, src_size[0], src_size[1])
            if scale_expr:
                args += ["-vf", scale_expr]
            args += ["-an", "-sn", "-fps_mode", "passthrough", target]
            _run_ffmpeg(args, timeout=timeout)
            if os.path.isfile(target) and os.path.getsize(target) > 0:
                if abs(attempt - sec) > 1e-9:
                    shown = f"{duration:.3f}s" if duration else "片尾"
                    note = f"（{sec:.3f}s 超出可用范围，片长 {shown}，实际取 {attempt:.3f}s）"
                break
        if os.path.isfile(target) and os.path.getsize(target) > 0:
            written.append(target)
            if note:
                print(f"[vframe] 提示: {os.path.basename(target)} {note}", file=sys.stderr)
        else:
            print(f"[vframe] 警告: {sec:.3f}s 未抽到帧（已退让到 {attempts[-1]:.3f}s 仍无帧）", file=sys.stderr)
    return written


# ---------------------------------------------------------------------------
# sheet
# ---------------------------------------------------------------------------
def sheet(
    target: str,
    out_path: str,
    cols: int = SHEET_COLS_DEFAULT,
    cell: int = SHEET_CELL_DEFAULT,
    label: bool = False,
    max_side: int = ANALYZE_MAX_SIDE,
) -> dict:
    """把帧拼成网格联络表（JPG），格间距 4px，背景 #FBF5E9，可选左上角帧号。"""
    files = _collect_frames(target)
    if cols <= 0:
        raise SystemExit("[vframe] --cols 必须 > 0")
    if cell <= 0:
        raise SystemExit("[vframe] --cell 必须 > 0")

    thumbs: list[Image.Image] = []
    for path in files:
        with Image.open(path) as img:
            # convert()/resize() 都返回新对象，出 with 之后文件句柄关掉也不影响这些副本
            frame = img.convert("RGB")
            width, height = frame.size
            long_side = max(width, height)
            if long_side > max_side:
                factor = max_side / float(long_side)
                frame = frame.resize(
                    (max(1, int(round(width * factor))), max(1, int(round(height * factor)))),
                    Image.LANCZOS,
                )
        thumb = frame.copy()
        thumb.thumbnail((cell, cell), Image.LANCZOS)
        thumbs.append(thumb)

    rows = (len(thumbs) + cols - 1) // cols
    canvas_w = cols * cell + (cols + 1) * SHEET_GAP
    canvas_h = rows * cell + (rows + 1) * SHEET_GAP
    canvas = Image.new("RGB", (canvas_w, canvas_h), SHEET_BG)
    draw = ImageDraw.Draw(canvas)

    for idx, thumb in enumerate(thumbs):
        row, col = divmod(idx, cols)
        slot_x = SHEET_GAP + col * (cell + SHEET_GAP)
        slot_y = SHEET_GAP + row * (cell + SHEET_GAP)
        off_x = slot_x + (cell - thumb.width) // 2
        off_y = slot_y + (cell - thumb.height) // 2
        canvas.paste(thumb, (off_x, off_y))
        if label:
            # PIL 默认位图字体，无需外部字体文件；底下垫一块背景色小方块保证可读
            text = str(idx + 1)
            bbox = draw.textbbox((0, 0), text)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            pad = 2
            draw.rectangle(
                [off_x, off_y, off_x + tw + pad * 2, off_y + th + pad * 2],
                fill=SHEET_BG,
            )
            draw.text((off_x + pad, off_y + pad - bbox[1]), text, fill=(20, 20, 20))

    parent = os.path.dirname(os.path.abspath(out_path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    ext = os.path.splitext(out_path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        canvas.save(out_path, format="JPEG", quality=92, subsampling=0)
    else:
        canvas.save(out_path)
    return {
        "sheet": os.path.abspath(out_path).replace("\\", "/"),
        "frames": len(thumbs),
        "cols": int(cols),
        "rows": int(rows),
        "cell": int(cell),
        "size": [int(canvas_w), int(canvas_h)],
        "label": bool(label),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _parse_times(text: str) -> list[float]:
    times: list[float] = []
    for chunk in re.split(r"[,;\s]+", text.strip()):
        if not chunk:
            continue
        try:
            times.append(float(chunk))
        except ValueError:
            raise SystemExit(f"[vframe] --times 里有无法解析的秒数：{chunk!r}")
    if not times:
        raise SystemExit("[vframe] --times 为空，例：--times 1.2,3.4,5.0")
    return times


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vframe.py",
        description="豆包视觉计算内核 · 视频帧质检（抽帧 / 闪烁卡帧分析 / 联络表 / 定点抽帧）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  vframe.py extract in.mp4 -o frames --fps 2 --scale 640\n"
            "  vframe.py analyze frames --json --flicker 0.06 --freeze 0.004 --freeze-run 3\n"
            "  vframe.py analyze \"frames/*.png\" --json\n"
            "  vframe.py sheet frames -o sheet.jpg --cols 6 --cell 320 --label\n"
            "  vframe.py strip in.mp4 --times 1.2,3.4,5.0 -o picks --scale 720\n"
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_extract = sub.add_parser("extract", help="用 ffmpeg 抽帧为 %%05d.png")
    p_extract.add_argument("video", help="输入视频路径（可含中文）")
    p_extract.add_argument("-o", "--out", required=True, help="输出帧目录")
    p_extract.add_argument("--fps", type=float, default=2.0, help="抽帧帧率，默认 2")
    p_extract.add_argument("--scale", type=int, default=0, help="按长边缩放到该像素；0=不缩放（默认）")
    p_extract.add_argument("--start", type=float, default=0.0, help="起始秒，默认 0")
    p_extract.add_argument("--dur", type=float, default=0.0, help="限时长秒，>0 时用 -t；默认 0=全长")
    p_extract.add_argument("--json", action="store_true", help='输出 {"frames":N,"dir":"..."}')

    p_analyze = sub.add_parser("analyze", help="分析帧序列，量化闪烁 / 卡帧 / 偏色 / 变暗")
    p_analyze.add_argument("target", help="帧目录或 glob，如 frames 或 \"frames/*.png\"")
    p_analyze.add_argument("--json", action="store_true", help="输出 JSON 报告")
    p_analyze.add_argument("--flicker", type=float, default=0.06, help="闪烁阈值 dluma >，默认 0.06")
    p_analyze.add_argument("--freeze", type=float, default=0.004, help="卡帧阈值 dluma <，默认 0.004")
    p_analyze.add_argument("--freeze-run", type=int, default=3, help="连续多少帧画面不动算卡帧区间，默认 3（须 >=2）")
    p_analyze.add_argument("--max-side", type=int, default=ANALYZE_MAX_SIDE, help="逐帧缩放长边上限，默认 512")

    p_sheet = sub.add_parser("sheet", help="把帧拼成网格联络表")
    p_sheet.add_argument("frames_dir", help="帧目录（或 glob）")
    p_sheet.add_argument("-o", "--out", required=True, help="输出图片，如 sheet.jpg")
    p_sheet.add_argument("--cols", type=int, default=SHEET_COLS_DEFAULT, help="列数，默认 6")
    p_sheet.add_argument("--cell", type=int, default=SHEET_CELL_DEFAULT, help="单元格边长，默认 320")
    p_sheet.add_argument("--label", action="store_true", help="每格左上角写帧号")
    p_sheet.add_argument("--json", action="store_true", help="输出 JSON 元信息")

    p_strip = sub.add_parser("strip", help="按给定秒数各抽一帧")
    p_strip.add_argument("video", help="输入视频路径")
    p_strip.add_argument("--times", required=True, help="逗号分隔秒数，如 1.2,3.4,5.0")
    p_strip.add_argument("-o", "--out", required=True, help="输出目录")
    p_strip.add_argument("--scale", type=int, default=0, help="按长边缩放；0=不缩放")
    p_strip.add_argument("--json", action="store_true", help="输出 JSON")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    _setup_io()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "extract":
        info = extract(
            args.video, args.out,
            fps=args.fps, scale=args.scale, start=args.start, dur=args.dur,
        )
        if args.json:
            print(_dump_json(info))
        else:
            print(f"抽出帧数: {info['frames']}")
            print(f"输出目录: {info['dir']}")
        return 0

    if args.cmd == "analyze":
        report = analyze(
            args.target,
            flicker_thr=args.flicker,
            freeze_thr=args.freeze,
            freeze_run=args.freeze_run,
            max_side=args.max_side,
        )
        if args.json:
            print(_dump_json(report))
        else:
            _print_analyze_text(report, _collect_frames(args.target))
        return 0

    if args.cmd == "sheet":
        info = sheet(args.frames_dir, args.out, cols=args.cols, cell=args.cell, label=args.label)
        if args.json:
            print(_dump_json(info))
        else:
            print(f"联络表: {info['sheet']}")
            print(f"帧数 {info['frames']}  网格 {info['cols']}x{info['rows']}  单元格 {info['cell']}px  画布 {info['size'][0]}x{info['size'][1]}")
        return 0

    if args.cmd == "strip":
        times = _parse_times(args.times)
        written = strip(args.video, times, args.out, scale=args.scale)
        if args.json:
            print(_dump_json({
                "times": [_fmt(t) for t in times],
                "dir": os.path.abspath(args.out).replace("\\", "/"),
                "frames": len(written),
                "files": [os.path.basename(p) for p in written],
            }))
        else:
            print(f"定点抽帧: {len(written)}/{len(times)} 帧 -> {os.path.abspath(args.out)}")
            for path in written:
                print(f"  {os.path.basename(path)}")
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
