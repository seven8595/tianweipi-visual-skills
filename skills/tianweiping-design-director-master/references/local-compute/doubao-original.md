---
name: local-compute-scheduler
description: 本机算力、云资源与成本调度（Windows RTX 5080 主机专用）。任何本地 AI 推理（Ollama/ComfyUI/MiniMax H3 视频生成/Wan2.1 I2V/出图/批量渲染/超分）启动前，先跑只读盘点再决定本机 vs 云，避免显存 OOM、内存爆掉和无效等待。触发词：本机跑、本地推理、显存不够、能不能本地跑、要多久、多久出图、多久生成视频、云服务器、成本、预算、5080、Ollama、ComfyUI、MiniMax、H3、Wan2.1、Hunyuan、Flux、SDXL、批量出图、批量生成、任务调度、显卡占用、内存不足、AI_OS、AI_WORKSPACE、超分、Real-ESRGAN。
---

# 本机算力调度（Windows RTX 5080 主机 · 已部署工作流版）

## ⚡ 30 秒决策树（agent 接到任务先读这里）

```
用户要跑本地 AI 任务
  ↓
跑 inventory.ps1 → 看末尾 GO/NO-GO
  ├─ NO-GO → 告诉用户缺什么（内存/显存/ComfyUI 没起），等他处理，不要硬跑
  └─ READY → 要跑 H3 视频？
        ├─ 单条试效果 → run-h3-sample.ps1 -Prompt "..." -DurationSec 5
        ├─ 批量出片   → prompts.txt → run-h3-batch.ps1 -PromptsFile prompts.txt
        └─ 长任务并行  → 另开窗口挂 watch-vram.ps1
  ↓
出片后跑 cleanup-check.ps1 → 把真实耗时/峰值显存填到基准表
```

**铁律**：
- 内存 <20GB 不跑 H3（主模型 19.5GB 要 offload 到内存）
- 不买新硬件、不开付费云实例（用户明确要求）
- 工作流 JSON 报错 → 转 comfyui-workflow-validation，本 skill 不修节点
- 剪映剪辑 → 转 jianying-cloud-ai-editing

---

## 0. 第一动作：先实测，不沿用旧状态

每次接到"跑本地 AI / 批量生成 / 渲染"类任务，**第一步必须**：

```powershell
powershell -ExecutionPolicy Bypass -File "<skill_dir>\inventory.ps1"
```

输出当前 CPU/RAM/显存/磁盘/RAM 占用 Top10/局域网邻居/Ollama 与 ComfyUI 状态。**不要相信本文件里的基线数字**——那是 2026-09-29 的快照，桌面应用一开多内存就变。

如果要跑长任务，另开一个 PowerShell 窗口挂监视：

```powershell
powershell -ExecutionPolicy Bypass -File "<skill_dir>\watch-vram.ps1"
# 任务跑完按 Ctrl+C，脚本会打印峰值显存和峰值内存
```

如果要跑 MiniMax H3 小样（ComfyUI 已启动在 :8188）：

```powershell
powershell -ExecutionPolicy Bypass -File "<skill_dir>\run-h3-sample.ps1" `
  -Prompt "a young woman walking through neon rain, slow motion" `
  -DurationSec 5 `
  -OutputPrefix "sample/neon_test"
# 自动加载 h3_template.json、改 prompt/时长/输出名、POST 到 ComfyUI、轮询到完成、打印耗时
# 提交前会自动预检：ComfyUI 在线、必需节点存在、5 个模型文件在盘上
```

如果要批量出 N 条（每行一个 prompt）：

```powershell
# 1. 写 prompts.txt（空行和 # 开头忽略）
# 2. 跑：
powershell -ExecutionPolicy Bypass -File "<skill_dir>\run-h3-batch.ps1" `
  -PromptsFile D:\AI_WORKSPACE\prompts.txt `
  -DurationSec 5 `
  -FirstFrame F:\upscale_work\input.jpg
# 逐条提交、失败自动重试 1 次、全部跑完写 batch_<timestamp>.csv 汇总
```

