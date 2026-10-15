> 来源：原 doubao-visual-core（视觉计算内核）原文

# 豆包视觉计算内核

> **核心主张**：不要靠"再抽一张"解决问题。**先量 → 再修 → 修完复量。**
> 抽卡解决的是运气，量化解决的是确定性。

---

## 0. 为什么要"底层运算"

常见循环：写提示词 → 出图 → 觉得不对 → 改词 → 再出 → 还是不对 → 再改。

问题在两头：**「觉得不对」是模糊判断，「改词」是盲改。**

内核把两头都变成数字：

| 模糊说法 | 量化说法 | 对应的确定动作 |
|---|---|---|
| "有点糊" | 相对参考图 −4.2 dB | `vfix.py unsharp --amount 90` |
| "发灰" | range95 = 0.31（理想 0.62） | `vfix.py autolevel --black 1.5` |
| "颜色花" | 色相跨度 59°（理想 ≤15°） | 提示词先定 3 色板，再生成 |
| "这套图不像一套" | 一致性 82/100 | `vfix.py unify --ref 最好那张` → 96 |
| "视频一闪一闪" | flicker 帧占比 7.4% | 锁定曝光/色温重出该镜 |

---

## 1. 五件工具（全本地，不联网、不调模型）

| 工具 | 一句话 | 主要命令 |
|---|---|---|
| **autoloop.py** | 编排：把生成和质检焊成一条闭环 | `run` `demo` `selftest` |
| **vqc.py** | 量化：这画面到底哪儿不对 | `score` `pick` `compare` `palette` `series` `textsafe` `report` |
| **vfix.py** | 修复：只修那一项，不重生成 | `autolevel` `unsharp` `chroma` `sat` `unify` `grain` `resize` `recipe` `batch` |
| **shot.py** | 编译：把规格变成可复现的提示词 | `build` `spec` `verify` `list` |
| **vframe.py** | 视频：抽帧 + 闪烁/卡帧检测 | `extract` `analyze` `sheet` `strip` |

运行环境：本机 Python（numpy + Pillow 即可），vframe 另需 ffmpeg。
脚本位置：本 skill 的 `scripts/` 目录。**全部用绝对路径调 Python 与 ffmpeg**，见第 7 节。
接本机 ComfyUI 生成栈：见 `references/comfyui.md`。

### 先跑一次自检（改过阈值之后必做）

```bash
python autoloop.py selftest      # 造 8 种已知缺陷，确认每项指标都抓得住
python autoloop.py demo --out work/demo    # 不用 GPU，跑通整条闭环
```

`selftest` 是回归测试：任何一次调阈值之后都该跑一遍。实测 8/8 通过。

---

## 2. 标准工作流（闭环五步）

```
① 编译规格   shot.py build --subject "..." --from-image 参考图.png
             ↓ 拿到结构化提示词 + 一致性锁
② 一次出 N 张  4~6 张，别一张张试
             ↓
③ 量化排序   vqc.py pick 候选/*.png --profile poster
             ↓ 直接给出"选它" + 它差在哪
④ 定向修复   vfix.py recipe 赢家.png -o fixed.png --steps "autolevel;chroma;unsharp"
             ↓
⑤ 复评确认   vqc.py score fixed.png --baseline 参考.png
             ↓ 没到位就回到 ④，别回到 ②
⑥ 成套校验   vqc.py series 成品/*.png  → 一致性 <70 就 vfix.py unify
```

**关键纪律：能用 ④ 修的，不要回 ②。** 回 ② 等于重新掷骰子，连已经对的部分都会一起变。

### 一条完整示例

```bash
# ③ 排序
python vqc.py pick out/*.png --profile product
#   ★ 选它   93.4 A  out/003.png
#   #2   91.2 A  out/001.png
#   → 用 003.png，接着按下面修：
#      ! mean_luma: 整体偏亮 → vfix.py autolevel

# ④ 修
python vfix.py recipe out/003.png -o fixed/003.png --steps "autolevel:black=1.2,white=98.5;chroma:size=5,strength=0.7;unsharp:radius=1.4,amount=60,threshold=3"

# ⑤ 复评（带基准，清晰度才算得准）
python vqc.py score fixed/003.png --profile product --baseline ref/product_ref.png
```

---

## 3. 指标怎么读 —— **先分清硬指标和提示指标**

这是本内核最容易用错的地方，先看这条：

> ⚠️ **绝对分数只在同一 profile、同一批内容之间横向比较才有意义。**
> 不要拿一张海报的 95 分和一张插图的 88 分比高低，那是两种东西。

### 3.1 硬门槛（绝对可判，不过就是错）

| 指标 | 含义 | 典型门槛 |
|---|---|---|
| `clip_high` | 高光溢出像素比 | poster ≤ 2.0%，video ≤ 2.8% |
| `clip_low` | 暗部死黑像素比 | ≤ 3.0% |
| `over_sat` | 饱和度 > 0.90 的像素比 | ≤ 4.5% |
| `noise_sigma` | Laplacian MAD 估噪 | ≤ 0.026 |
| `min_side` | 短边像素 | poster ≥ 1200 |
| `textsafe` | 文字对比度 / 底噪 | ≥ 4.5:1 且底噪 < 0.10 |

