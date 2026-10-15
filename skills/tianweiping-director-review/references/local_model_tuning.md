# 本地模型调参指南 v2（RTX 5080 16GB）

两档工作流：**快速草图档**（10 版选构图）+ **精修交付档**（出最终图）。

## 0. 两档流程（v2 核心）

```
Step 1  快速草图档：Hyper-SDXL / LCM，5 秒一版，出 10 张选构图
Step 2  锁构图：用选中的草图做 ControlNet / img2img
Step 3  精修交付档：Flux.1-dev fp8 或 Juggernaut XL，跑最终质量
Step 4  超分：Real-ESRGAN 到 4K
Step 5  总监审核：过 12 维 checklist + fatal_mistakes 图鉴
```

不要在草图档追求质量，也不要在精修档反复换构图——分开做。

---

## 1. 模型选择矩阵

| 场景 | 首选 | 备选 |
|---|---|---|
| 建筑 / 空间 / 商业街 | **Flux.1-dev fp8** | SDXL + Architecture LoRA |
| 平面海报 / KV / 品牌 | **Flux.1-dev fp8** | Juggernaut XL |
| 时尚 / 人物 / 产品写真 | **RealVisXL V5.0** | Juggernaut XL v9 |
| 赛博 / 夜景 / 强风格 | **Flux.1-dev fp8** + 风格 LoRA | CyberRealistic |
| 国风 / 水墨 / 东方 | **SDXL + Guofeng LoRA** | Flux + Chinese ink LoRA |
| **快速草图（新增）** | **Hyper-SDXL 1-2 steps** | LCM-LoRA + SDXL |

**VAE**：
- Flux 必须配 `ae.safetensors`
- SDXL 用自带，色彩偏暖时换 `sdxl_vae.safetensors`

---

## 2. 快速草图档（v2 新增，强烈推荐）

目的：5 秒出一张，10 张选构图。不要在这里调质感。

### Hyper-SDXL 1-2 steps
- 基于 SDXL，蒸馏到 1–4 步
- Sampler：`euler`
- Steps：**4–8**
- CFG：1.0–2.0
- 分辨率：1024×576（16:9）
- 用途：试构图、试调性、试人物位置

### LCM-LoRA + SDXL
- LCM-LoRA 权重 0.8
- Steps：4–6
- CFG：1.5–2.0
- 用途：同上，兼容老 SDXL 底模

**关键**：草图档跑完选定一张，再用 img2img（denoise 0.5–0.6）+ Flux 精修。

---

## 3. 精修交付档

### Flux.1-dev（推荐）
- Sampler：`euler` 或 `dpmpp_2m`
- Scheduler：`simple` / `beta`
- Steps：**24–28**（超过 32 提升有限）
- Guidance：**3.0–3.8**（<2.5 崩，>4.5 过饱和）
- 分辨率：`1344×768` / `1536×864`

### SDXL
- Sampler：`DPM++ 2M Karras` 或 `DPM++ 3M SDE Karras`
- Steps：**30–35**
- CFG：**5.5–7**
- Hires fix：0.4–0.5 denoise

---

## 4. 分辨率与超分（关键）

**错误做法**：直接生 4K → 爆显存 / 出伪影 / 人物变形 / 文字乱码。

**正确流程**：
1. 原生出图：Flux `1344×768`；SDXL `1024×576` / `1344×768`
2. Hires fix 或 Real-ESRGAN：
   - `4x-UltraSharp`（写实）
   - `RealESRGAN_x4plus`（通用）
   - `RealESRGAN_x2plus`（温和）
3. 最终到 3840×2160 / 4096×2304

5080 16GB 跑 Flux fp8 原生 `1920×1080` 也可以，但人物 / 文字更容易崩——优先小图生 + 超分。

---

## 5. LoRA 推荐

| 场景 | LoRA | 权重 |
|---|---|---|
| 建筑写真 | `Architecture.safetensors`（Flux 版） | 0.6–0.8 |
| 写实感 | `Photo realism` / `Realistic` | 0.4–0.6 |
| 暖光 | `Warm Light` / `Golden Hour` | 0.3–0.5 |
| 海报 / 排版 | `Poster Design` / `Typography` | 0.5–0.7 |
| 国风 | `Guofeng` / `Chinese ink` | 0.6–0.8 |
| 时尚 | `Fashion Photography` | 0.5–0.7 |

**禁忌**：一张图叠 3 个以上 LoRA，会互相打架。

---

## 6. ControlNet（锁质量的关键）

- **建筑 / 空间**：`controlnet-tile`（锁构图）、`lineart`（锁透视）、`mlsd`（锁建筑线）
- **海报 / KV**：`layout`（区域提示）、`segment`（分区写 prompt）
- **人物**：`openpose`（锁姿势）、`depth`（锁空间）
- **Depth Anything** 模型对建筑空间锁定特别有效

---

## 7. 显存急救（OOM 时）

1. Flux 切 fp8 量化（`flux1-dev-fp8.safetensors`）
2. SDXL 加 `--medvram` 启动参数
3. ComfyUI 开 `vae tiling`
4. 分辨率降到 `1024×576` 先出草图
5. 关掉 ControlNet 高分分支
6. 关 Chrome 硬件加速（吃显存）

---

## 8. 出图后必查（总监视角）

参考 SKILL.md 第 3 节 12 维 checklist + `fatal_mistakes.md` 图鉴。任何一项 ❌ 就重渲，不硬交。