任务跑完后，收尾检查（只读，不删东西）：

```powershell
powershell -ExecutionPolicy Bypass -File "<skill_dir>\cleanup-check.ps1"
# 查：GPU 显存还被谁占、ComfyUI/ollama 进程是否还在、Ollama 模型是否驻留、
#     output 目录大小、当前磁盘和内存余量，最后列收尾 checklist
```

---

## 1. 硬件基线（2026-09-29 实测快照，仅参考）

| 部件 | 规格 | 实测状态 |
|---|---|---|
| 主板 | Gigabyte Z890M AORUS ELITE WIFI7 | — |
| CPU | Intel Core Ultra 7 270K Plus，24C/24T | — |
| 内存 | 32 GB DDR | **空闲仅 ~11 GB**（Chrome/Doubao/ChatGPT/Coze/Steam/抖音/微信 常驻吃 20 GB+） |
| GPU | NVIDIA RTX 5080，16 GB GDDR7，sm_120 (CC 12.0) | 空闲 14 GB，温度 ~35°C，驱动 616.64，CUDA 13.0 |
| 磁盘 C: | 500 GB NVMe | 空闲 222 GB |
| 磁盘 D: | 704 GB（AI_WORKSPACE / AI-OS 项目） | 空闲 160 GB |
| 磁盘 E: | 703 GB（ComfyUI portable 所在） | 空闲 219 GB |
| 磁盘 F: | 954 GB（最空，Real-ESRGAN 超分目录） | **空闲 828 GB，临时输出/缓存优先放这里** |
| 网络 | 仅 WLAN 2，192.168.31.159/24 | ARP 表只有路由器，**Mac/iPhone/iPad 当前不在网，不做分布式** |
| OS | Windows 11 专业版 26200 | — |

---

## 2. 已部署的推理栈（不要重复装，不要找错路径）

### 2.1 ComfyUI portable（主力）
- 路径：`E:\ComfyUI_windows_portable\`
- **版本：0.37.0**（MiniMax H3 节点从这版开始内置，`comfy_extras/nodes_minimax_h3.py` 自带，不需要装 custom_nodes）
- custom_nodes 现状：仅 `ComfyUI-GGUF`（用于加载 Wan2.1 GGUF 模型）
- **启动脚本（按优先级）**：
  1. `run_nvidia_gpu_fast_fp16_accumulation.bat` —— Blackwell 优化，优先用这个
  2. `run_nvidia_gpu.bat` —— 上面那个出问题再退回
  3. `run_cpu.bat` —— 不要用，慢 100 倍
- embedded Python：`python_embeded\python.exe`，torch 2.13.0+cu130，CUDA 可用
- **ML 任务一律用这个 embedded python；系统 Python 3.14 没装 torch，别用**

### 2.2 已下模型（实测清单，2026-09-29）

**MiniMax H3 视频生成全家桶（本机主力）**：
| 文件 | 位置 | 大小 | 用途 |
|---|---|---|---|
| `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | diffusion_models/ | 19.53 GB | H3 主模型（int8 量化） |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | text_encoders/ | 14.61 GB | Qwen3VL-32B 文本编码器（AWQ） |
| `minimax_h3_video_vae_fp16.safetensors` | vae/ | 4.85 GB | 视频 VAE |
| `minimax_h3_audio_vae_fp32.safetensors` | vae/ | 0.56 GB | 音频 VAE |
| `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors` | loras/ | 1.82 GB | **8 步 turbo LoRA，必挂** |

**Wan2.1 I2V 备用**：
| 文件 | 位置 | 大小 |
|---|---|---|
| `wan2.1-i2v-14b-480p-Q4_0.gguf` | diffusion_models/ | 9.54 GB |
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | text_encoders/ | 1.72 GB |
| `wan_2.1_vae.safetensors` | vae/ | 0.24 GB |

### 2.3 Ollama
- 版本 0.34.4
- 已装：`qwen2.5:7b` (4.7 GB)、`qwen2.5:14b` (9 GB)
- 模型不自动卸载，跑完用 `ollama stop qwen2.5:7b` 释放显存

