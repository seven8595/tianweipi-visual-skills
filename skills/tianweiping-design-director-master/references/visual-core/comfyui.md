> **脚本实际位置**：`田伟平设计总监大师级别\scripts\`（本技能目录内）。下文示例里的 `$sk` 即指向该目录。

# 与本地 ComfyUI 生产栈对接

> 本文件是 reference，不是 skill 主文件。它讲清一件事：**本 skill 的四件工具（vqc / vfix / shot / vframe）
> 与本地生成栈（`local-stack/produce.py`）如何接成闭环**。
>
> 上游依据：`local-stack/LOCAL-FIRST.md`（本机实测总纲，数字来源）、`README-comfy-deploy.md`（部分已过期，见 §1.4）、
> `local-stack/produce.py` 与 `local-stack/comfy_client.py` 源码。
>
> 本文件里的每个数字都来自上述文件或本次读源码/实测；无法核实的写「未核实」，不估。

## 1. 本机事实

### 1.1 解释器（两个都在，首选 python_embeded）

| 解释器 | 版本 | 实测具备 | 用途 |
|---|---|---|---|
| `F:\ComfyUI_windows_portable\python_embeded\python.exe` | 3.13.14 | requests 2.34.2、piper（可导入）、numpy 2.5.2、Pillow 12.3.0 | **首选**：`produce.py`、`tts.py`、本 skill 四个脚本 |
| `F:\AI\ComfyUI\venv\Scripts\python.exe` | 3.11.9 | requests 2.34.2、numpy 2.4.6、Pillow 12.3.0；**无 piper**（实测 ImportError） | 仅当需要 venv 里的 torch 等库时用；`comfy_client.py` 的 docstring 指向它 |

**为什么首选 python_embeded**：`LOCAL-FIRST.md` §10.3 与 `produce.py` docstring 都写明它是「同时具备 requests + piper」
的解释器，`tts.py` 的 ImportError 分支也直接提示「use the python_embeded interpreter」。venv 缺 piper，
跑 `produce.py tts` / `smoke` 会直接失败。**本 skill 的四个脚本只需要 numpy + Pillow，两个解释器都能跑；
统一用 python_embeded，省得一半命令能跑一半不能跑。**

### 1.2 GPU 与版本

| 项 | 值 | 来源 |
|---|---|---|
| GPU | NVIDIA GeForce RTX 5080，16303 MiB（约 15.9 GiB） | 本次 nvidia-smi 实测 |
| 驱动 | 616.64 | 本次 nvidia-smi 实测 |
| ComfyUI | **0.38.0** | LOCAL-FIRST §9（校正技能库里的 0.37.0） |
| 显存余量 | 空闲约 14.6GB（README 记的交付时快照） | README-comfy-deploy.md |
| 跑满时的资源镜像 | GPU 占用 15.6/16.3GB、利用率 99%、58°C、231W；ComfyUI 进程 RSS 6.38GB；系统内存空闲只剩 1.7GB | LOCAL-FIRST §3 |
| 自定义节点 | ComfyUI-GGUF、ComfyUI-WanVideoWrapper（均已加载成功） | README-comfy-deploy.md |

### 1.3 三个端口（别搞混）

| 端口 | 归属 | 状态 | 产物目录 |
|---|---|---|---|
| 8188 | 用户自建（`--listen 0.0.0.0 --lowvram`） | 常驻，LOCAL-FIRST 记录「本次未改动」；**本文件写作时探测为 DOWN（未运行）** | `F:\AI\ComfyUI\output` |
| 8189 | 本栈沙箱实例（`comfy-runtime` 重定向目录） | **随会话退出**；双击 `start-stack.bat` 可常驻 | `comfy-runtime\output` + `local-stack\out` |
| 8190 | 旧 Codex 交付（SDXL-only） | 未运行 | — |

**探测优先级写在源码里**：`produce.py:probe_host()` 依次 `GET http://127.0.0.1:8189/system_stats`、`8188/system_stats`，
谁先返回 200 用谁，都不通则 fallback 到 8189（随后提交才会报连接错误）。`comfy_client.py` 的默认 host 是
`COMFY_HOST` 环境变量或 `127.0.0.1:8189`。**两个实例哪个在都能用，但同一时刻只有一块卡，不要同时压。**

