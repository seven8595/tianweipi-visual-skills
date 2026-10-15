> 来源：原 archviz-promo-studio

# Archviz Promo Studio — 建筑宣传片工作室

把一张建筑效果图变成一支30秒-3分钟的电影感宣传片。全流程本地算力（RTX 5080 + ComfyUI + Wan2.1 I2V），零云API。

## 核心工作流

```
建筑概念 brief → 关键帧效果图（Flux dev）→ 分镜脚本 → 逐镜头I2V（Wan2.1）→ 配音配乐 → 剪辑成片
```

## 1. 概念阶段（出片前必须想清）

| 项目 | 要回答的问题 |
|---|---|
| 片长 | 30秒招商快剪 / 2分钟方案汇报 / 5分钟宣传片 |
| 受众 | 政府汇报 / 甲方决策 / 购房者 / 招商客户 |
| 调性 | 高端克制 / 温暖生活 / 科技未来 / 文化底蕴 |
| 核心主张 | 一句话：这支片要让观众记住什么？ |
| 输出画幅 | 横版16:9（汇报/招商）/ 竖版9:16（抖音/朋友圈） |

**禁止**：没想清楚就出图。没有主张的宣传片就是PPT轮播。

## 2. 分镜脚本模板

一支标准2分钟建筑宣传片 = 8-12个镜头，每个镜头3-5秒。

| 镜号 | 景别 | 运镜 | 内容 | 时长 | 情绪 |
|---|---|---|---|---|---|
| 01 | 远景 | 缓慢推进/拉升 | 城市天际线/项目位置 | 4s | 宏大开场 |
| 02 | 鸟瞰 | 俯瞰缓移 | 项目全貌/总平面 | 4s | 空间格局 |
| 03 | 中景 | 推轨/横移 | 沿街商业/主入口 | 4s | 第一印象 |
| 04 | 近景 | 推近 | 建筑细节/材质/灯光 | 3s | 品质感 |
| 05 | 人视 | 跟随/穿越 | 人物走在广场/入户 | 4s | 生活感 |
| 06 | 室内 | 横移/摇 | 大堂/中庭/配套 | 4s | 配套展示 |
| 07 | 特写 | 固定/微移 | 材质/光影/细节 | 3s | 精致度 |
| 08 | 黄昏/夜景 | 缓拉 | 蓝调时刻/灯光亮起 | 5s | 氛围高潮 |
| 09 | 远景 | 拉升/后移 | 项目融入城市 | 4s | 收尾升华 |

**节奏**：开场慢→中段稳→高潮（夜景）→收尾慢。不要全程一个节奏。

## 3. 运镜提示词（直接喂Wan2.1 I2V）

**原则**：首帧图锁画面，prompt只写动作和运镜，不写画面内容。

### 标准运镜库

| 运镜 | Prompt（英文） | 适用 |
|---|---|---|
| 缓慢推进 | `Camera slowly pushes in toward the building, gentle forward dolly, smooth motion` | 开场、特写 |
| 缓拉远 | `Camera slowly pulls back revealing the full scene, smooth dolly out` | 收尾、全貌 |
| 横移 | `Camera tracks laterally from left to right, smooth sideways motion` | 沿街立面 |
| 拉升 | `Camera crane rises upward revealing the city skyline, smooth upward movement` | 鸟瞰开场 |
| 俯角缓移 | `High angle aerial view, camera slowly glides over the rooftop, gentle forward motion` | 鸟瞰镜头 |
| 跟随人视 | `Camera follows a person walking through the plaza, steady handheld, natural walking pace` | 生活场景 |
| 穿越/推进 | `Camera dollies forward through the glass entrance into the lobby, smooth continuous motion` | 室内过渡 |
| 环绕 | `Camera slowly orbits around the building corner, gentle arc motion` | 建筑转角 |
| 微移固定 | `Subtle handheld camera, very slight movement, atmospheric` | 特写、细节 |

### 禁忌（会崩）

- 不写 `glow / reflection / flicker / light particles`（i2v会加多余特效）
- 不写快速运动/急推急拉（Wan2.1会糊）
- 不写多人复杂动作（肢体崩坏）
- 首帧图必须是静态关键帧，不是视频帧

## 4. 本地技术参数

### 关键帧效果图（Flux dev fp8）
- 分辨率：1216×832（横版）或 832×1216（竖版）
- Sampler：euler, simple, 24 steps, cfg=1.0, guidance=3.5
- 风格关键词：`architectural photography, blue hour, cinematic, photorealistic, David Chipperfield restrained luxury, 28mm, two-point perspective`

### I2V视频（Wan2.1 14B FP8）
- 分辨率：1280×720 原生（5080 32GB直跑）
- 时长：每段3-5秒
- 首帧：用Flux生成的关键帧
- 加速：TeaCache/BlockSwap节点压到2-3分钟/段
- 显存：32GB（5080）

### 后期
- 剪辑：剪映/DaVinci Resolve
- 配音：本地edge-tts或人工录音
- 配乐：版权免费BGM（Blue Hour氛围）
- 字幕：项目名+slogan，微软雅黑

## 5. 项目类型速查

| 类型 | 关键镜头 | 调性 |
|---|---|---|
| 养老社区 | 老人在花园、餐厅吃饭、康复中心、子女探望 | 温暖、安心、绿意 |
| 商业综合体 | 沿街人流、橱窗灯光、夜景、水景反射 | 高端、活力、蓝调 |
| 住宅楼盘 | 鸟瞰总平、入户大堂、阳台景观、黄昏灯光 | 宜居、品质、归属感 |
| 政府公建 | 正面全景、仪式感轴线、材质特写 | 庄重、大气、对称 |

## 6. 交付检查

- [ ] 每段视频和首帧关键帧角色/建筑一致
- [ ] 运镜方向和空间逻辑一致（不要忽左忽右）
- [ ] 蓝调时刻镜头天空颜色统一
- [ ] 没有乱码招牌（后期PIL叠）
- [ ] 节奏有快慢，不是匀速轮播
- [ ] 最后一镜有项目名+slogan
