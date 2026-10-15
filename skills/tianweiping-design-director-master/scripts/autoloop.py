#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""autoloop.py —— 豆包视觉计算内核 · 闭环编排器

把「生成」和「质检修复」焊成一条流水线，替代"出图 → 肉眼看看 → 改词 → 再出"的循环。

  一个镜头：生成 N 张候选 → vqc 排序选赢家 → vfix 只修该修的那项 → 复评（没变好就回滚）
  整批镜头：vqc series 查一致性 → 不够就 vfix unify 拉齐 → 出 HTML 报告

它**不自己生成图**，而是调用你已有的生成通道（本机是 local-stack\\produce.py），
模板变量：{prompt} {seed} {out} {index}

子命令
  run   --shots shots.json --out work/ --gen-cmd "<命令模板>" [--cand 4] [--profile product]
  demo  --out work/ [--mock-src 图.png]          不用 GPU，用合成缺陷图自检整条闭环
  selftest                                       校验 vqc 的指标能抓住已知缺陷

示例
  # 真跑（本机 ComfyUI 生产栈）
  autoloop.py run --shots shots.json --out work\\ep01 --cand 4 --profile illustration ^
    --gen-cmd "\"F:\\ComfyUI_windows_portable\\python_embeded\\python.exe\" \"<ws>\\local-stack\\produce.py\" image --prompt \"{prompt}\" --seed {seed} --out \"{out}\""

  # 先自检通路，不烧 GPU
  autoloop.py demo --out work\\demo --mock-src ref.png