### 1.4 README-comfy-deploy.md 里已过期 / 需更正的说法

| README 原文 | 判定 | 实际 |
|---|---|---|
| `node comfy.js --workflow ...`（调用方式整节） | **已过期** | LOCAL-FIRST §10.3：本机没有 `node`（本次复核：`Get-Command node` 无结果）；`comfy.js` 跑不了。统一走 `produce.py` / `comfy_client.py` |
| `pwsh -File comfy-runtime\start-comfy.ps1` | **已过期** | LOCAL-FIRST §10.4：`pwsh` 不在 PATH（本次复核：无结果），本机是 PowerShell 5.1。内层调用用 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File` |
| 「服务地址 `http://127.0.0.1:8188`」 | **需更正** | 8188 是用户自建实例；本栈沙箱实例是 **8189**。README 头部已指向 LOCAL-FIRST，但正文未同步 |
| Python 行只写 venv 解释器 | **不完整** | `produce.py` 要 python_embeded（piper）；见 §1.1 |
| 目录重定向参数、不用 `--base-directory` 的理由、模型只读路径、`--reserve-vram 1.0` | 仍然有效 | 与 `comfy-runtime\start-comfy.ps1` 一致（本次核对该脚本含 `--reserve-vram 1.0`） |
| 生命周期「沙箱回收子进程、实例由 DSH 后台作业持有」 | 仍然有效 | 与 LOCAL-FIRST §7 一致 |

### 1.5 工作流文件位置（API 格式）

`C:\Users\seven\Documents\deepseek-harness\default-workspace\local-stack\workflows\`

| 文件 | 用途 | 关键节点（`--set` 可覆写） |
|---|---|---|
| `flux_t2i.json` | Flux1-dev 文生图 | `4.text` 提示词、`5.guidance`、`7.width/height`、`8.seed/steps`、`10.filename_prefix` |
| `h3_i2v.json` | MiniMax-H3 图生视频含音频 | `5.lora_name`、`6` 首帧（上传）、`7.prompt/width/height/length`、`8.noise_seed`、`11.steps`、`16.filename_prefix` |
| `wan22_ti2v.json` | Wan2.2 TI2V-5B 纯文生视频 | `4.text`、`5.text` 负向、`6.width/height/length`、`8.seed/steps/cfg`、`11.filename_prefix` |

工作流里声明的权重名（源码核实）：`flux1-dev.safetensors`、`minimax_h3_fl2va_pruned_int8_convrot.safetensors`、
`qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`、`wan2.2_ti2v_5B_fp16.safetensors`（wan22 由 `doctor` 的检查表列出）。

### 1.6 produce.py 全部子命令（源码 `build_parser()` 核实）

`doctor` `image` `video` `t2v` `tts` `upscale` `mux` `inventory` `watch` `batch` `free` `cleanup` `smoke`

> 注意：`free` 在 LOCAL-FIRST §1 与 §8 的子命令清单里**都没出现**（§8 那串是
> image/video/t2v/tts/upscale/mux/batch/inventory/watch/cleanup/doctor/smoke），但它确实在源码里存在。

## 2. produce.py 调用契约（参数名逐条核对源码）

**全局选项必须写在子命令前面**（它们注册在顶层 parser 上，写在子命令后会被 argparse 拒绝）：

```powershell
$py   = 'F:\ComfyUI_windows_portable\python_embeded\python.exe'
$prod = 'C:\Users\seven\Documents\deepseek-harness\default-workspace\local-stack\produce.py'

