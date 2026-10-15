# 本地渲染管线参数（RTX 5080 16GB 优化）

所有参数基于用户本机 **Windows RTX 5080**。目标：在不爆显存的前提下拿到接近 D5 / Corona 级别的写真感。

## 0. 本机环境配置（已探测，2026-10-07）

| 项 | 值 |
|---|---|
| OS | Windows 11 (NT 10.0.26300) |
| GPU | NVIDIA GeForce RTX 5080 (16GB) |
| ComfyUI 版本 | 0.38.0 |
| ComfyUI 路径 | `F:\AI\ComfyUI` |
| venv Python | `F:\AI\ComfyUI\venv\Scripts\python.exe` |
| 启动脚本 | `F:\AI\ComfyUI\start_comfyui.bat`（已改为 `--listen 0.0.0.0 --port 8188 --highvram`） |
| 输出目录 | `F:\AI\ComfyUI\output` |
| Tailscale IP | `100.77.54.21` |
| Tailscale 账号 | `weipingtian933@` |
| 本地 API | `http://127.0.0.1:8188` |
| Tailscale API（手机/Mac 用） | `http://100.77.54.21:8188` |

**其他 ComfyUI 实例**（备用）：
- `F:\ComfyUI_windows_portable\ComfyUI\`（便携版）
- `F:\h3_work\ComfyUI_windows_portable\ComfyUI\`（h3 工作版）

**已装依赖**：`gguf 0.19.0`、`accelerate 1.15.0`。

**启动 ComfyUI 命令**（PowerShell）：
```powershell
Start-Process -FilePath "F:\AI\ComfyUI\venv\Scripts\python.exe" `
  -ArgumentList "main.py --listen 0.0.0.0 --port 8188 --highvram" `
  -WorkingDirectory "F:\AI\ComfyUI" -WindowStyle Hidden
```

---

## 1. Checkpoint 选择优先级

| 场景 | 推荐模型 | 备注 |
|---|---|---|
| 建筑写真 / 招商图（首选） | **Flux.1-dev fp8** + 建筑 LoRA | 光线、玻璃反射、材质最真 |
| 快速出方案 / 草图 | **Juggernaut XL v9**（SDXL） | 速度快、人物自然 |
| 城市更新 / 旧改照片写实 | **Realistic Stock Photo XL** 或 **epiCRealismXL** | 真实感强 |
| 欧式 / 文旅 / 历史街区 | **RealVisXL V5.0** + 复古 LoRA | 色彩温润 |
| 赛博朋克 / 夜景霓虹 | **CyberRealistic Negative** 工作流 + Flux | 霓虹不糊 |

**VAE**：SDXL 用自带 VAE 即可；Flux 用 `ae.safetensors`（Flux 官方 VAE）。

## 2. 推荐 LoRA（建筑效果图向）

- `Architecture.safetensors`（Flux 版，权重 0.6–0.8）——强化建筑结构与透视。
- `Realistic Vision` / `Photo realism` LoRA（权重 0.4–0.6）——去 AI 味。
- `Warm Light` / `Golden Hour` LoRA（权重 0.3–0.5）——强化蓝调时刻暖光溢出。
- 慎用人物 LoRA：本图人物是背景，不是主角；强行加真人 LoRA 会让人抢戏。

## 3. 采样器与参数

### Flux.1-dev（推荐）
- Sampler：`euler` 或 `dpmpp_2m`
- Scheduler：`simple` / `beta`
- Steps：20–28
- CFG / Guidance：3.0–3.5（Flux 用 guidance，不是 CFG）
- Resolution：`1344×768` 原生 → 之后超分（5080 16GB 跑 1920×1080 fp8 也可以，但原生更稳）

### SDXL（Juggernaut / RealVis）
- Sampler：`DPM++ 2M Karras` 或 `DPM++ 3M SDE Karras`
- Steps：28–35
- CFG：5.5–7
- Resolution：`1536×864`（SDXL 最佳 bucket）→ 超分到 1920×1080

## 4. 分辨率与超分（重要）

不要直接生图拉到 4K。正确流程：

1. 原生生成：SDXL `1536×864` / Flux `1344×768`。
2. Hires fix 或单独超分节点：**Real-ESRGAN x4+** 或 **4x-UltraSharp**，2x 放大到 `3072×1728` / `2688×1536`。
3. 需要印刷 300 DPI A3 时：超分到 `4961×3508`（A3 横版 300DPI）。

5080 16GB 直接生 `2048×1152` 也 OK，但人物比例、招牌文字更容易崩——优先小图生 + 超分。

## 5. 工作流建议（ComfyUI）

最简链路：
```
Load Checkpoint → CLIP Text Encode (Positive) → CLIP Text Encode (Negative)
→ Empty Latent Image (1536×864)
→ KSampler → VAE Decode → Save Image
```

要提升质量加：
- **ControlNet**（建筑透视）：`controlnet-tile` 或 `controlnet-lineart` + 一张参考街景草图，锁住透视。
- **Regional Prompter**：左右建筑分区写不同 prompt，避免"两栋楼长得一样"。
- **Hires Fix**：默认 0.4–0.5 denoise。

## 6. 招牌文字处理

AI 生招牌文字几乎一定乱码。三种处理方式：
1. **Prompt 里让招牌虚化**：`blurred signage, out of focus store signs, illegible shop windows` —— 最快、最稳。
2. **生图后用 PS / ComfyUI 节点 inpaint 替换文字**。
3. **Flux.1 dev + 带文字能力的微调**（如 Flux-Text）—— 试验性，不建议用在交付图上。

默认用方式 1。

## 7. 显存急救

如果 OOM：
- Flux 切 fp8 量化（`flux1-dev-fp8.safetensors`）。
- SDXL 开 `--medvram` 或 ComfyUI 里开 `vae tiling`。
- 分辨率降到 `1024×576` 先出草图，满意后再超分。
- 关闭 ControlNet 高分辨率分支。

## 8. 出图后必做的人工检查

参考 SKILL.md 第 11 节 QA 清单。任何一项不过 → 改 prompt 重渲，不要硬交。
