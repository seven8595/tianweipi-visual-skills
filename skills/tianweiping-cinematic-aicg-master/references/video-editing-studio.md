---
name: video-editing-studio
description: 专业视频剪辑全流程能力。从素材整理、粗剪、精剪、调色、音效、字幕到导出成片。支持横屏/竖屏、短视频/长视频、Vlog/短剧/动画/广告。触发词：剪辑视频、剪视频、视频后期、粗剪精剪、调色、加字幕、加音乐、导出成片。
---

# 视频剪辑工作室

## 1. 工作流程

```
素材整理 → 粗剪 → 精剪 → 调色 → 音效配乐 → 字幕 → 导出
```

| 阶段 | 动作 | 工具 |
|---|---|---|
| 素材整理 | 分类、筛选、命名、转码 | 资源管理器 / ffmpeg |
| 粗剪 | 去掉废片、拼顺序、定节奏 | 剪映 / PR / ffmpeg |
| 精剪 | 切点、转场、变速、关键帧 | 剪映 / PR |
| 调色 | 一级校色、风格LUT、局部调整 | 剪映 / DaVinci |
| 音效 | 配乐、音效、人声、混音 | 剪映 / Audition |
| 字幕 | 自动识别、校对、样式 | 剪映 |
| 导出 | 分辨率、码率、格式、平台适配 | 剪映 / PR |

## 2. 常用参数

| 平台 | 分辨率 | 帧率 | 码率 | 格式 |
|---|---|---|---|---|
| 抖音/快手竖屏 | 1080×1920 | 30fps | 8-12Mbps | MP4 H.264 |
| B站/YouTube横屏 | 1920×1080 | 30/60fps | 10-20Mbps | MP4 H.264 |
| 小红书竖版 | 1080×1440 | 30fps | 8-10Mbps | MP4 H.264 |
| 电影感 | 4K 3840×2160 | 24fps | 50Mbps+ | ProRes / H.265 |

## 3. 剪辑节奏原则

- **前3秒定生死**：短视频开头必须有钩子（动作/悬念/冲突）
- **节奏跟着情绪走**：快节奏用短镜头（0.5-1秒），慢节奏用长镜头（2-5秒）
- **J-cut/L-cut**：音频先入画面后入，或画面先出声音后出，减少硬切
- **B-roll覆盖**：口播视频必须配画面素材，不能全程怼脸
- **音乐卡点**：鼓点切镜头，情绪高潮给特写

## 4. 转场使用规则

| 转场 | 适用场景 | 禁忌 |
|---|---|---|
| 硬切 | 90%日常剪辑 | 不用花里胡哨的转场 |
| 溶解 | 时间流逝、回忆 | 别用太多 |
| 推拉/缩放 | 强调重点 | 别滥用 |
| 遮挡转场 | 物体经过镜头 | 需提前拍素材 |
| 音效转场 | 匹配音效切画面 | 需要音效素材 |

## 5. ffmpeg常用命令

```bash
# 截取片段
ffmpeg -i input.mp4 -ss 00:01:00 -to 00:02:00 -c copy output.mp4

# 拼接视频
ffmpeg -f concat -safe 0 -i list.txt -c copy output.mp4

# 转码压缩
ffmpeg -i input.mov -c:v libx264 -crf 18 -preset slow output.mp4

# 提取音频
ffmpeg -i input.mp4 -vn -acodec mp3 output.mp3

# 加字幕
ffmpeg -i input.mp4 -vf subtitles=sub.srt output.mp4

# 加速2倍
ffmpeg -i input.mp4 -filter:v "setpts=0.5*PTS" output.mp4

# 竖屏转横屏（模糊背景）
ffmpeg -i input.mp4 -vf "split[original][copy];[copy]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,gblur=sigma=20[blurred];[original]scale=1920:1080[original];[blurred][original]overlay=(W-w)/2:(H-h)/2" output.mp4
```

## 6. 剪映快捷键

| 快捷键 | 功能 |
|---|---|
| Ctrl+B | 分割片段 |
| Delete | 删除选中 |
| Ctrl+Z | 撤销 |
| 空格 | 播放/暂停 |
| 滚轮 | 时间线缩放 |
| I / O | 标记入点/出点 |

## 7. 交付检查清单

- [ ] 开头3秒有钩子
- [ ] 节奏不拖沓
- [ ] 音画同步
- [ ] 字幕无错别字
- [ ] 音量统一（人声-6dB，配乐-20dB）
- [ ] 导出分辨率码率正确
- [ ] 成片总时长符合要求