& $py $prod --json --host 127.0.0.1:8189 image --prompt "..." --out out\a.png   # 全局选项在前
& $py $prod image --prompt "..." --out out\a.png --json                        # 错误：--json 会被拒
```

| 子命令 | 必填 | 可选（默认） | 源码位置 |
|---|---|---|---|
| `image` | `--prompt` `--out` | `--width 1024` `--height 1024` `--steps 20` `--seed 20261008` `--guidance 3.5` `--timeout 1800` | `cmd_image` |
| `video` | `--first-frame` `--prompt` `--out` | `--width 832` `--height 480` `--seconds 5.0` `--steps 4`（仅 4 或 8）`--seed 20261008` `--timeout 3600` | `cmd_video` |
| `t2v` | `--prompt` `--out` | `--negative "blurry, low quality, ..."` `--width 704` `--height 480` `--seconds 5.0` `--steps 30` `--cfg 5.0` `--seed 20261008` `--timeout 3600` | `cmd_t2v` |
| `tts` | `--out` | `--text` `--text-file` `--length-scale 1.0`（转发给 `tts.py`） | `cmd_tts` |
| `upscale` | `--in` `--out` | `--scale 2`（2/3/4）`--model realesrgan-x4plus`（4 选 1）`--gpu 0` `--fps`（视频重封装用，缺省 24.0） | `cmd_upscale` |
| `mux` | `--video` `--out` | `--audio` `--reencode` `--keep-original-audio` `--shortest` | `cmd_mux` |
| `batch` | `--prompts-file` `--first-frame` `--out-dir` | `--width 832` `--height 480` `--seconds 5.0` `--steps 4`（4/8）`--seed 20261008` `--timeout 3600` `--dry-run` | `cmd_batch` |
| `inventory` | — | 仅全局 `--json` `--host` | `cmd_inventory` |
| `watch` | — | `--seconds 0`（0=采到 Ctrl+C）`--interval 3.0` | `cmd_watch` |
| `cleanup` | — | `--purge-frames` | `cmd_cleanup` |
| `free` | — | 仅全局选项 | `cmd_free` |
| `doctor` | — | 仅全局选项 | `cmd_doctor` |
| `smoke` | — | `--prompt` `--motion` `--voice` `--seconds 5.0` `--upscale-model realesrgan-x4plus` `--timeout 3600` | `cmd_smoke` |

**与 LOCAL-FIRST §1 示例的差异（照源码，不照抄示例）**：

1. LOCAL-FIRST §1 的 `batch` 示例写成 `batch --prompts-file shots.txt --first-frame f.png --out-dir out\ep01`，
   三个参数名与源码一致（`--prompts-file` / `--first-frame` / `--out-dir`）。但 §9 表格里的
   `produce.py batch --prompts-file` 是省略写法，**只给 `--prompts-file` 会直接报缺参数**。
2. `upscale` 的输入参数名是 **`--in`**（`dest="infile"`），不是 `--input`。
3. `t2v` 的默认分辨率是 **704×480**（不是 832×480），默认步数 30。
4. `video` / `batch` 的 `--steps` 有 `choices=[4, 8]`：传 5 会被 argparse 直接拒绝；`steps<=4` 时
   `cmd_video` 自动换 4-step turbo LoRA，否则换 8-step LoRA。
5. `--json` 是**全局**开关：`produce.py image --json` 会报错，必须 `produce.py --json image`。

**两处源码行为要提前知道**：

- `cmd_image` / `cmd_video` 先把产物下载到固定目录 `local-stack\out\image` / `out\video`，
  再用 `newest()`（按 mtime）挑最新的一个 `copy2` 到 `--out`。**并发跑两个 image 进程会互相抢错文件** ——
  这是「必须串行」的硬理由之一。
- `video` 的帧数由 `h3_length_for(seconds)` 自动对齐到 `≡5 (mod 17)`；`t2v` 对齐到 `≡1 (mod 4)`。
  **不要自己算 length，也不要绕过它直接改工作流。**

## 3. 闭环怎么接：autoloop.py

### 3.1 状态与命令行契约

`田伟平设计总监大师级别/scripts/autoloop.py` 已落盘；下表与下方示例**逐条核对过该脚本的 `build_parser()` / `run_shot()` 源码**。

| 参数 | 含义（默认值） |
|---|---|
| `--shots` | 镜头清单（必填）。JSON 顶层读 `profile` 与 `shots[]`；每项缺 `name` 时按 `shot{i:02d}` 命名 |
| `--out` | 工作目录（必填）。每镜一个子目录 `{序号:02d}_{name}\` |
| `--gen-cmd` | 生成命令模板（默认空串）。**为空且未加 `--dry-run` 时直接报错** |
| `--cand` | 每个镜头出几张候选（默认 4） |
| `--profile` | 覆盖 shots.json 里的 profile 与 vqc 评分 profile（默认取 shots.json 的，再退到 `illustration`） |
| `--recipe` | vfix 修复步骤串（默认 `autolevel:black=1.0,white=99.0;chroma:size=5,strength=0.7;unsharp:radius=1.4,amount=55,threshold=3`） |
| `--rounds` | 修复-复评最大轮数（默认 2） |
| `--min-consistency` | 成套一致性阈值（默认 70.0），低于它触发 `unify` 到 `{out}\_unified\` |
| `--no-unify` / `--unify-strength` | 关闭自动统一 / 统一强度（默认 1.0） |
| `--report` / `--json` / `--dry-run` | 报告路径 / 机器可读输出 / 只演练流程 |
| `demo --out --mock-src` | 无 GPU 自检（`--profile` 默认 `illustration`）；`selftest` 是另一个子命令，校验 vqc 能抓已知缺陷 |

| 变量 | 填什么 |
|---|---|
| `{prompt}` | 该镜头的提示词。脚本先把 `shot.py compile_prompt()` 的 zh 结果压成**单行并截到 600 字符**，再替换进去 |
| `{seed}` | 整数种子。脚本下发的是 `1000 + i*7919`（`seed0=1000`，`i` 从 0 起），即 1000 / 8919 / 16838 / 24757 |
| `{out}` | 该候选的目标路径，**唯一**：`{out}\{序号:02d}_{name}\cand{i+1:02d}.png` |
| `{index}` | 候选序号（1..N），只用于命名/日志，不参与采样 |

替换是**纯字符串 `.replace()`**（`{prompt}` → `{seed}` → `{out}` → `{index}`），所以模板里的引号要自己处理好。

### 3.2 完整可运行示例（image 子命令）

```powershell
$py   = 'F:\ComfyUI_windows_portable\python_embeded\python.exe'
$root = 'C:\Users\seven\Documents\deepseek-harness\default-workspace'
$sk   = 'C:\Users\seven\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.user_skills\田伟平设计总监大师级别\scripts'