退出码  0=全部达标   3=有镜头未达标   2=参数或环境问题
"""
import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import vqc
import vfix
import shot as shotmod

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")


def log(msg):
    print(f"[autoloop] {msg}", flush=True)


def list_images(d):
    if not os.path.isdir(d):
        return []
    return sorted(os.path.join(d, f) for f in os.listdir(d)
                  if f.lower().endswith(IMG_EXT) and os.path.isfile(os.path.join(d, f)))


# ============================================================ 生成通道

def gen_one(template, prompt, seed, out_path, index, cwd=None, timeout=1800, dry=False):
    """执行一条生成命令。模板变量 {prompt} {seed} {out} {index}"""
    cmd = (template.replace("{prompt}", prompt)
                   .replace("{seed}", str(seed))
                   .replace("{out}", out_path)
                   .replace("{index}", str(index)))
    if dry:
        log(f"  [dry-run] {cmd}")
        return True, "dry-run"
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8:replace")
    env.setdefault("PYTHONUTF8", "1")
    try:
        r = subprocess.run(cmd, shell=True, cwd=cwd, env=env, timeout=timeout,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        tail = (r.stdout or b"").decode("utf-8", "replace")[-600:]
        if r.returncode != 0:
            return False, f"退出码 {r.returncode}: {tail}"
        if not os.path.exists(out_path):
            # 生成器有时会自己改文件名/扩展名，兜底找同目录最新图
            cand = [p for p in list_images(os.path.dirname(out_path))
                    if os.path.splitext(os.path.basename(p))[0].startswith(
                        os.path.splitext(os.path.basename(out_path))[0])]
            if cand:
                shutil.move(cand[0], out_path)
                return True, "改名兜底"
            return False, f"命令成功但没有产物：{out_path}\n{tail}"
        return True, ""
    except subprocess.TimeoutExpired:
        return False, f"超时（{timeout}s）"


# ============================================================ 单镜头闭环

def run_shot(sp, outdir, cand, gen_cmd, profile, recipe, dry, max_rounds=2,
             min_gain=0.6, mock_pool=None, seed0=1000):
    """返回一个镜头的完整结果"""
    os.makedirs(outdir, exist_ok=True)
    prompt = sp.get("_prompt") or shotmod.compile_prompt(sp)["zh"]
    prompt_one = " ".join(prompt.split("\n"))[:600]
    res = {"name": sp.get("name") or os.path.basename(outdir), "prompt": prompt_one,
           "candidates": [], "winner": None, "fixed": None, "kept": None,
           "before": None, "after": None, "note": ""}

    # 1) 出候选
    for i in range(cand):
        if mock_pool:
            label, src = mock_pool[i % len(mock_pool)]
            p = os.path.join(outdir, f"cand{i + 1:02d}_{label}.png")
        else:
            src, label = None, ""
            p = os.path.join(outdir, f"cand{i + 1:02d}.png")
        if os.path.exists(p):
            res["candidates"].append(p)
            continue
        if mock_pool:
            if not dry:
                os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
                shutil.copy2(src, p)
            res["candidates"].append(p)
            continue
        ok, msg = gen_one(gen_cmd, prompt_one, seed0 + i * 7919, p, i + 1, dry=dry)
        if ok:
            res["candidates"].append(p)
        else:
            log(f"  候选 {i + 1} 生成失败：{msg}")
    if dry:
        # 演练模式：没有真实产物，不要往下走评分（会去读不存在的文件）
        res["candidates"] = []
        res["note"] = "dry-run：只列出将要执行的生成命令与闭环流程，未产出文件"
        return res
    res["candidates"] = [p for p in res["candidates"] if os.path.exists(p)]
    if not res["candidates"]:
        res["note"] = "没有产出任何候选"
        return res

    # 2) 排序
    scored = []
    for p in res["candidates"]:
        m = vqc.metrics(p)
        s = vqc.score(m, profile)
        scored.append((p, m, s))
    scored.sort(key=lambda t: (t[2]["hard_fail"], -t[2]["total"]))
    win_p, win_m, win_s = scored[0]
    res["winner"] = win_p
    res["ranking"] = [{"file": os.path.basename(p), "total": s["total"], "grade": s["grade"],
                       "hard_fail": s["hard_fail"]} for p, _, s in scored]

    # 3) 修复 + 复评（只有变好才保留）
    steps = vfix.parse_steps(recipe) if recipe else []
    cur_p, cur_s = win_p, win_s
    if steps and not dry:
        for rnd in range(max_rounds):
            if cur_s["hard_fail"] == 0 and not cur_s["issues"]:
                break
            out = os.path.join(outdir, f"fixed{rnd + 1}.png")
            try:
                im, fmt = vfix.open_rgb(cur_p)
                vfix.save_rgb(vfix.run_steps(im, steps), out, fmt)
            except Exception as e:
                res["note"] += f" 修复异常({e})；"
                break
            m2 = vqc.metrics(out)
            s2 = vqc.score(m2, profile, baseline=vqc.metrics(win_p))
            if s2["total"] > cur_s["total"] + min_gain:
                res["fixed"] = out
                cur_p, cur_s = out, s2
            else:
                try:
                    os.remove(out)
                except OSError:
                    pass
                res["note"] += f" 第{rnd + 1}轮修复没变好（{cur_s['total']}→{s2['total']}），已回滚；"
                break
    res["kept"] = cur_p
    res["before"] = {"file": os.path.basename(win_p), "total": win_s["total"],
                     "grade": win_s["grade"], "hard_fail": win_s["hard_fail"]}
    res["after"] = {"file": os.path.basename(cur_p), "total": cur_s["total"],
                    "grade": cur_s["grade"], "hard_fail": cur_s["hard_fail"],
                    "issues": [i["key"] for i in cur_s["issues"]],
                    "fix_list": [i["advice"] for i in cur_s["issues"]]}
    return res


# ============================================================ 整批

def load_shots(path):
    # utf-8-sig：PowerShell 的 Set-Content -Encoding UTF8 会带 BOM，用 utf-8 读会炸
    with open(path, encoding="utf-8-sig") as fh:
        doc = json.load(fh)
    base = doc.get("base") or {}
    shots = doc.get("shots") or []
    out = []
    for i, sh in enumerate(shots, 1):
        sp = dict(base)
        sp.update(sh)
        sp.setdefault("profile", doc.get("profile", "illustration"))
        name = sp.get("name") or f"shot{i:02d}"
        sp["name"] = name
        sp["_prompt"] = shotmod.compile_prompt(sp)["zh"]
        out.append(sp)
    return doc.get("profile", "illustration"), out


def cmd_run(a):
    profile_default, shots = load_shots(a.shots)
    profile = a.profile or profile_default
    os.makedirs(a.out, exist_ok=True)
    log(f"镜头 {len(shots)} 个 · 每个 {a.cand} 张候选 · profile={profile}")
    log(f"输出 {a.out}")
    results = []
    t0 = time.time()
    for i, sp in enumerate(shots, 1):
        log(f"[{i}/{len(shots)}] {sp['name']}")
        r = run_shot(sp, os.path.join(a.out, f"{i:02d}_{sp['name']}"), a.cand, a.gen_cmd,
                     profile, a.recipe, a.dry, max_rounds=a.rounds)
        results.append(r)
        if r.get("after"):
            log(f"   {r['before']['total']} → {r['after']['total']}  "
                f"保留 {os.path.basename(r['kept']) if r['kept'] else '-'}")
        else:
            log(f"   跳过：{r.get('note','')}")

    # 成套统一
    kept = [r["kept"] for r in results if r.get("kept") and not a.dry]
    series = None
    if len(kept) >= 2:
        series = series_report(kept, profile)
        log(f"成套一致性 {series['consistency']}（{len(kept)} 张）")
        if series["consistency"] < a.min_consistency and not a.no_unify:
            best = max(results, key=lambda r: (r.get("after") or {}).get("total", 0))
            ref = best["kept"]
            uni = os.path.join(a.out, "_unified")
            os.makedirs(uni, exist_ok=True)
            for r in results:
                if not r.get("kept"):
                    continue
                im, fmt = vfix.open_rgb(r["kept"])
                dst = os.path.join(uni, os.path.basename(os.path.dirname(r["kept"])) + ".png")
                vfix.save_rgb(vfix.op_unify(im, vfix.open_rgb(ref)[0], a.unify_strength),
                              dst, fmt)
            after = series_report(list_images(uni), profile)
            log(f"  unify（参考 {os.path.basename(ref)}）后一致性 {after['consistency']}")
            series["after_unify"] = after
            series["unified_dir"] = uni
            series["ref"] = ref

    report = {"profile": profile, "out": os.path.abspath(a.out),
              "elapsed_s": round(time.time() - t0, 1),
              "shots": results, "series": series}
    with open(os.path.join(a.out, "autoloop.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    if a.report:
        write_report(report, a.report)
        log(f"报告 {a.report}")
    if a.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))

    bad = [r for r in results if not r.get("after") or r["after"]["hard_fail"] > 0]
    log(f"完成 {len(results)} 个镜头，用时 {report['elapsed_s']}s，"
        f"硬门槛未过 {len(bad)} 个")
    return 0 if not bad else 3


def series_report(files, profile):
    ms = [vqc.metrics(p) for p in files]
    lums = np.array([m["expo"]["mean_luma"] for m in ms], np.float32)
    sats = np.array([m["color"]["mean_sat"] for m in ms], np.float32)
    hues = np.array([m["color"]["hue_mean"] for m in ms], np.float32)
    ten = np.array([m["sharp"]["log_ten"] for m in ms], np.float32)
    ang = np.deg2rad(hues)
    R = min(1.0, max(1e-6, float(np.hypot(np.cos(ang).mean(), np.sin(ang).mean()))))
    import math
    hue_conc = math.degrees(math.sqrt(-2 * math.log(R)))
    cons = (vqc.saturate(1 - float(lums.std()) / 0.14, 0, 1) * 0.35 +
            vqc.saturate(1 - float(sats.std()) / 0.13, 0, 1) * 0.25 +
            vqc.saturate(1 - hue_conc / 55.0, 0, 1) * 0.25 +
            vqc.saturate(1 - float(ten.std()) / 0.55, 0, 1) * 0.15)
    return {"count": len(ms), "consistency": round(cons * 100, 1),
            "luma_std": round(float(lums.std()), 4), "sat_std": round(float(sats.std()), 4),
            "hue_conc": round(hue_conc, 2),
            "scores": [vqc.score(m, profile)["total"] for m in ms]}


def write_report(rep, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    rows = []
    for r in rep["shots"]:
        b = r.get("before") or {}
        a_ = r.get("after") or {}
        thumb = ""
        if r.get("kept") and os.path.exists(r["kept"]):
            try:
                t = Image.open(r["kept"]).convert("RGB")
                t.thumbnail((260, 260))
                td = os.path.join(os.path.dirname(os.path.abspath(path)), "thumbs")
                os.makedirs(td, exist_ok=True)
                tn = os.path.join(td, re.sub(r"[^\w\-.]", "_", os.path.basename(r["kept"])) + ".jpg")
                t.save(tn, quality=82)
                thumb = os.path.relpath(tn, os.path.dirname(os.path.abspath(path))).replace("\\", "/")
            except Exception:
                pass
        iss = "".join(f"<li>{x}</li>" for x in (a_.get("fix_list") or []))
        rows.append(f"""<div class=c><img src="{thumb}"><div>