### 2.4 Real-ESRGAN 超分
- 路径：`F:\upscale_work\realesrgan-ncnn-vulkan.exe`（2022 老版本，Vulkan 后端）
- 用法见目录下 `README_windows.md`
- 注意：这是 ncnn vulkan 版，会同时占 GPU，**不要和 ComfyUI 同时跑**

### 2.5 自定义 AI_OS 流水线
- `D:\AI_WORKSPACE\` —— 主工作区，有 `START_AI_OS.bat` / `STOP_AI_OS.bat`
- 工作流模板：`D:\AI_WORKSPACE\h3_template.json`（ComfyUI API 格式，9:16 竖屏 0.4MP，已引用全部 H3 模型 + turbo LoRA）
- 输出目录：`D:\AI_WORKSPACE\output\`（当前为空，批量任务先确认这里的子目录约定）
- `D:\AI-OS\` 是另一个早期项目，有 `video_pipeline.py`，按需再看

### 2.5.1 h3_template.json 节点地图（改参数看这里，不要瞎改连线）

这是 **I2V（图生视频）** 工作流，不是纯文生视频——必须有首帧图。

| 节点 ID | class_type | 作用 | 改什么 |
|---|---|---|---|
| `105:104` | MiniMaxH3ImageToVideo | 核心 | `inputs.prompt` = 提示词；`first_frame` 来自节点 114 |
| `114` | LoadImage | 首帧图 | `inputs.image` = 文件名（在 ComfyUI input/ 下） |
| `105:111` | PrimitiveFloat | 时长（秒） | `inputs.value`，小样用 5，正式 10–15 |
| `105:107` | ComfyMathExpression | 自动算帧数 | 不用动，公式对齐到 17 的倍数（H3 要求） |
| `105:15` | RandomNoise | 种子 | `inputs.noise_seed`，换一个 seed 出不同片 |
| `105:126` | PrimitiveBoolean | turbo LoRA 开关 | 默认 `true`，**小样保持 true（8 步快）** |
| `105:125` | PrimitiveInt | turbo 步数 | 默认 8，别加 |
| `105:124` | PrimitiveInt | 非 turbo 步数 | 20（关掉 turbo 才用） |
| `115` | ResolutionSelector | 分辨率 | 9:16 竖屏 0.4 MP，不要随便调高 |
| `92` | SaveVideo | 输出 | `inputs.filename_prefix`，按任务命名 |
| `105:91` | CreateVideo | 封装 | fps=24, bit_depth=8, sRGB，别动 |

**默认配置已经是最优小样配置**：turbo 8 步 + 9:16 0.4MP + 5 秒。改时长或分辨率前先跑一次小样。

### 2.6 其他
- ffmpeg 9.0.2（gyan full build）
- 第二个 `E:\ComfyUI_windows_portable_nvidia\` 目录为空，**不要用**

---

## 3. 16 GB 显存的能力边界（针对已装模型）

| 任务 | 本机可行性 | 关键约束 |
|---|---|---|
| Ollama qwen2.5:7b Q4 | 轻松 | 显存 ~5 GB |
| Ollama qwen2.5:14b Q4 | 可跑 | 显存 ~9 GB |
| **MiniMax H3 视频生成（int8 + turbo 8步）** | **可跑但吃紧** | 主模型 19.5 GB > 16 GB，必然 lowvram offload；加文本编码器 14.6 GB，**系统内存峰值会到 25 GB+**。跑之前必须把空闲内存清到 ≥20 GB |
| Wan2.1 I2V 14B Q4 GGUF 480p 5s | 可跑 | 显存 ~10 GB，系统内存 ~16 GB |
| SDXL / SD3.5 / Flux 出图 1024² | 轻松 | — |
| 超分（Real-ESRGAN） | 轻松 | 但会和 ComfyUI 抢 GPU，串行跑 |
| HunyuanVideo / Wan2.2 FP16 | **跑不动** | 模型本体 28 GB+，本机没有这些模型，不要下 |
| 4K 视频 / >10s 高分辨率长片 | **不要本机硬刚** | 小样先测，爆显存就报用户授权上云 |
| LoRA 微调 | 可跑但不要同时跑别的 | batch=1 |
| 训练 >7B LLM | **不要本机** | 显存+内存都不够 |

**显存不足时的降级顺序**：降分辨率 → 降 batch → GGUF/GGML 量化 → `--lowvram` 模型 offload → 转云。
**画质有变化时必须先出 1 张对照给用户确认，不要直接批量。**

---

## 4. 内存是真瓶颈，不是显存

32 GB 物理内存，桌面常驻吃 20 GB+，空闲只有 ~11 GB。跑 MiniMax H3 之前**必须关**（不是最小化）：
- Chrome 多余标签页 / ChatGPT 桌面端 / Coze 桌面端
- Steam、EA Desktop、抖音客户端、WeGame
- 微信、企业微信、WorkBuddy 多余实例

关完用 `inventory.ps1` 复核空闲内存到 **≥20 GB** 再启动 ComfyUI。
**不要把页面文件当物理内存**——视频生成会疯狂 swap，慢 10 倍。

---

## 5. 任务分配决策树

```
接到任务
  ↓