& $py "$sk\autoloop.py" run `
  --shots "$root\waipo-story\shots.json" `
  --out   "$root\waipo-story\work" `
  --cand 4 `
  --profile product `
  --gen-cmd "& '$py' '$root\local-stack\produce.py' image --prompt `"{prompt}`" --seed {seed} --out `"{out}`" --width 1024 --height 1024 --steps 20"
```

- 内层用**反引号转义的双引号**（`` `" ``），因为外层的 `--gen-cmd` 已经占用了双引号。
- 同一条模板在 Git Bash / WSL 下改用 `\"`：`--prompt \"{prompt}\"`、`--out \"{out}\"`，路径仍是 Windows 形式。
- 展开后 autoloop 逐条执行，`{index}` = 1..4、`{seed}` = 1000 / 8919 / 16838 / 24757、`{out}` = `...\cand01.png` … `cand04.png`：
  `... produce.py image --prompt "<shot01 提示词>" --seed 1000 --out <work>\01_shot01\cand01.png --width 1024 --height 1024 --steps 20`
- 换成视频：`{out}` 后缀改 `.mp4`，命令换成
  `produce.py video --first-frame <首帧> --prompt "{prompt}" --seed {seed} --out "{out}" --seconds 5 --steps 4`
  （`--first-frame` 是整镜固定值，写死在模板里，不占变量）。

出图后由本 skill 接手（同一批候选，同一 profile）：

```powershell
$sk = "$sk"
& $py "$sk\vqc.py" pick "$root\waipo-story\work\s01\*.png" --profile product
& $py "$sk\vfix.py" recipe "$root\waipo-story\work\s01\c03.png" -o "$root\waipo-story\work\s01\fixed.png" `
      --steps "autolevel:black=1.2,white=98.5;chroma:size=5,strength=0.7;unsharp:radius=1.4,amount=60,threshold=3"
