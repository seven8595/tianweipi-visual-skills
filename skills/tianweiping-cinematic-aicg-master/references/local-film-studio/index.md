---
name: local-ai-film-studio
description: "全本地算力AI电影制作工作室。从剧本、分镜、角色设定到ComfyUI本地渲染、upscale、剪辑输出的完整流水线。当用户要求用本地GPU制作AI视频/电影/短片、不使用云算力、赛博武侠/古风/科幻风格电影、批量生成镜头时使用。触发词：本地AI电影、全本地渲染、ComfyUI做视频、Wan2.1生成电影、赛博武侠短片、本地出片、不花钱做视频。"
---

# Local AI Film Studio — 全本地AI电影制作工作室

## 概述

用本地GPU（RTX 30/40/50系列）+ ComfyUI + Wan2.1 I2V，从零制作完整AI电影。不依赖任何云算力，所有生成在本地完成。

支持风格：赛博武侠、古风、科幻、末世、任何需要电影质感的AI视频项目。

## 核心约束

- **零云算力**：所有生成在本地GPU完成，不调用任何在线API
- **电影质感**：所有prompt必须包含反塑料感关键词（见 references/prompt_style.md）
- **角色一致性**：每个角色先做参考图，再用IP-Adapter/LoRA锁定
- **分镜驱动**：先出完整分镜表，再批量生成，不要边想边做

## 工作流（按顺序执行）

### Step 1: 环境检查与搭建
读取 `references/environment_setup.md`，确认：
- GPU型号和VRAM（16GB起步，推荐24GB；**32GB 直接走 FP8 路线**）
- ComfyUI是否已安装
- Wan2.1模型是否已下载（**32GB 优先 FP8 官方版，不要下 GGUF**）
- CUDA版本是否匹配GPU架构（Blackwell 50系需要cu128+）
- 加速节点是否装好（TeaCache/BlockSwap，见 `references/acceleration.md`）

### Step 2: 剧本与分镜
1. 写三幕结构剧本（时长、角色、场景）
2. 拆成5秒一个的镜头清单
3. 每个镜头配好：首帧prompt + 视频运镜prompt + 负面提示词
4. 参考 `references/prompt_style.md` 中的电影质感关键词

### Step 3: 角色与场景设定
1. 为每个主要角色写视觉设定prompt
2. 生成角色参考图（首帧图）
3. 场景环境图
4. 用IP-Adapter或LoRA锁定角色长相

### Step 4: 批量生成
1. 按分镜表逐镜头生成
2. 每个镜头流程：首帧图 → I2V生成5秒 → upscale到目标分辨率
3. 记录失败镜头，重新生成

### Step 5: 后期
1. 配音（本地TTS）
2. 配乐音效
3. 剪辑拼接
4. 调色输出

## VRAM适配表

| VRAM | 模型选择 | 生成分辨率 | 速度参考 |
|---|---|---|---|
| 8GB | Wan2.1 1.3B 或 GGUF Q3 | 480p | ~5min/段 |
| 12GB | Wan2.1 14B GGUF Q4 | 480p | ~8min/段 |
| 16GB | Wan2.1 14B GGUF Q4/Q5 | 480p | ~10min/段 |
| 24GB | Wan2.1 14B FP8 | 720p | ~15min/段 |
| **32GB（RTX 5080/5090）** | **Wan2.1 14B I2V FP8 原生** | **720p 原生（1280×720）** | **社区参考 4–8min/段，开加速节点可压到 2–3min/段** |

> **32GB 卡不要走 GGUF 路线**：显存够，直接上官方 FP8 版，画质优于 GGUF Q4/Q5。
> 上表 32GB 速度为社区公开测试区间，**本机首次跑必须用最短片段（49帧）实测校准**，不要照表估工期。加速方案见 `references/acceleration.md`。

## 关键参考文档

- **环境搭建** → `references/environment_setup.md`
- **电影质感prompt模板** → `references/prompt_style.md`
- **角色一致性方案** → `references/character_consistency.md`
- **批量生成管线** → `references/production_pipeline.md`
- **5080/32GB 加速手册** → `references/acceleration.md`

## 重要提醒

- 50分钟电影 = 约600个5秒片段 = 数百小时纯生成时间，提前告知用户工期（按本机实测速度重算，不要照抄下方旧表）
- 分辨率路线按 VRAM 分：16GB 卡走 480p 生成 → 4x upscale 到 1080p；**32GB 卡可直接 720p 原生生成 → 2x upscale 到 1440p/4K**，少一次 upscale 就少一代画质损失
- 国内下载HuggingFace模型慢，用hf-mirror.com镜像或ModelScope
- 每次生成前检查镜头prompt七要素：主体+场景+动作+镜头+光照+音频+约束
- **工期表是 16GB 基线的旧参考**；32GB/5080 首次跑完一个镜头后，用实测秒数 × 镜头数重新给用户报工期