<div><b>{r['name']}</b> &nbsp; <span class=g>{b.get('total','-')} → <b>{a_.get('total','-')}</b></span>
{'(硬门槛未过)' if a_.get('hard_fail') else ''}</div>
<div style="color:#76695A;font-size:12px">{r.get('note','')}</div>
<ul>{iss}</ul>
<div style="color:#76695A;font-size:12px">{r.get('prompt','')[:150]}</div>
</div></div>""")
    s = rep.get("series")
    shtml = ""
    if s:
        shtml = (f"<h2>成套一致性 {s['consistency']} / 100</h2>"
                 f"<p>亮度离散 {s['luma_std']} · 饱和离散 {s['sat_std']} · "
                 f"色相集中 {s['hue_conc']}°</p>")
        if s.get("after_unify"):
            shtml += (f"<p>unify 后 <b>{s['after_unify']['consistency']}</b> / 100"
                      f"（参考 {os.path.basename(s['ref'])}）→ {s.get('unified_dir','')}</p>")
    html = f"""<!doctype html><meta charset=utf-8><title>autoloop 报告</title>
<style>body{{font:14px/1.7 'Microsoft YaHei',sans-serif;background:#FBF5E9;color:#40372E;margin:0;padding:26px}}
h1{{font-size:20px}}h2{{font-size:17px;margin-top:26px}}
.c{{display:flex;gap:16px;background:#fff;border-radius:10px;padding:14px;margin:10px 0;
box-shadow:0 4px 14px rgba(64,55,46,.10)}}img{{width:240px;height:auto;border-radius:6px}}
.g{{background:#E4744A;color:#fff;padding:2px 10px;border-radius:99px;font-weight:700}}
ul{{margin:6px 0 0 18px;padding:0;color:#C9483D;font-size:13px}}</style>
<h1>autoloop 报告 · profile={rep['profile']} · {len(rep['shots'])} 个镜头 · 用时 {rep['elapsed_s']}s</h1>
{shtml}{''.join(rows)}"""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)


# ============================================================ demo：不用 GPU 自检整条闭环

def make_defective(src, dst, kind, seed=3):
    im = Image.open(src).convert("RGB")
    a = np.asarray(im, np.float32)
    rng = np.random.default_rng(seed)
    if kind == "clean":
        out = a
    elif kind == "bright":
        out = np.clip(a * 1.22 + 26, 0, 255)
    elif kind == "washed":
        m = a.mean()
        out = np.clip((a - m) * 0.42 + m + 12, 0, 255)
    elif kind == "noisy":
        out = np.clip(a + rng.normal(0, 16, a.shape), 0, 255)
    elif kind == "blur":
        out = np.asarray(im.filter(__import__("PIL.ImageFilter", fromlist=["x"]).GaussianBlur(2.4)),
                         np.float32)
    elif kind == "satur":
        hsv = np.asarray(im.convert("HSV"), np.float32)
        hsv[..., 1] = np.clip(hsv[..., 1] * 1.9, 0, 255)
        out = np.asarray(Image.fromarray(hsv.astype(np.uint8), "HSV").convert("RGB"), np.float32)
    else:
        out = a
    Image.fromarray(out.astype(np.uint8), "RGB").save(dst)


def cmd_demo(a):
    """用合成缺陷图跑一遍闭环：候选里混入 1 张正常 + 3 张有缺陷的，
    正确行为是选出正常那张、且不把它修坏。"""
    os.makedirs(a.out, exist_ok=True)
    if a.mock_src and os.path.exists(a.mock_src):
        src = a.mock_src
    else:
        src = os.path.join(a.out, "_base.png")
        W, H = 900, 900
        im = Image.new("RGB", (W, H), (244, 231, 200))
        d = ImageDraw.Draw(im)
        d.ellipse([180, 240, 720, 700], fill=(228, 116, 74))
        d.ellipse([330, 330, 570, 560], fill=(46, 71, 86))
        d.rectangle([120, 720, 780, 780], fill=(126, 155, 118))
        try:
            f = ImageFont.truetype(os.path.join(os.environ.get("WINDIR", r"C:\Windows"),
                                                "Fonts", "msyh.ttc"), 60)
            d.text((450, 800), "自检图", font=f, fill=(64, 55, 46), anchor="mm")
        except Exception:
            pass
        im.save(src)
        log(f"没有 --mock-src，生成了一张自检底图 {src}")

    pool = os.path.join(a.out, "_pool")
    os.makedirs(pool, exist_ok=True)
    kinds = ["bright", "clean", "washed", "noisy"]
    for k in kinds:
        make_defective(src, os.path.join(pool, f"mock_{k}.png"), k)
    log(f"合成 {len(kinds)} 张模拟候选：{', '.join(kinds)}")

    shots = {"profile": a.profile, "base": {"shot": "中景", "angle": "平视", "lens": "50",
                                            "aperture": "4", "ratio": "1:1",
                                            "texture": "哑光", "motion": "固定"},
             "shots": [{"name": "demo", "subject": "闭环自检", "action": "选出正常那张"}]}
    sp_path = os.path.join(a.out, "shots_demo.json")
    with open(sp_path, "w", encoding="utf-8") as fh:
        json.dump(shots, fh, ensure_ascii=False, indent=1)

    args = argparse.Namespace(shots=sp_path, out=os.path.join(a.out, "run"), cand=len(kinds),
                              gen_cmd="", profile=a.profile, recipe=a.recipe, dry=False,
                              rounds=1, json=False, report=os.path.join(a.out, "demo_report.html"),
                              min_consistency=70.0, no_unify=True, unify_strength=1.0)
    # demo 直接指定候选池
    profile_default, shot_list = load_shots(sp_path)
    os.makedirs(args.out, exist_ok=True)
    r = run_shot(shot_list[0], os.path.join(args.out, "01_demo"), len(kinds), "",
                 a.profile, a.recipe, False,
                 mock_pool=[(k, os.path.join(pool, f"mock_{k}.png")) for k in kinds])
    ok = bool(r.get("winner")) and "clean" in os.path.basename(r["winner"])
    print()
    log("候选排序：" + " > ".join(f"{x['file']}({x['total']})" for x in r.get("ranking", [])))
    log(f"选出 {os.path.basename(r['winner'] or '-')}   期望 mock_clean.png   "
        f"{'✔ 通过' if ok else '✘ 未通过'}")
    if r.get("fixed"):
        log(f"修复 {r['before']['total']} → {r['after']['total']}（{os.path.basename(r['fixed'])}）")
    else:
        log(f"没有需要修或修不好：{r.get('note') or '选择器认为已经达标'}")
    summary = {"demo_pass": ok, "winner": r.get("winner"), "ranking": r.get("ranking"),
               "before": r.get("before"), "after": r.get("after")}
    with open(os.path.join(a.out, "demo_result.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=1)
    return 0 if ok else 3


# ============================================================ vqc 指标自检

def cmd_selftest(a):
    """造已知缺陷，验证 vqc 的对应指标真的会亮。
    这是回归测试：改过阈值或公式后跑一遍，确认没有把该抓的漏掉。
    底图刻意做成「深主体 + 中间调 + 浅底 + 细纹理」，让 ok 样本在各项软带里都落在良好区间。"""
    tmp = a.out or os.path.join(os.environ.get("TEMP", "."), "vqc_selftest")
    os.makedirs(tmp, exist_ok=True)
    W, H = 1400, 1000
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.zeros((H, W, 3), np.float32)
    base[..., 0], base[..., 1], base[..., 2] = 236.0, 230.0, 214.0          # 浅底
    ellipse = ((xx - 700) ** 2 / 360.0 ** 2 + (yy - 500) ** 2 / 300.0 ** 2) < 1.0
    base[ellipse] = (46, 71, 86)                                            # 深主体
    rect = (xx > 150) & (xx < 520) & (yy > 620) & (yy < 880)
    base[rect] = (228, 116, 74)                                             # 中间调色块
    base += (np.sin(xx / 6.5) * np.cos(yy / 8.5))[..., None] * 7.0          # 细纹理
    base = np.clip(base, 0, 255)
    rng = np.random.default_rng(11)
    cases = {
        "ok": base,
        "clip_high": np.clip(base + 55.0 * (base / 255.0), 0, 255),         # 只抬亮部
        "clip_low": np.where(base < 120, 0.0, base),                        # 压死暗部
        "flat": np.clip((base - base.mean()) * 0.40 + base.mean(), 0, 255),
        "gray": np.clip(base * 0.22 + 178, 0, 255),
        "satur": np.clip(base.mean(-1, keepdims=True)
                         + (base - base.mean(-1, keepdims=True)) * 3.4, 0, 255),
        "noisy": np.clip(base + rng.normal(0, 22, base.shape), 0, 255),
        "blur": np.asarray(Image.fromarray(base.astype(np.uint8), "RGB")
                           .filter(__import__("PIL.ImageFilter", fromlist=["x"]).GaussianBlur(3.0)),
                           np.float32),
    }
    # 每个样本期望「至少亮起」的指标；None 表示不该有任何硬门槛失败
    expect = {"ok": None, "clip_high": "clip_high", "clip_low": "clip_low",
              "flat": "range95", "gray": "range95", "satur": "over_sat",
              "noisy": "noise_sigma", "blur": None}
    files = {}
    for k, arr in cases.items():
        p = os.path.join(tmp, f"st_{k}.png")
        Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").save(p)
        files[k] = p

    rows, passed, failed = [], 0, 0
    for k, p in files.items():
        m = vqc.metrics(p)
        s = vqc.score(m, "illustration")
        got = [i["key"] for i in s["issues"] if i.get("hard")] + \
              [i["key"] for i in s["issues"] if not i.get("hard")]
        exp = expect[k]
        if exp is None:
            if k == "ok":
                ok = s["hard_fail"] == 0
                detail = "无硬门槛失败" if ok else f"不该失败却失败：{got}"
            else:   # blur：清晰度没有基准就不该下结论，只要不误判成硬失败即可
                ok = s["hard_fail"] == 0 and s["total"] >= 60
                detail = f"无硬失败且总分 {s['total']} ≥ 60"
        else:
            ok = exp in got
            detail = f"期望 {exp} 亮" + (" ✔" if ok else f" ✘（实际亮起 {got}）")
        passed += 1 if ok else 0
        failed += 0 if ok else 1
        rows.append((k, s["total"], s["grade"], s["hard_fail"], detail, ok))

    print(f"\n{'样本':<12}{'总分':>7}{'级':>4}{'硬失败':>7}   判定")
    print("-" * 78)
    for k, t, g, hf, detail, ok in rows:
        print(f"{k:<12}{t:>7.1f}{g:>4}{hf:>7}   {'✔' if ok else '✘'} {detail}")
    print("-" * 78)
    print(f"自检 {passed}/{passed + failed} 通过   （样本目录 {tmp}）")
    if failed:
        print("！有指标没抓住已知缺陷，去检查 vqc.py 的阈值与评分函数。")
    return 0 if failed == 0 else 3


# ============================================================

def main():
    ap = argparse.ArgumentParser(description="豆包视觉计算内核 · 闭环编排器")
    sub = ap.add_subparsers(dest="cmd", required=True)
    prof = ["default", "poster", "product", "illustration", "video_frame"]
    rec_default = "autolevel:black=1.0,white=99.0;chroma:size=5,strength=0.7;unsharp:radius=1.4,amount=55,threshold=3"

    p = sub.add_parser("run", help="跑整批镜头的闭环")
    p.add_argument("--shots", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--gen-cmd", default="")
    p.add_argument("--cand", type=int, default=4)
    p.add_argument("--profile", choices=prof)
    p.add_argument("--recipe", default=rec_default)
    p.add_argument("--rounds", type=int, default=2)
    p.add_argument("--min-consistency", type=float, default=70.0)
    p.add_argument("--no-unify", action="store_true")
    p.add_argument("--unify-strength", type=float, default=1.0)
    p.add_argument("--report", default="")
    p.add_argument("--dry-run", dest="dry", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("demo", help="不用 GPU 自检整条闭环")
    p.add_argument("--out", required=True)
    p.add_argument("--mock-src")
    p.add_argument("--profile", default="illustration", choices=prof)
    p.add_argument("--recipe", default=rec_default)
    p.set_defaults(fn=cmd_demo)

    p = sub.add_parser("selftest", help="校验 vqc 指标能抓住已知缺陷")
    p.add_argument("--out")
    p.set_defaults(fn=cmd_selftest)

    a = ap.parse_args()
    if a.cmd == "run" and not a.gen_cmd and not a.dry:
        raise SystemExit("run 需要 --gen-cmd（生成命令模板），或用 --dry-run 只演练流程")
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