& $py "$sk\vqc.py" score "$root\waipo-story\work\s01\fixed.png" --profile product --baseline <参考图.png>
```

### 3.3 为什么每个候选要换 seed

- seed 是**唯一**能让同一条提示词产出不同画面的参数。其余参数（prompt / 尺寸 / 步数 / guidance）在候选之间
  必须逐字相同，否则 `vqc.py pick` 比较的不是同一个问题的四个答案，量化排序失去意义。
- `produce.py image` 的 `--seed` 默认 20261008，`batch` 里作者的做法是 `args.seed + i - 1`（20261008、20261009、…）；
  autoloop 则是 `1000 + i*7919`（1000、8919、16838、24757）。**两者都只是「每个候选一个种子」，不要用随机数**：
  出问题时要用 seed 精确复现赢家那张。（注意 autoloop 的取值不是 `--cand` 的下标本身，`{index}` 只用于命名。）
- 换 seed 只换噪声初值，不换模型；4 张候选的成本 = 4 × 单张时间，且必须串行（§5.1）。

## 4. 分工边界

| 环节 | 归 produce.py（生成栈） | 归本 skill（质检栈） |
|---|---|---|
| 出图 / 图生视频 / 文生视频 | `image` `video` `t2v` `batch` | — |
| 放大 / 转码 / 封装 | `upscale` `mux` | — |
| 配音 | `tts` | — |
| 算力盘点 / 峰值采样 / 收尾 | `inventory` `watch` `cleanup` `free` `doctor` | — |
| 提示词编译 | — | `shot.py build / spec / verify / list` |
| 画面量化 / 排序 / 成套一致性 | — | `vqc.py score / pick / compare / palette / series / textsafe / report` |
| 定向修复 / 统一风格 | — | `vfix.py autolevel / unsharp / chroma / sat / unify / grain / resize / recipe / batch` |
| 视频帧闪烁 / 卡帧检测 | — | `vframe.py extract / analyze / sheet / strip` |
| 闭环编排 | 只被调用，不感知 autoloop | `autoloop.py`（生成 → vqc 排序 → vfix 修复 → 复评） |

**绝对不要重复做的事**：

1. **不要在 autoloop 或任何新脚本里重写 ComfyUI HTTP 客户端。** 已经有 `local-stack\comfy_client.py`
   （`base_url` / `apply_set` / `upload_image` / `collect_files` / `download`），`produce.py:submit()` 复用的就是它，
   源码注释写明「Same code path as comfy_client's CLI, so the two never drift」。
2. **不要新建 / 改写工作流 JSON。** 三个模板已在 `local-stack\workflows\`，改参数用 `--set node.field=value` 或
   `produce.py` 已有的开关；手改模板会让 `doctor` 的模型名检查失效。
3. **不要在 autoloop 里自己算帧数 / LoRA / 尺寸对齐。** 那是 `h3_length_for()`、`cmd_video` 的职责。
4. **不要把中间候选写进 `local-stack\out\`。** 那会让 `newest()` 的 mtime 挑选逻辑互相干扰；
   候选一律写自己的 `--out <work>\...`，收尾用 `produce.py cleanup`。
5. **不要用「回生成」替代 vfix。** 能被 vfix 修掉的问题（发灰 / 脏 / 糊 / 不统一）不要重新出图 ——
   回 ② 等于重掷骰子，连已经对的部分都会一起变。

---

## 5. 降级与排队

### 5.1 单卡 = 串行

一块 RTX 5080（16303 MiB）跑 `image` 时 guidance/size 不变；跑 H3 时实测占满到 15.6/16.3GB。
**autoloop 必须串行执行候选，不要并行、不要开多个 produce.py 进程**（除了显存，还有 §2 说的产物挑选竞态）。
`batch` 子命令本身就是逐条串行（源码打印「批量出片：N 条，逐条串行（GPU 只有一块）」），可作为串行的参照实现。

### 5.2 不够时按 LOCAL-FIRST §5 的顺序降（不要自己发明）

1. 降分辨率（H3：832×480 → 640×384 → 512×288）
2. 降帧数（时长 5s → 2s；H3 的 length 必须 ≡ 5 mod 17）
3. 换模型（H3 → Wan2.2 TI2V-5B → Wan2.1 I2V-14B GGUF）
4. 关掉其它 GPU 程序（**不同时开 ComfyUI + Ollama + realesrgan**）
5. 仍不行 → 报用户，摆出「本机方案耗时/成本」vs「云方案耗时/成本」两列，等授权，不擅自开实例

补充：画质相关参数变更，**先出 1 张/1 段对照给用户确认，再批量**（§5 末句）。
另外 `produce.py free` 可让 ComfyUI 卸载模型归还显存（缓存会占住约 10GB，和用户 8188 实例抢卡时用），
它是 §5 第 4 条「关掉其它 GPU 程序」的、比关进程更温和的前置动作。

### 5.3 autoloop 跑之前要不要先 inventory

**要。** 理由与顺序：

1. `produce.py inventory` 是只读的，给 GO / NO-GO。它按 **空闲内存 20GB**（源码 `H3_RAM_FLOOR_GB = 20.0`）判定：
   ≥20GB 判 `video-h3 GO`；<20GB 判 `GO(慢)`（源码注释：实测可跑，832x480/124f/4步约 70–150s，但明显变慢）；
   ComfyUI 不在线则 `NO-GO`。所以它不会拦你，但会告诉你这次是快还是慢。
2. 它同时报磁盘与工具链（ffmpeg / realesrgan / piper / 三个工作流文件是否在位）——autoloop 依赖其中至少一个生成通道
   和后续的 vfix/vframe 工具链。
3. 内存是这套部署的实际瓶颈（LOCAL-FIRST §4：「内存不是显存才是瓶颈」）。跑批量前先关掉
   Chrome / 豆包 / ChatGPT / Steam / 微信，能把 Flux 从 3.7–6.9 s/it 拉回 1–2 s/it。
4. 批量估算按「实测单条 × N × 1.3 安全系数」，**超过 20 条先跑 2 条小样校准**（§3）。

---

## 6. 生命周期

| 实例 | 谁起的 | 会话结束后 | 备注 |
|---|---|---|---|
| `127.0.0.1:8189` | Agent 的 DSH 后台作业 | **随之退出，需重启** | 重启用 `start-stack.bat`（双击）或 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File local-stack\start-stack.ps1`，`-Port` 默认 8189 |
| `127.0.0.1:8188` | 用户双击 `F:\AI\ComfyUI\start_comfyui.bat` | 不受影响，一直挂着 | 产物落在 `F:\AI\ComfyUI\output` |

