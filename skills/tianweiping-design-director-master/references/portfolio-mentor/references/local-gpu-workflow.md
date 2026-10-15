# 本机 GPU 工作流（Windows + RTX 5080）

## 环境已验证（2026-09-29）

| 项 | 值 |
|---|---|
| GPU | RTX 5080, 16GB, 空闲约 14GB |
| 驱动 | 616.64 |
| ComfyUI 便携版 | `C:\Users\seven\Desktop\ComfyUI_windows_portable\` |
| ComfyUI 自带 Python | `python_embeded\python.exe`（3.13.14, torch 2.13+cu130, CUDA 可用） |
| ComfyUI 模型状态 | **空**（checkpoints/loras/upscale 全是 placeholder） |
| 系统 Python | 沙箱自带 3.14，无 torch |
| 已装创作软件 | Photoshop, Huion 数位板, 剪映 |
| 盘空间 | C: 224GB, D: 161GB, E: 219GB, **F: 832GB**（大文件放 F） |

## 已跑通：超分（Real-ESRGAN ncnn-vulkan）

**为什么用 ncnn 而不是 ComfyUI**：ComfyUI 没下 checkpoint，启动也生不了图；ncnn 独立 exe 不依赖 ComfyUI，Vulkan 后端直接吃 GPU。

**流程**：
1. 下载 `realesrgan-ncnn-vulkan-20220424-windows.zip`（43MB）
   - GitHub 直连超时（青岛网络）
   - **镜像可用**：`https://ghfast.top/https://github.com/...`
2. 解压到 `F:\upscale_work\`
3. 跑 `.\realesrgan-ncnn-vulkan.exe -i in.png -o out.png -n realesrgan-x4plus -s 4`
4. 用 ComfyUI 自带 Python 的 PIL 把 4x 结果（如 7092×9456）Lanczos 缩回目标尺寸（如 3600×4800），写 300DPI

**已固化脚本**：`scripts/upscale_batch.ps1`
```powershell
.\scripts\upscale_batch.ps1 -InputDir "C:\...\imgs" -OutputDir "F:\out" -TargetWidth 3600 -TargetHeight 4800 -DPI 300
```
首次运行自动从镜像下载 Real-ESRGAN。

## 待办：ComfyUI 本地生图

要本地生图（不耗云端 image_gen）需要下至少一个 checkpoint。5080 16GB 能跑：
- SDXL 1.0 (~6.5GB)：通用
- Flux.1-dev (~12GB)：质量高但要 fp8 量化才不爆显存
- 现有角色 LoRA：龙狸宝贝这种 IP 没有现成 LoRA，得自己训

**下模型前必须问用户**：
- 用哪个基础模型（SDXL 还是 Flux）
- 放哪个盘（建议 F:\ComfyUI_models）
- 下多大的版本

不要擅自下 12GB 模型。

## 网络经验

- GitHub 直连在青岛网络环境经常超时
- ghfast.top 镜像可用，速度 ~13MB/s
- HuggingFace 直连也常超时，用 `hf-mirror.com`
- 不要反复重试直连，30 秒不响应就换镜像

## 不要做的事

- 不要在 C 盘放大模型（C 盘虽然有 224GB，但 ComfyUI 本体在 C，模型也下 C 会越积越多）
- 不要用系统 Python 跑 torch（沙箱版没装）
- 不要启动 ComfyUI server 来跑超分（没必要，ncnn 更快）
- 不要把超分当成结构修复（画风不对、角色画错、文字乱码，超分只会把错误放大）