### 3.2 软指标（合理区间 + 理想点，越界只扣分）

`mean_luma` `range95` `mean_sat` `hue_spread` —— 打分是**梯度**的：
理想点 100 分，区间边缘 78 分，区间外继续衰减。所以"勉强合格"和"刚刚好"能拉开差距。

### 3.3 相对指标（**没有参考图就不要拿它下结论**）

| 指标 | 为什么不能用绝对值 |
|---|---|
| `sharp` | 清晰度和画面内容强相关：一张极简插图的梯度能量天然低于一张纹理特写。**必须 `--baseline`。** |
| `compose` | 三分法只是其中一种构图。居中的对称海报本来就不在三分点。所以它只做启发式提示，权重 0.7。 |
| `plastic_ratio` | 平坦区高频占比，和画风有关（水彩本来就没高频）。 |

---

## 4. 症状 → 处方速查

| 症状 | 量化特征 | 处方（先改提示词，再后处理） |
|---|---|---|
| 糊 | `sharp` 比参考低 > 3 dB | 提示词加"细节/纹理/微距"并调低降噪 → `vfix.py unsharp` |
| 发灰 | `range95` < 0.45 | `vfix.py autolevel --black 1.0 --white 99.0` |
| 过曝/死白 | `clip_high` > 门槛 | 删"强光/发光/过曝/逆光光斑" → `autolevel --white 96` |
| 死黑 | `clip_low` > 门槛 | 提示词加"暗部保留细节" → `autolevel --black 3` |
| 脏/糊在暗部 | `noise_sigma` 高 | `vfix.py chroma`（**只去色噪，别整体磨皮**） |
| 塑料感 | `plastic_ratio` 极低 | 提示词加"胶片颗粒/皮肤纹理/纸张质感" → `grain --amount 4` |
| 颜色花 | `hue_spread` > 90° | 先定 3 色板再生成；成套图用 `vfix.py unify` |
| 太艳 | `mean_sat` 高 + `over_sat` 超 | `vfix.py sat --gain 0.9 --vibrance 0.05` |
| 一套图不像一套 | `series` 一致性 < 70 | `vfix.py unify --ref 最好那张` |
| 文字看不清 | `textsafe` verdict ≠ ok | 加 0.75+ 不透明衬底，或换干净区块 |
| 视频闪 | `flicker` 帧占比 > 5% | 锁曝光/色温/种子重出该镜 |
| 视频卡 | `freeze_runs` 占比 > 20% | 检查运动幅度，提高运动强度描述 |

---

## 5. 提示词槽位（shot.py）

别写一整段抒情文字。按**槽位**填，每个槽位只放一件事：

```
【主体】【动作】【镜头：景别·机位·焦段·光圈】【光：光位·色温】
【色：锁定调色板】【质感】【运动】【情绪】【画面比例】【补充】【禁止】
```

同场景多镜头时，**只改「主体」和「动作」两行**，其余逐字复制 —— 这是让一场戏看起来
"像同一个人拍的"最可靠的办法。`shot.py spec` 会自动生成这段「一致性锁」。

出图后回查：`shot.py verify 成品.png --palette "#E4744A,#2E4756"` —— 确认画面真按锁色走了。

---

## 6. 视频别忘（vframe.py）

图能一张张看，视频不能。所以视频只查三件事：

1. **闪烁**：相邻帧亮度跳变 > 0.06 的帧占比，> 5% 就是 bad
2. **卡帧**：连续 3 帧以上几乎不动
3. **漂移**：整段亮度单调下滑（多半是生成时的曝光漂移）

```bash
python vframe.py extract clip.mp4 -o frames --fps 2
python vframe.py analyze frames            # 出 JSON + verdict
python vframe.py sheet frames -o sheet.jpg # 一眼看全片
```

---

## 7. 踩过的坑（本机实测，别再踩）

1. **PIL 的 `"LAB"` 模式不能用。** RGB→LAB→RGB 往返在 Pillow 12.3 上会产出霓虹色
   （实测取色出来是 `#00FFFF / #FF00FF`）。调色板聚类改用 **YCbCr 加权 k-means**，
   色彩迁移改成**自己实现的 CIELAB**（往返误差 4e-8）。
2. **"平台型"评分没有区分度。** 第一版阈值函数在区间内一律给 100 分，结果 8 张图全是满分，
   等于没量。必须用**有理想点的梯度函数**（理想点 100、区间边缘 78）。
3. **Windows 下 `glob` 不区分大小写。** `*.png` 和 `*.PNG` 会匹配同一批文件 → 批量处理跑两遍。
   凡是 glob 出来的列表都要按 `abspath.lower()` 去重。
4. **WCAG 对比度必须做 sRGB 反 gamma。** 直接用 `0.2126R+0.7152G+0.0722B` 算，
   深色文字配浅底会被严重低估（实测 3.12:1，正确值 8.19:1，一个判 warn 一个判 ok）。