**autoloop 中途服务挂了会怎样**：`produce.py` 的 `submit()` 在提交阶段对连接失败会抛异常，
`main()` 捕获后打 `! <错误>` 并返回退出码 1；执行中途挂掉则卡在 `history` 轮询直到 `--timeout`（image 默认 1800s、
video 3600s）后抛 `TimeoutError`，同样退出码 1。**表现是 autoloop 那个候选失败/变慢，而不是静默出错。**

**怎么续跑**：`--out` 目录结构是确定性的（`{out}\{序号:02d}_{name}\cand{i+1:02d}.png`），
而且 `run_shot()` 遇到**已存在的候选会直接复用、不再调生成命令**（源码 `if os.path.exists(p): ... continue`），所以：

1. 先 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File local-stack\start-stack.ps1` 把 8189 起回来；
2. `produce.py doctor`（或 `inventory`）确认在线与显存；
3. 删掉没生成完的候选文件（0 字节 / 打不开 / mock 之外的残留），**原样重跑同一条 autoloop 命令**：
   已完成的候选会被跳过，只补缺失的那些。
4. 注意两点：候选是「按文件存在即视为已完成」的，所以**半张图必须删**（否则会被算进排序）；
   另外 `{seed}` 由候选下标决定，不随重跑次数变化 —— 复现性天然成立，不会因为续跑而抽到不同结果。

**常驻建议**：想跨会话稳定跑，就双击 `local-stack\start-stack.bat`（跑 8189，完全在工作区内，
不污染用户自己的 ComfyUI 状态）。

---

## 7. 踩坑清单（从脚本里调 produce.py 相关）

| # | 现象 | 原因 | 做法 |
|---|---|---|---|
| 1 | PowerShell 里中文提示词/中文输出变乱码或孤立代理字符，Python 抛 `UnicodeEncodeError` | PS 5.1 管道传中文给 native exe 会坏；宿主按 GBK 解码 UTF-8 | 文本走 **UTF-8 文件**（`--text-file` 就是这个原因）；看正常中文用 `chcp 65001` 或给 python 加 `PYTHONIOENCODING=gbk`；本 skill 脚本旁挂 UTF-8 控制台 |
| 2 | ffmpeg 报未知参数 `-vsync` | ffmpeg 9.0.2 已移除 `-vsync` | 用 `-fps_mode passthrough`（`produce.py` / `vframe.py` 内部均已如此） |
| 3 | 想用 `node comfy.js` 调工作流，命令找不到 | **本机没有 `node`** | 用 `produce.py`；`comfy_client.py` 的 docstring 虽提到 venv 解释器，实际两个解释器都有 requests |
| 4 | 脚本里写 `pwsh -File ...` 失败 | **`pwsh` 不在 PATH**，本机是 PowerShell 5.1 | 用 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ...` |
| 5 | H3 提交被拒 / 帧数报错 | H3 的 `length` 必须 ≡ 5 (mod 17)；Wan 的 `length` 必须 ≡ 1 (mod 4) | 交给 `produce.py`：`h3_length_for()` 与 `cmd_t2v` 自动对齐，不要手写 length |
| 6 | H3 成片中间出现 2×2 分屏拼贴 | H3 的多镜头叙事行为，不是流水线缺陷（832×480/124 帧实测，约 t=2.5s 处出现） | 要强制单镜头：prompt 只写**一个动作 + 一个运镜**，别写故事性描述 |
| 7 | ffmpeg 一个报错刷出几百行编译选项 | 未关 banner | 内部调用统一 `-hide_banner -loglevel error`（`produce.py` 已如此） |
| 8 | 直接 `import` 工作流 JSON 改节点，或手改 `h3_i2v.json` | 模板是 `doctor` 的检查对象，手改会让模型名检查失效 | 用 `--set node.field=value`（`comfy_client.apply_set`，值按 JSON 解析）或 produce.py 开关 |
| 9 | 显存被上一次任务缓存占住，下一个任务变慢/OOM | ComfyUI 缓存约 10GB | `produce.py free`；再不行按 §5.2 第 4 条关其它 GPU 程序 |
| 10 | `Get-CimInstance` 之类的查询在沙箱里被拒 | DSH 沙箱策略 | 用 `produce.py inventory` / `watch` 取等价信息 |
| 11 | 大批量跑到一半才发现链路不通 | 没有先盘点 | 先 `inventory`（GO/NO-GO）再 `batch --dry-run`（只解析 prompts、不提交 GPU） |

