# 本地执行与核验

核查日期：2026-10-13。使用现有工具，不因旧路径或历史报告就认为当前仍可用。

## 本机本次状态

- Python：F:/AI/Python310/python.exe可以执行标准库辅助器；Pillow已可导入，用于本次参考/预览检查。
- FFmpeg6.1.1、FFprobe4.0.2已实际运行。路径见本地验证记录；旧FFprobe部分字段选择器不支持，现有探测器采用兼容读取。
- ComfyUI：127.0.0.1:8188实际返回RTX5080，提交前队列为空。8190本次无法连接，不采用旧技能中的E盘入口做保证。
- 原ComfyUI位于F:/AI/ComfyUI，已配置F:/ComfyUI_windows_portable/ComfyUI模型路径。没有改它的代码、启动参数或其他项目工作流。
- 本次模型枚举核验到flux1-dev、clip_l、t5xxl_fp8、ae及所需原生节点；实际加载与图像结果另见request.json。没有安装新模型/节点。
- 没有找到可用Blender命令或bpy，本次OBJ导出由标准库实现；不称已部署Blender。ASR/视频转绘及完整动画生成未在本轮测试。

## 生图入口

在skill目录使用自己的、已核验的API格式工作流：

```powershell
python .\scripts\run_local_image.py .\assets\comfy-smoke-test.json
python .\scripts\run_local_image.py .\assets\comfy-smoke-test.json --submit --output '新的本次输出目录' --wait 240
```

默认只预检。submit表示执行一次本地请求；服务有其他排队工作时不提交。接口限定本机HTTP根地址，禁代理和重定向；不调用外网生成或自动下载。

工作流需为API prompt图，不是GUI编辑格式。辅助器支持明确列出的原生本地节点，检查当前节点与枚举值；不接入任意自定义节点或外部API节点。预检不能代替服务自己的强校验和实际运行。

记录prompt_id以后，不因等待超时再提交。继续等待已有请求：

```powershell
python .\scripts\run_local_image.py .\assets\comfy-smoke-test.json --resume '原输出目录\request.json' --wait 240
```

成功下载图片时状态为media_created_pending_review，仍需看图、核对实际尺寸与设计目标。恢复时可复用字节相同的已有结果，拒绝覆盖不同文件。只跟踪本次ID，不取消其他任务或卸载用户正在使用的模型。

comfy-smoke-test是512×512、4步、batch1的小规模可用性测试，不能直接作为高质量商业参数或符合附件空间的设计稿。后续创作按真实模型、显存、参考控制与检查结果选择配置。

## 层级区分

技能文件已安装 ≠ 生成模型已部署；预检成功 ≠ 生图完成；图片存在 ≠ 设计通过；静帧与元数据 ≠ 视频与声音通过。模型来源、项目使用条件和字体/音乐资料按真实任务核验，本轮未给商业许可结论。
