---
name: seven-ai-os
description: Seven AI Core Intelligence OS v1.0.0 —— 个人 AI 认知架构。外置增强，不改模型本体。ChatGPT=总导演/研究/QA，豆包=执行型创意智能体，RTX 5080+ComfyUI=生产引擎，三者共享知识/记忆/经验/审美库。当用户提到"Seven AI / 七仔大脑 / 核心 OS / 用 Seven AI 跑 / 出图前先过 RAG / 查经验库 / 写经验卡 / QA 打分 / 重建索引 / 审美 DNA / World Model / LOCK 锁定 / 反方 Agent / Council / 多假设 / 缺失信息 / 元认知 / Creator Critic / 硬门禁 / Veto / SMART REPAIR / 审批 / benchmark / 回滚"，或要求按认知闭环执行任何出图/视频/调研/设计任务时使用。
---

# Seven AI Core Intelligence OS v1.0.0

外置增强，不改模型本体权重。代码在 Windows `D:\SevenAI\`，本机（Linux 云）作为总控/研究节点调用。

## 认知闭环

```
PERCEIVE → WORLD MODEL → RETRIEVE → HYPOTHESIZE → RESEARCH
       → SIMULATE → DEBATE → PLAN → EXECUTE → OBSERVE
       → CRITIQUE → REPAIR → CONSOLIDATE
```

## 11 个模块

| 模块 | 职责 |
|---|---|
| master | 任务契约、协作、状态、最终交付 |
| core_intelligence | 多模态证据、世界模型、知识图谱、RAG |
| archviz | 商业街/建筑空间真实性、尺度、视角、锁定 |
| tool_router | 工具/模型能力、质量、资源、成本、备用路线 |
| qa | Creator/Critic、硬门禁、Veto、SMART REPAIR |
| memory | 长期项目记忆、经验库、失败数据库 |
| device_orchestration | Windows 5080 + Mac + iPad 调度 |
| research | 可追溯资料、冲突核验、研究简报 |
| image_director | 图像创作、角色一致性、mask、定点修改 |
| video_director | 分镜、时间线、制作、声音字幕、视频验收 |
| project_manager | 项目依赖、预算、责任人、版本、交付 |

## 8 个结构化契约

task / asset / qa / memory-entry / device-job / approval / benchmark-run / runtime-config

## 硬规则

1. **禁止直接吐 prompt。** 先 RAG + Memory + Aesthetic DNA 召回，再写 prompt。
2. **Creator/Critic 分离。** Creator 创造，Critic 攻击弱点，Final Director 裁决。
3. **硬门禁失败阻止通过。** QA <70 reject，70-84 repair，85+ final，92+ portfolio。
4. **不合格不交付。** repair 后重新 QA，不把 repair 当 final。
5. **每次任务结束写 Experience Card。** 成功/失败/下次改进。
6. **本地优先。** ComfyUI/Ollama 优先，云端只留给强模型步骤。
7. **未核验就是未知。** 不编造完成的渲染、连接的设备、安装的模型、测试结果或 QA 分。
8. **审批绑定具体动作。** 候选更新后不能沿用旧版审批。

## 三机分工

| 设备 | 角色 | 端点 |
|---|---|---|
| Windows RTX 5080 | Render Node | ComfyUI http://192.168.5.8:8188, Render Node http://192.168.5.8:8770 |
| MacBook | 总控 | Master Agent、RAG、项目管理 |
| iPad | Creative Console | 批注、草图、Mask、选片 |

## V3 18 条协议

Meta Reasoning / Uncertainty / Multi-Agent Review / Devil's Advocate / Simulation / Dynamic Tool Routing / Model Routing / Best-of-N / Causal Memory / Failure Intelligence / Prediction / Benchmark / Version Control / Resource Awareness / Permission Control / Human Review / Context Management / Learning Loop

## V4 新增

World Model（LOCK/EDIT/REMOVE/ADD）/ Active Perception（CRITICAL/IMPORTANT/OPTIONAL）/ Hypothesis Engine / Evidence System / Creator-Critic Separation / Memory Hierarchy / Skill Evolution

## 已验证状态（2026-10-08）

- ComfyUI 0.38.0 在 RTX 5080 跑通，Flux.1 dev fp8，24 秒/张（832×1216, 15步）
- Render Node 0.0.0.0:8770，开机自启 + 守护脚本
- 第一张真出图已产出：D:\SevenAI\outputs\commercial_street_00001_.png
- v1.0.0 包已校验通过（12 modules / 8 schemas / 9 examples / 9 negative checks）