---

## 8. 先跑冒烟：最小成本验证通路

目标：用 **1 个镜头 × 2 个候选、低分辨率、短步数** 把「生成 → 量化 → 排序 → 修复 → 复评」串一遍，
确认通路而不是确认画质。顺序如下（全部用绝对路径）。

```powershell
$py   = 'F:\ComfyUI_windows_portable\python_embeded\python.exe'
$root = 'C:\Users\seven\Documents\deepseek-harness\default-workspace'
$sk   = 'C:\Users\seven\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.user_skills\田伟平设计总监大师级别\scripts'
$prod = "$root\local-stack\produce.py"
$sk   = "$sk"

# 0) 后端在线 + 显存/内存/工具链
& $py $prod inventory

# 1) 无 GPU 自检：先证明排序/修复/复评这段是通的
& $py "$sk\autoloop.py" demo --out "$root\smoke\work" --mock-src "<任一现成 png>"

# 2) 最小生成：768x768、12 步、2 个 seed（对照实测 768/20 步热态 85.2s，2 张约 2–3 分钟）
New-Item -ItemType Directory -Force "$root\smoke\cand" | Out-Null
& $py $prod image --prompt "a lone lighthouse on a cliff at dusk, oil painting" `
      --width 768 --height 768 --steps 12 --seed 20261008 --out "$root\smoke\cand\c01.png"
