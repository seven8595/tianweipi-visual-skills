# 本地 Flux / ComfyUI 实测经验（RTX 5080）

> 这些是真跑出来的参数，不是猜的。2026-10 验证。

## 环境
- ComfyUI便携版：`F:\ComfyUI_windows_portable\`
- 嵌入式Python：`F:\ComfyUI_windows_portable\python_embeded\python.exe`
- API端口：`127.0.0.1:8188`
- 启动：`Start-Process "F:\ComfyUI_windows_portable\run_nvidia_gpu.bat"`，约12秒就绪

## 模型
- 主模型：`flux1-dev.safetensors` (22.17GB, fp8加载)
- 文本编码器：`t5xxl_fp8_e4m3fn_scaled.safetensors` (4.8GB) + `clip_l.safetensors` (0.23GB)
- VAE：`ae.safetensors` (0.31GB)
- 超分：`4x-UltraSharp.pth`

## 实测参数（Flux dev）
| 参数 | 值 | 说明 |
|---|---|---|
| 采样器 | euler + simple | Flux dev标准 |
| Steps | 24 | 够用，30+无明显提升 |
| CFG | **1.0** | 关键！Flux dev是guidance-distilled，CFG>3会崩 |
| 出图速度 | ~40秒/张 | 1024×1344 |
| 显存占用 | ~22GB fp8加载 | 5080 16GB需fp8量化 |

## 已验证做不通的
- Flux dev不能用高CFG（3.0+崩图）
- 纯image_edit文字描述改材质力度弱，精准局部改必须用Inpaint+ControlNet
- ComfyUI缺ControlNet模型（MLSD/Lineart），线稿控制做不了
- 缺Architecture LoRA，纯Flux原生已够概念阶段
- Flux不擅长精确文字/编号/logo——后期PS排版

## 生图脚本
`F:\ai智能体田伟平总监水平自动工作流\local_pipeline\flux_generate.py`
```
python flux_generate.py --prompt "描述" --width 1024 --height 1344 --steps 24 --seed 7 --out output.png
```

## 输出目录
`F:\ai智能体田伟平总监水平自动工作流\local_pipeline\output\`

## 超分
用 `scripts/upscale_batch.ps1` 或Real-ESRGAN本地脚本。
