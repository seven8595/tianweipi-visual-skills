---
name: dragon-baby-ip-workflow
description: 龙鳞宝贝IP角色插画项目工作流。触发词：龙鳞宝贝、倒立微笑、龙女IP、角色插画修图。包含ERR-ART-001错误记录（手部畸形被客户驳回）、ComfyUI本地工作流、PS修图步骤、交付前自检清单。
---

# 龙鳞宝贝 IP 角色插画工作流

## 项目背景
- IP名：龙鳞宝贝
- 当前任务：倒立微笑姿势角色插画
- 历史问题：首次交付因手部畸形、人体比例错误被客户驳回（ERR-ART-001）

## 强制规则（ERR-ART-001 永久生效）
1. AI 出图仅作草图，禁止直接交付原始 AI 图
2. 手部必须 PS 重绘：5根手指、关节透视正确、手掌比例协调
3. 交付前必须逐项打勾自检清单
4. 倒立姿势重点检查：重心、脖子弯曲度、衣服褶皱方向、头发因重力垂落

## ComfyUI 工作流
- 本地路径：项目目录下 `dragon_baby_upside.json`
- 硬件：Windows RTX 5080
- 参数：1024×1440，dpmpp_2m/karras，28步，CFG7
- 正向提示词核心：correct hand anatomy, 5 fingers, proper limb proportion
- 反向提示词核心：bad anatomy, deformed hands, extra fingers, missing fingers

## PS 修图流程
1. 骨架校正（红色线图层画人体结构）
2. 手部重绘（找真人倒立手参考，钢笔工具勾轮廓）
3. 面部修正（倒立五官对称、微笑不歪）
4. 材质细化（龙鳞高光、衣服褶皱方向）
5. 统一光影（曲线+色彩平衡+盖印锐化）

## 交付物
- PSD 分层源文件
- JPG 预览图（sRGB）
- 压缩包命名：`龙鳞宝贝-倒立微笑_修订版.zip`
- 附一句话修改说明

## 参考构图
- 正面倒立：双手撑地，龙鳞长发垂落
- 侧面倒立：展示龙尾和服饰侧面细节