& $py $prod image --prompt "a lone lighthouse on a cliff at dusk, oil painting" `
      --width 768 --height 768 --steps 12 --seed 20261009 --out "$root\smoke\cand\c02.png"

# 3) 量化排序 → 看 vqc 是否真的把两张分开（同 profile 才可比）
& $py "$sk\vqc.py" pick "$root\smoke\cand\*.png" --profile illustration

# 4) 定向修复 → 复评
& $py "$sk\vfix.py" recipe "$root\smoke\cand\c01.png" -o "$root\smoke\cand\fixed.png" --steps "autolevel;chroma;unsharp"
& $py "$sk\vqc.py" score "$root\smoke\cand\fixed.png" --profile illustration --baseline "$root\smoke\cand\c02.png"

# 5) 接 autoloop（把 §3.2 的 --gen-cmd 原样搬来，只改 --cand 2 与尺寸/步数）
& $py "$sk\autoloop.py" run --shots "<一份只有 1 个镜头的 shots.json>" --out "$root\smoke\auto" `
      --cand 2 --profile illustration `
      --gen-cmd "& '$py' '$prod' image --prompt `"{prompt}`" --seed {seed} --out `"{out}`" --width 768 --height 768 --steps 12"
```

放大的判据（不与下面的数字冲突再放大）：

| 项 | 冒烟档 | 正式档 | 依据 |
|---|---|---|---|
| 分辨率 | 768×768 | 1024×1024 | 实测 768/20 步热态 85.2s；1024/20 步首跑 149.6s（含 t5xxl 冷加载） |
| 步数 | 12 | 20（image 默认） | `image` 默认 `--steps 20` |
| 候选数 | 2 | 4（autoloop `--cand 4`） | 单卡串行，成本线性 |
| 视频（如需接） | 640×384 / 2s / 4 步 | 832×480 / 5s / 4 步 | 实测 640×384/39 帧 69.1s；832×480/124 帧 120.2s |
| 批量 | 1 镜 | 先 2 条校准，再按「实测 × N × 1.3」 | LOCAL-FIRST §3 工期外推 |
| 视频质检 | `vframe.py extract --fps 2` → `analyze` | 同 | `analyze` 的 flicker/freeze 阈值默认 0.06 / 0.004 |

冒烟通过的检查点：`inventory` 有 GO、两张候选都落地且非 0 字节、`pick` 排出名次且给出「差在哪」、
`vfix` 输出能打开、`score --baseline` 给出相对值（没有 baseline 时 `sharp` 只能记录原始值、不能下结论）、
`autoloop demo` 与 `run` 都不需要人工介入。

---

## 9. 未核实项（不要当事实用）

1. **`shots.json` 的实际内容** —— 已知结构是顶层 `profile` + `shots[]`（每项 `name` 可选，其余键交给
   `shot.py compile_prompt()`），但 `waipo-story\shots.json` 尚未核验，示例路径只是占位。
2. **8188 / 8189 / 8190 在其它时刻的在线状态** —— 本文件写作时三者均探测为 DOWN；
   表中「常驻 / 随会话退出」来自 LOCAL-FIRST §7 的记述，不是本次探测结果。
3. **三处模型搜索路径下各权重的当前占用与校验值**（22GB / 19.5GB / 14.6GB / 9.3GB / 10.6GB 等来自 LOCAL-FIRST §2，
   本次未逐文件核验）。
4. **`qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`、`wan2.2_ti2v_5B_fp16.safetensors` 的磁盘存在性** ——
   只核对了它们出现在工作流 JSON 与 `doctor` 的检查表里。
5. **`realesrgan` 模型文件的具体清单** —— 只确认 `produce.py` 期望的程序路径
   `local-stack\bin\realesrgan\realesrgan-ncnn-vulkan.exe`（`doctor` 会检查），未逐一列举 `models\` 下的模型文件。
