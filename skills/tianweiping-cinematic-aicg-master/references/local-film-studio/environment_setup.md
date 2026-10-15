# 环境搭建指南

## GPU兼容性

| GPU架构 | 代表型号 | PyTorch版本 | CUDA版本 |
|---|---|---|---|
| Ampere | 30系 | 2.x | cu118/cu121 |
| Ada | 40系 | 2.x | cu121/cu124 |
| Blackwell | 50系（含 RTX 5080/5090） | 2.7+ | cu128（必须！） |

> **Blackwell 50系注意**：必须用cu128版本的PyTorch，cu124及以下无法识别GPU。
> 安装命令：`pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128`

## 5080 / 32GB 用户必读（本项目主力配置）

- **不要下 GGUF 量化版**。32GB 显存直接跑 Comfy-Org 官方 repackaged 的 **FP8 版**（`*_fp8_scaled.safetensors`），原生 720p，画质明显好于 GGUF Q4/Q5。
- **ComfyUI 必须是较新版本**（2025 年以后的 release 或 nightly），旧版不支持 Blackwell 的 FP8 算子。先 `git pull` 再装依赖。
- 装完先用一段最短片段（49帧）冒烟测试，确认 `torch.cuda.is_available()` 返回 True、且不 OOM，再开始批量。
- 加速节点（TeaCache / BlockSwap）是 5080 上把单镜头从 5 分钟压到 2–3 分钟的关键，见 `acceleration.md`。

## 标准安装步骤

### 1. Python环境
- 用Python 3.10（不要用3.12+，很多依赖不兼容）
- 单独建venv，不要污染系统Python

### 2. ComfyUI
- 下载地址：https://github.com/comfyanonymous/ComfyUI
- 放到空间大的盘（模型文件动辄 50GB+，预留 ≥100GB）
- 安装自定义节点：
  - ComfyUI-GGUF（量化模型支持，≤16GB 才需要）
  - ComfyUI-WanVideoWrapper（Wan2.1视频支持）
  - 加速节点（TeaCache / BlockSwap），见 `acceleration.md`

### 3. 模型下载清单

#### 路线 A：32GB / 5080 推荐（FP8 原生）

| 模型 | 约大小 | 放置目录 |
|---|---|---|
| wan2.1_i2v_720p_14B_fp8_scaled.safetensors（或 480p FP8 版，按目标分辨率选） | ~17GB | models/diffusion_models/ |
| wan_2.1_vae.safetensors | ~500MB | models/vae/ |
| umt5_xxl-encoder（fp8 或原版均可） | ~9GB / ~3GB | models/clip/ |
| clip_vision_h.safetensors | ~1.5GB | models/clip_vision/ |
| 4x-UltraSharp.pth（或 2x 模型） | ~60MB | models/upscale_models/ |

> 具体文件名以 Comfy-Org 在 HuggingFace `Comfy-Org/Wan_2.1_ComfyUI_repackaged` 仓库当前 release 为准；国内走 hf-mirror 或 ModelScope 镜像。

#### 路线 B：≤16GB（GGUF 量化兜底）

| 模型 | 大小 | 放置目录 |
|---|---|---|
| wan2.1-i2v-14b-480p-Q4_K_M.gguf | ~9GB | models/unet/ |
| wan_2.1_vae.safetensors | ~500MB | models/vae/ |
| umt5-xxl-encoder-Q5_K_M.gguf | ~3GB | models/clip/ |
| clip_vision_h.safetensors | ~1.5GB | models/clip_vision/ |
| 4x-UltraSharp.pth | ~60MB | models/upscale_models/ |

### 4. 国内下载加速
- HuggingFace直连超时 → 用 `https://hf-mirror.com` 镜像
- 设置环境变量：`$env:HF_ENDPOINT = "https://hf-mirror.com"`
- 大文件用迅雷/IDM多线程下载，比Python库快
- ModelScope 也有 Wan2.1 镜像，搜 "Wan2.1" 即可

### 5. 启动命令（按显存选，路径换成你自己的）
```powershell
# 32GB / 5080：FP8 全量驻留显存
cd <你的ComfyUI目录>
venv\Scripts\Activate.ps1
python main.py --listen 127.0.0.1 --port 8188 --fast fp8 --windows-standalone-build

# 16GB 及以下：走 lowvram，模型按需换入换出
# python main.py --listen 127.0.0.1 --port 8188 --lowvram
```

> 不要把路径写死成 `F:\AI\ComfyUI`，先 `Get-PSDrive` 看哪个盘剩 ≥100GB，装那一个。

## 常见问题

**Q: CUDA available但跑模型报错？**
A: 检查GPU架构是否匹配PyTorch CUDA版本。50系必须cu128+。

**Q: 32GB 卡还 OOM？**
A: 先确认没同时开着别的吃显存的程序（浏览器硬件解码、游戏、另一个 ComfyUI 实例）。`nvidia-smi` 看占用。仍 OOM 就把生成分辨率从 720p 降到 480p，或开 BlockSwap。

**Q: 16GB VRAM跑OOM？**
A: 换更低量化级别（Q4→Q3），或加 `--lowvram` 参数。

**Q: 生成的视频有塑料感？**
A: 检查prompt是否加了电影质感关键词，见 prompt_style.md。

**Q: 5080 上生成比别人慢很多？**
A: 十有八九是没用 cu128 版 PyTorch，或没开加速节点。先 `python -c "import torch; print(torch.__version__, torch.version.cuda)"` 核对。