5. **"底噪"要只量背景像素。** 把文字笔画一起算进去，std 必然大，会稳定误判。
6. **清晰度一定要给 `--baseline`。** 没有参考图时它只能记录原始值，不能下结论。
7. **中文输出要给控制台 UTF-8**：`chcp 65001` 或 `$env:PYTHONIOENCODING='utf-8'`，
   否则 PowerShell 里全是乱码（脚本本身没问题）。
8. **`--dry-run` 是你的保险。** 批量处理前先 `--dry-run` 看一眼要动哪些文件。
9. **ffmpeg 抽帧的两个坑**：`-vsync` 已废弃，要用 `-fps_mode passthrough`（否则会补帧/丢帧，
   `dluma` 序列直接失真）；`-ss` 放在 `-i` 前面是**快速 seek**，会跳到最近的关键帧上，
   秒数对不上 —— 要精确定点取帧必须把 `-ss` 放在 `-i` 后面。
10. **"N 帧没动"是 N−1 个连续小差分。** `dluma[i]` 描述的是 `i-1 → i` 的变化，
    所以帧 1,2,3 相同、帧 4 才变 → 冻结区间是 `[1,3]` 而不是 `[1,4]`。算区间时最容易少一帧。
11. **`-pattern_type glob` 在 Windows 上不可用**（实测报 `Function not implemented`）。
    要合成测试视频，先把图按 `f000.png f001.png ...` 重命名成序列，再用 `-i f%03d.png`。
12. **`strip` 取 t 正好等于片长会抽不到帧**（容器时长 ≠ 该时刻真的有帧）。
    取帧要允许由近到远退让重试，6.000s 的片子退到 5.500s 才出图。
13. **PowerShell 写 JSON 会带 BOM。** `Set-Content -Encoding UTF8` 写出的文件，
    `json.load(open(p, encoding="utf-8"))` 直接报 `Unexpected UTF-8 BOM`。
    凡是读用户手写的 JSON（shots.json、workflow 配置），一律用 **`encoding="utf-8-sig"`**。
14. **噪声会把清晰度垫高。** 加噪图的梯度能量天然更高，`sharp` 反而更好看 ——
    自检时「加噪候选 96.5 分」赢过了「干净候选 96.4 分」，查下去才发现
    `illustration` 的噪声门槛定成了 0.034，而干净交付物实测只有 0.005–0.015。
    **噪声门槛必须按实测标定**，否则排序会被加噪图带偏。这就是 `autoloop.py selftest` 存在的理由。
15. **`--dry-run` 要提前返回。** 演练模式下没有真实产物，继续走评分会去读不存在的文件。
    凡是有「先生成再分析」两阶段的脚本，dry-run 必须在第一阶段就返回。

---

## 8. 交付前检查清单

- [ ] 硬门槛全过（`vqc.py score` 的"硬门槛未过"为 0 项）
- [ ] 总分在同批里排前 1/3（`pick` 排过序）
- [ ] 有文字的图跑过 `textsafe`，AA 4.5:1 全过
- [ ] 成套交付跑过 `series`，一致性 ≥ 70
- [ ] 视频跑过 `analyze`，verdict = ok
- [ ] 原图与修复图**都留着**（修复参数写在命令里，可复现可回滚）

---

## 附：文件清单

```
田伟平设计总监大师级别/
├── SKILL.md                       # 本文件
├── references/
│   ├── quality-gates.md           # 各场景阈值表 + 为什么这么定
│   ├── prompt-slots.md            # 槽位取值表 + 三套现成模板
│   ├── symptom-rx.md              # 症状 → 处方（含前后参数与命令）
│   └── comfyui.md                 # 接本机 ComfyUI 生产栈（端口/解释器/produce.py 契约/降级/生命周期）
└── scripts/
    ├── autoloop.py                # 编排：run / demo / selftest
    ├── vqc.py                     # 量化：score/pick/compare/palette/series/textsafe/report
    ├── vfix.py                    # 修复：autolevel/unsharp/chroma/sat/unify/grain/resize/recipe/batch
    ├── shot.py                    # 编译：build/spec/verify/list
    └── vframe.py                  # 视频：extract/analyze/sheet/strip
```

## 附二：本机路径速查

| 项 | 值 |
|---|---|
| 首选解释器 | `F:\ComfyUI_windows_portable\python_embeded\python.exe`（有 piper，全栈通用） |
| 备用解释器 | `F:\AI\ComfyUI\venv\Scripts\python.exe`（无 piper） |
| 生成栈入口 | `<工作区>\local-stack\produce.py` |
| ComfyUI 实例 | 8189（本栈，随会话退出）/ 8188（用户自建，常驻） |
| ffmpeg | `C:\Users\seven\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_...\bin\ffmpeg.exe` |

细节与已过期说法见 `references/comfyui.md`。**改动阈值后必须重跑 `autoloop.py selftest`。**
