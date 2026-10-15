> 田伟平视觉技能库 · 全库地图
> 用途：查任何内容前先看这张表，确认该读哪个技能、哪个文件。
> 核对原则：以磁盘实际文件为准，不要凭描述假设。

# 全库地图（6 个技能）

```
C:\Users\seven\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.user_skills\
```

| # | 技能 | 定位 | 规模 |
|---|---|---|---|
| 0 | **田伟平设计总监大师级别** | 总纲：标准 + 路由 + 跨域能力 | SKILL.md + 40 文件 |
| 1 | **田伟平视觉设计ai智能体自动化生图总监水平skill** | 建筑/室内空间出图生产 | 30 文件 |
| 2 | **田伟平建筑设计师** | 建筑学习路线 / 6 步管线 / 宣传片 / 提案 PPT | 7 文件 |
| 3 | **田伟平潮玩设计大师** | 角色 IP / 潮玩 / 绘画 / UI 审美 / 制作规范 | 49 文件 |
| 4 | **田伟平电影动画aicg大师** | 电影感 / 导演风格 / 动画 / 漫剧 / 海报 | 38 文件 |
| 5 | **田伟平总监审核标准** | 12 维审稿 / 设计风格参数 / 本地调参 | 13 文件 |

---

## 0. 田伟平设计总监大师级别（总纲 · 本技能）

| 文件 | 什么时候读 |
|---|---|
| `SKILL.md` | 任何视觉任务的第一个入口 |
| `references/director-standard.md` | 要定"总监级"标准、拒绝权、12 维、本地调参 |
| `references/library-index.md` | 本文件——查全库 |
| `references/model-selection.md` | 选模型、比较本地/云端 |
| `references/dual-director-review/` | 审已成片（宫崎骏×诺兰）、发片终检 |
| `references/shot-cards/` | 写镜头提示词、运镜、转场 |
| `references/film-visual-reference/` | 漫剧/短剧风格路线、红果爆款公式 |
| `references/commercial-street/` | 商业综合体/开放式街区 ArchViz |
| `references/visual-core/` | 画面量化质检、定向修复、视频帧检 |
| `references/space-plan/` | 平面图转白模 |
| `scripts/` | vqc / vfix / shot / vframe / autoloop / build_whitebox / submit_comfyui |

---

## 1. 田伟平视觉设计ai智能体自动化生图总监水平skill

**管**：一句话需求 → 建筑效果图 / 室内效果图 / 平面户型图 / 轴测剖透视 / 海报 KV / 夜景日景变体 / 九宫格营销图 / 图生视频分镜。

**核心方法**：Linktel/Lynkvis/即梦节点画布七大技术——保结构重绘 / 三图融合 / 红框标注局部修改 / 平面图出 3D / 六按钮批量 / 九宫格物料 / 日转夜 + LLM 分镜图生视频。叠加 13 位建筑与室内大师风格卡 + 12 维审稿。

**用户只拍板 3 个节点**：风格方向 / 最终选稿 / 对外发布。

**主要 references**：`video-techniques-extracted.md`（七大技术原文）、`design-director-workflow.md`（总监工作流）、`prompt-templates.md`、`redlines-and-checklist.md`、`tianweiping-signature-style.md`、`cinematic-narrative-portraits.md`、`fmcg-poster-portfolio-case.md`、`emergency-portfolio-cheatsheet.md`、`master-style-lexicon.md`

---

## 2. 田伟平建筑设计师

**管**：建筑设计从零到总监的学习路线 / 建筑视觉 6 步管线 / 三大师风格 / 建筑宣传片 / 设计提案 PPT。

| 文件 | 内容 |
|---|---|
| `references/learning-roadmap.md` | 六阶段学习路线（含免费软件替代） |
| `references/master-6step-pipeline.md` | 纸笔草图 → 线稿 → 灰模 → 材质灯光 → 渲染 → PS 后期 |
| `references/masters.md` | 安藤 / 扎哈 / BIG 三大师画法详解 |
| `references/promo-studio.md` | 建筑宣传片全流程 + 运镜库 |
| `references/proposal-ppt-spec.md` | 11 页提案 PPT 结构 + 四色制 |
| `references/proposal-ppt-quick-template.md` | PPT 逐页排版参数（可直接套） |

---

## 3. 田伟平潮玩设计大师

**管**：角色 IP 设计 / 潮玩盲盒与周边 / 三视图转面 / 表情动作 / 玩具化 / 风格词典 / 数字绘画全流程 / AI 痕迹诊断 / 本地 Flux 精修 / 图片视频制作规范 / UI 审美校准。