inventory.ps1 实测当前余量
  ↓
纯文本/对话？ ──是→ Ollama qwen2.5 本地
  ↓否
出图/改图？ ──是→ ComfyUI 本地（先看 models/ 里有没有对应 checkpoint）
  ↓否
图生视频/文生视频？
  ├─ 用 H3？ → 确认内存空闲 ≥20 GB，加载 h3_template.json，挂 turbo LoRA，9:16 0.4MP
  ├─ 用 Wan2.1 I2V？ → 480p 5s 小样先跑
  ↓
小样：1 个最短片段（H3：8步 turbo；Wan：5s 480p）
  ├─ 峰值显存 ≤ 14 GB 且稳定 → 本地批量
  ├─ OOM 或慢到不可接受 → 降级参数再试一次；仍不行 → 报用户，等授权上云
  ↓
需要长视频/4K/批量 >50 条？
  ↓
小样时间 × N 估算，告诉用户预计时长和机器占用，再启动
```

**不做的事**：
- ❌ 不因为有 Mac/iPhone/iPad 就硬做分布式（ARP 里看不到，软件也不支持合并显存）
- ❌ 不同时开 ComfyUI + Ollama + Real-ESRGAN 三个 GPU 任务
- ❌ 不因为"闲着也是闲着"就后台跑长任务——会占着内存让用户其他工作卡死
- ❌ 不擅自删模型、原始素材、工程文件来腾空间
- ❌ 不擅自下载新模型到 E 盘（E 盘只剩 219 GB，一个 H3 级模型就 20 GB，下之前先问用户）

---

## 5.5 常见错误处置（本机实测会碰到的）

| 现象 | 原因 | 处置 |
|---|---|---|
| `CUDA out of memory` / ComfyUI 崩 | 显存爆了 | 1) 关掉 turbo 以外的其他 GPU 任务（Ollama、Real-ESRGAN、Chrome 硬件加速）<br>2) 时长从 15s 降到 5s<br>3) 分辨率从 0.4 MP 降到 0.25 MP<br>4) 还爆就报用户，不要硬加 `--lowvram` 试到崩为止 |
| 生成速度极慢（>5 min/条），GPU 利用率 <30% | 系统内存 swap 了 | 关桌面应用，把空闲内存清到 ≥20 GB。H3 模型 19.5 GB 必须 offload 一部分到内存，内存不够就 swap |
| ComfyUI 启动卡 `loading model` 超过 5 min | 模型从 E 盘冷读 + 系统内存不够 | 第一次加载慢是正常的（~53 GB 模型），等。第二次会有系统缓存 |
| 出片全黑 / 全紫 / 花屏 | VAE 或模型版本错配 | 不要自己改 JSON，转交 `comfyui-workflow-validation` skill 排错 |
| 节点报红色 / 缺节点 | ComfyUI 版本 <0.37（H3 节点 0.37 才内置） | 升级 ComfyUI portable；不要手装 custom_nodes 凑节点 |
| `run-h3-sample.ps1` 报"missing model files" | 模型文件被移动/删除 | 按脚本列出的路径从磁盘找，不要重新下载 |
| `run-h3-sample.ps1` 报 ComfyUI not reachable | ComfyUI 没启动 | 先跑 `E:\ComfyUI_windows_portable\run_nvidia_gpu_fast_fp16_accumulation.bat`，等浏览器开 :8188 再跑脚本 |
| 磁盘写满 | 输出视频累积 | 清 `E:\ComfyUI_windows_portable\ComfyUI\output\` 里的旧片，不要删 models/ |

---

## 5.6 与其他 skill 的分工（不要越界）

- **comfyui-workflow-validation**：负责 ComfyUI 工作流 JSON 生成、节点缺失排错、模型-节点适配、自定义节点安装。**遇到工作流报错、节点红色、JSON 导出问题，转它**，不要在本 skill 里硬修节点。
- **jianying-cloud-ai-editing**：负责剪映里的智能剪辑（AI 切片、文字成片、智能包装、视频翻译）。**剪辑、加字幕、套特效走它；本地模型生成原始素材走本 skill**。
- **byted-mediakit-video / editing**：负责已有视频的转码、抽帧、切片、字幕压制等后处理。
- **本 skill 只管一件事**：决定这次任务在本机跑还是上云、跑之前资源够不够、小样要多久、跑完怎么收尾。

---

## 5.7 Windows PowerShell 5.1 兼容性坑（已踩过，别再踩）

本机 `powershell.exe` 是 **5.1.26100**，不是 PowerShell 7。写脚本时：

1. **不要用 `ConvertFrom-Json -AsHashtable`**——PS 5.1 没这个参数。直接用 `ConvertFrom-Json` 返回 PSCustomObject，节点 ID 带冒号用 `$wf.'105:104'` 访问（不要用 `$wf["105:104"]`，那是 hashtable 语法）。
2. **不要把多行 JSON 字符串通过 pipeline 传给函数**——PowerShell 会按行拆分，导致 `无效的 JSON 基元`。用 `ConvertFrom-Json -InputObject $raw` 显式传参。
3. **函数参数别命名 `$InputObject`**——会和 `ConvertFrom-Json -InputObject` 在函数作用域内产生诡异冲突。用 `$Json` 或别的名字。
4. **深拷贝工作流最简单的方式**：每次任务从磁盘重读 JSON 文件（文件才几 KB），不要 `ConvertTo-Json | ConvertFrom-Json` 绕一圈。
5. 所有脚本 dot-source 同目录 `lib.ps1`，公共函数（Read-Workflow / Submit-ComfyWorkflow / New-MultipartFileBody）只写一遍。
6. 改完脚本用 `-DryRun` 模式验证 JSON 构造对不对，不需要真起 ComfyUI。

---

## 6. 小样测量协议（批量前必做）

记录 5 个数，写进回复给用户看：

| 指标 | 怎么测 |
|---|---|
| 模型加载时间 | ComfyUI 启动到 H3 模型全部加载完（第一次最慢，之后缓存） |
| 单条生成时间 | 从 prompt 提交到出片（挂 turbo 8 步后的秒数） |
| 峰值显存 | 跑的时候另开 PowerShell `.\watch-vram.ps1` 盯峰值 |
| 峰值内存 | 同上，脚本会同时记录 WorkingSet |
| 输出质量 | 给用户看小样，等确认再批量 |

**只有近似线性的任务才能外推**（如 N 张图）。长视频、高分辨率、复杂场景时间通常超线性增长（2x 像素 ≈ 4x 时间），外推要给 ±50% 区间。

---

## 7. 云资源（默认不碰，除非用户明确授权）

用户没给预算授权时：**只做本机方案和估算，不创建任何云实例**。

### 7.1 本机 vs 云成本决策公式（不填具体价格，授权时再查当日价）

启动云实例前，必须把这两列并列算给用户看：

| 项 | 本机（RTX 5080 16G） | 云 GPU（A100 80G / 4090 24G 按需） |
|---|---|---|
| 单条 H3 5s 视频耗时 | 小样实测后填（秒） | 按厂商实例规格估算，标"约" |
| 批量 N 条总耗时 | 单条 × N（近似线性，±50%） | 同左 |
| 硬件成本 | 已购，不计入增量 | 时价 ×（总耗时 + 环境准备 20 min） |
| 环境准备 | 已装好，0 | 装驱动/ComfyUI/下 53GB 模型 ≈ 30–60 min 也在计费 |
| 存储/流量 | 0 | 数据盘 + 公网下载视频出网费 |
| 电费 | 功耗按 nvidia-smi power.draw × 时长 × 电价（约 0.6 元/度） | 0 |
| 机会成本 | 占用机器期间不能干别的 | 不占本机 |

**决策规则**：
- 本机小样跑通且单条 < 3 min → **本机**，不用云
- 本机小样跑通但要批量 > 100 条 / 要过夜 → 算本机电费 vs 云时价，通常本机仍便宜
- 本机小样 OOM（分辨率 >720p、时长 >15s、要 FP16 不要 int8）→ **才考虑云**
- 云实例选 **可中断（spot）** 前，必须确认 ComfyUI 任务能断点续跑；否则用按量付费

### 7.2 授权后必交的一页纸

用户点头后，开实例前先把这段贴出来：
- 任务：具体出什么、多少条、每条多长
- 实例：规格、区域、时价（查官网当日，标注日期）
- 预计时长：含环境准备和模型下载
- 预计总费用区间：低–高
- 超时保护：跑满 X 小时自动关机
- 收尾：关机后删数据盘和弹性公网 IP（停实例 ≠ 停计费）

**云端 ≠ 总成本低**：环境准备和模型下载的 30–60 分钟也在计费，批量小时任务云反而贵。

---

## 8. 收尾检查（任务跑完必做）

1. 核对输出文件数量、大小、能正常打开（`D:\AI_WORKSPACE\output\` 或 F 盘临时目录）
2. 关 ComfyUI（Ctrl+C 关窗口）；Ollama 用 `ollama stop <model>` 释放显存
3. 检查 F:\ 临时目录有没有大中间文件要清
4. 如果用了云：关机 + 删盘 + 删弹性公网 IP，**停实例不等于停计费**
5. 把本次实测耗时/显存写进本文件第 9 节基准表，下次预测更准

---

## 9. 任务基准记录（持续更新）

| 日期 | 任务 | 配置 | 小样实测 | 批量外推偏差 | 备注 |
|---|---|---|---|---|---|
| 2026-09-29 | 资源盘点基线 | RTX 5080 16G / 32G RAM | 显存空闲 14G，内存空闲 11G | — | 桌面常驻吃内存是常态 |
| 2026-09-29 | H3 工作流模板确认 | h3_template.json 9:16 0.4MP | 未跑小样 | — | 主模型 19.5G > 16G，必 lowvram；跑前内存需 ≥20G |
| 2026-09-29 | run-h3-sample.ps1 DryRun | PS5.1 + lib.ps1 | JSON 解析/字段修改/seed 生成 0.1s | — | 未真提交；等 ComfyUI 起后再测真实耗时 |
| 2026-09-29 | run-h3-batch.ps1 DryRun | 3 条 prompts 测试 | 3/3 OK，CSV 9 列正确生成 | — | 空行/注释正确过滤；未真提交 |
| 2026-09-29 | preflight 验证 | /object_info + 模型文件 | MiniMaxH3ImageToVideo 节点存在；5 个模型共 41.4GB 全在盘 | — | 未提交任务；确认 run-h3-sample.ps1 的 preflight 逻辑可过 |
| 2026-09-29 | inventory GO/NO-GO 实测 | ComfyUI 在跑但内存 10GB | 正确判 NO-GO：内存不够 | — | ComfyUI v0.37.0 在线，显存 13.2GB 空闲；提示关 Chrome/ChatGPT/Coze |

> 未经实测不要在这里写"XX 模型 X 秒出片"这类固定产能数字。
