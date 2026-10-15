# 本地 ComfyUI Flux 精修实操（16GB 显存，RTX 5080 验证）

> 2026-10-03 龙鳞宝贝倒立版实战沉淀。适用：既有 IP 姿势重绘、AI 图去味精修、高清化、风格统一。

## 0. 环境前提（先查再跑）

- ComfyUI ≥ 0.37，原生支持 Flux 节点
- 模型文件位置（以桌面便携版为例）：
  - `models/diffusion_models/flux1-dev.safetensors`
  - `models/text_encoders/clip_l.safetensors`
  - `models/text_encoders/t5xxl_fp8_e4m3fn_scaled.safetensors`
  - `models/vae/ae.safetensors`
- **坑**：flux1-dev 在 `diffusion_models/` 不在 `checkpoints/`，用 `CheckpointLoaderSimple` 会报 `ckpt_name not in []`。必须走 `UNETLoader`。

## 1. 两种任务模式

| 模式 | denoise | 用途 | 结构保留度 |
|---|---|---|---|
| **重绘/换姿势** | 0.55–0.65 | 给姿势参考图，换画风/换细节 | 保留大姿势，细节会重生成 |
| **精修/去味** | 0.25–0.30 | 已成品，只加手绘质感/提清晰度 | 几乎不动结构，只刷材质笔触 |

**选错代价**：精修时 denoise 0.6 → 角色身份特征漂移（胸口星丢、角形状变、手脚套变）。重绘时 denoise 0.3 → 改不动任何东西，白跑。

## 2. 节点组（直接套）

```
1  UNETLoader          unet_name=flux1-dev.safetensors  weight_dtype=fp8_e4m3fn
2  DualCLIPLoader      clip_name1=clip_l.safetensors   clip_name2=t5xxl_fp8_e4m3fn_scaled.safetensors   type=flux
3  VAELoader           vae_name=ae.safetensors
4  LoadImage           image=<你的输入图>
5  VAEEncode           pixels=[4,0]   vae=[3,0]
6  CLIPTextEncode      text=<positive>   clip=[2,0]
7  FluxGuidance        conditioning=[6,0]   guidance=3.0–3.5
8  CLIPTextEncode      text=<negative>   clip=[2,0]
9  KSampler            model=[1,0]   seed=<固定>   steps=22–25   cfg=1.0
                       sampler=euler   scheduler=simple
                       positive=[7,0]   negative=[8,0]
                       latent_image=[5,0]   denoise=<见上表>
10 VAEDecode           samples=[9,0]   vae=[3,0]
11 SaveImage           images=[10,0]   filename_prefix=<项目名>
```

**Flux 铁律**：`cfg=1.0`，`sampler=euler`，`scheduler=simple`。guidance 用 `FluxGuidance` 节点单独控，不要塞在 CLIPTextEncode 里。

## 3. 分辨率

- 输入图先 resize 到 **64 的倍数**，3:4 竖版用 `1472×1984`，1:1 用 `1024×1024`，16:9 用 `1920×1088`
- 16GB 显存跑 1472×1984 + fp8 量化没问题（约 3–5 分钟出一张）
- 最终要客户尺寸（如 1773×2364）：先在 1472×1984 精修，再用 `System.Drawing` 高质量 bicubic 放大（见 §6）

## 4. Prompt 写法（按 本 skill 风格词典规则）

### 重绘模式 positive 骨架
```
same cute fluffy orange baby dragon mascot, <本次姿势描述>,
<TWO CURVED SPIRAL rainbow horns with stripes>, <彩虹手套/靴子>,
<GLOWING WARM GOLDEN STAR ON CHEST>,
thick shaggy orange fur, visible impasto oil painting brush strokes,
thick paint texture, warm solid golden yellow background,
childrens picture book illustration, centered
```

### 精修模式 positive 骨架
```
identical image, exact same composition, exact same pose, exact same character,
NO changes to any detail,
masterful hand-painted oil illustration, thick impasto brushstrokes visible on canvas,
professional childrens book illustrator artwork, detailed individual fur strands,
rich layered paint texture, visible canvas weave, hand-drawn artistic quality
```

### negative 骨架
```
AI generated, smooth plastic look, 3d render, cgi, vector,
changed pose, extra elements, deformed, extra limbs,
text, watermark, blurry, low quality
```

**规则**：
- IP 核心识别点（胸口星、彩虹条纹、披风）用全大写强调
- 要去掉的错误细节（蓝紫地面、蓝色侧角、露趾）写进 negative
- 不写艺术家名字，只写视觉参数（impasto/canvas weave/fur strands）

## 5. 提交与轮询（PowerShell）

```powershell
$body = @{ prompt = $workflowDict } | ConvertTo-Json -Depth 10
$resp = Invoke-RestMethod -Uri "http://127.0.0.1:8188/prompt" -Method Post -Body $body -ContentType "application/json"
# $resp.prompt_id 轮询 http://127.0.0.1:8188/history/<prompt_id>
```

输入图必须先放进 ComfyUI 的 `input/` 目录，`LoadImage` 节点才能看到。

## 6. 后处理：放大到客户尺寸

```powershell
Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile($src)
$bmp = New-Object System.Drawing.Bitmap($nw, $nh)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
$g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
$g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
$g.DrawImage($img, 0, 0, $nw, $nh)
$bmp.Save($dst, [System.Drawing.Imaging.ImageFormat]::Png)
```

1.2× 以内放大质量损失可接受；超过 1.5× 应考虑加 ESRGAN upscale 模型。

## 7. 常见坑

| 症状 | 原因 | 解法 |
|---|---|---|
| `ckpt_name not in []` | flux 在 diffusion_models 不是 checkpoints | 换 UNETLoader |
| 胸口星/角形状漂移 | denoise 太高 | 降到 0.28 精修，或 prompt 全大写强调识别点 |
| OOM | 分辨率太大或没开 fp8 | UNETLoader 选 fp8_e4m3fn；降到 1024×1365 |
| 脚下出现蓝紫污渍 | prompt 没排除 | negative 加 `purple stains on floor, blue ground` |
| 角色变成 3D 皮克斯感 | guidance 太高或风格词不够 | guidance 降到 2.5，positive 加 `impasto oil painting, canvas texture` |

## 8. 交付前对照清单

- [ ] 角色身份锚点全在（胸口星/角/披风/手脚套颜色数量）
- [ ] 姿势和用户参考图一致
- [ ] 没有 AI 塑料感、全局平滑、随机装饰
- [ ] 分辨率达到客户要求（300 DPI / 指定像素）
- [ ] 文件放在项目 `output/`，文件名含版本号