| 文件 | 内容 |
|---|---|
| `references/character-ip-methodology.md` | 角色 IP 完整方法论（36KB） |
| `references/art-creation-workflow.md` | 数字绘画完整流程 + Flux 实战教训 |
| `references/prev-artist-toydesign-full.md` | 上一版主文件全文（查细节） |
| `references/seven-style-profile.md` | SEVEN 个人风格档案 |
| `references/local-flux-refine.md` | 本地 Flux 精修实操 |
| `references/longlin-baby-case.md` / `dragon-baby-workflow.md` | 龙鳞宝贝项目标准 + ERR-ART-001 |
| `references/toy-character-principles.md` / `toy-chibi.md` | 潮玩角色硬约束 |
| 6 大风格词典 | `cyberpunk-hard` / `retro-deco` / `wild-impasto` / `biomech-dark` / `crystal-painterly` / `toy-chibi` |
| `references/ui-aesthetic.md` | 界面/网页审美校准 |
| `references/visual-direction.md` / `image-workflow.md` / `video-workflow.md` / `quality-and-repair.md` | 制作规范 |
| `references/production-handoff.md` / `project-and-code.md` / `capabilities-and-sources.md` | 交接与校验 |
| `scripts/` | check_project.py / build_handoff.py / probe_media.py |
| `_reference_pack/` | 艺术研究原始资料 |

---

## 4. 田伟平电影动画aicg大师

**管**：真人电影导演视觉签名 / 导演审片 / 动画电影全流程 / 日本动画大师方法（宫崎骏 JM / 新海诚 JS / ufotable JU）/ 漫剧质量 / 电影级海报。

| 文件 | 内容 |
|---|---|
| `references/directors.md` | 13 位真人电影导演视觉签名 + 场景速查 |
| `references/review-prompts.md` / `review.md` | 审片模板 + 动画审片与返修 |
| `references/aicg-film-playbook.md` | AIGC 动画电影完整实战手册（27KB，21 节） |
| `references/master-visual-reference.md` | 摄影/动画大师视觉参数 + 4 张检查清单 |
| `references/master-methods.md` | 宫崎骏/新海诚/ufotable 方法转译 |
| `references/emotional-longform.md` | 长篇叙事与情感编剧 |
| `references/design-language.md` / `cinematic-recipes.md` / `quality-and-iteration.md` | 海报设计语言 + 三种配方 + 质检 |
| `references/drama-quality-rubric.md` | 漫剧质量评分 |
| `references/v11-library/` | 风格库 + 角色库 + 导演库（JSON） |
| `templates/` | hero_frame / i2v_motion 模板 |
| `assets/ref-01~03.png` | 海报风格范例 |

**本地管线事实**：ComfyUI 活跃实例 = `C:\Users\seven\Desktop\ComfyUI_windows_portable\`，API `127.0.0.1:8188`；H3 模板 `D:\AI_WORKSPACE\h3_template.json`；Real-ESRGAN `F:\upscale_work\realesrgan-ncnn-vulkan.exe`。

---

## 5. 田伟平总监审核标准

**管**：出图前立 brief、出图后 12 维审稿、SMART REPAIR、本地模型参数、AI 致命错误识别、25+ 设计风格参数、30+ 大师方法论。

| 文件 | 内容 |
|---|---|
| `references/brief_templates.md` | 总监立 brief 模板 |
| `references/design-styles.md` | 25+ 种设计风格参数（配色/字体/圆角/阴影/排版） |
| `references/design_masters.md` | 30+ 位设计大师方法论 |
| `references/fatal_mistakes.md` | AI 出图致命错误图鉴 + 修复关键词 |
| `references/local_model_tuning.md` | 本地 ComfyUI / Flux / SDXL 参数 |
| `references/commercial-space-review.md` / `commercial-space-cases.md` | 商业空间审稿 + 5 种案例 |
| `assets/reference-images/I01-I05.jpg` | 商业空间案例参考图 |

---

## 常见任务 → 读哪里

| 任务 | 路径 |
|---|---|
| 做一张建筑效果图 | 技能 1（生产）+ 技能 5（审稿） |
| 学建筑/问怎么成为设计总监 | 技能 2 `learning-roadmap.md` |
| 设计一个角色 IP | 技能 3 `character-ip-methodology.md` |
| 角色图画出来像 AI | 技能 3 第 7 节 + `local-flux-refine.md` |
| 做一条电影感短片 | 技能 4 + 总纲 `shot-cards/` |
| 审一条已成片 | 总纲 `dual-director-review/` |
| 画面有点糊/发灰/挑一张 | 总纲 `visual-core/` + `scripts/vqc.py` |
| 商业综合体效果图 | 总纲 `commercial-street/` + 技能 1 |
| 平面图转白模 | 总纲 `space-plan/` + `scripts/build_whitebox.py` |
| 选哪个模型 | 总纲 `model-selection.md` |
| 海报怎么才不"AI 味" | 技能 5 `design-styles.md` + `fatal_mistakes.md` |
