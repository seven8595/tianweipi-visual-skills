# 真人电影剧照质感 Prompt 模板库

三国漫剧项目实战验证（2026-09，7次风格迭代后确认）。
目标：**98版《三国演义》电视剧截图质感**，不是AI生成感。用户否决词："太假了""不像真人"。

## 一、核心公式

```
Screenshot from [年代] TV drama [剧名] + photorealistic live-action still of [角色/场景]
+ real actor face + detailed skin texture with pores and wrinkles
+ [材质磨损描述] + [颜色做旧描述]
+ grainy film texture + looks like a real TV drama screenshot not AI generated
```

## 二、人物人设模板

### 刘备（黄晓明版，帅但写实）
```
Screenshot from 2010 TV drama Three Kingdoms, photorealistic live-action still of Liu Bei,
handsome noble face, sharp jawline, kind determined eyes, long black beard,
wearing cream-white Hanfu robe with subtle embroidery, jade crown hairpiece,
warm golden hour lighting, shallow depth of field, peach blossom background,
detailed skin texture, movie still from a historical drama film, vertical 9:16
```

### 关羽（陆树铭版，红脸长髯）
```
Screenshot from 1994 TV drama Three Kingdoms, photorealistic live-action still of Guan Yu,
real actor face, detailed skin texture with pores and wrinkles, reddish-brown skin tone,
long flowing black beard, wearing green cloth robe under simple iron armor, green headscarf,
dignified serious expression, natural daylight, grainy film texture,
looks like a real TV drama screenshot not AI generated, vertical 9:16
```

### 张飞（李靖飞版，粗粝写实）
```
Screenshot from 1994 TV drama Three Kingdoms, photorealistic live-action still of Zhang Fei,
real actor face, detailed weathered skin texture, thick black beard and wild hair, burly build,
wearing worn black leather armor with red cloth underneath, fierce but not cartoonish expression,
natural campfire lighting at night, grainy film texture,
looks like a real TV drama screenshot not AI generated, vertical 9:16
```

## 三、场景模板

### 古代市集（涿郡街头）
```
Cinematic film still, photorealistic ancient Chinese market street,
wooden storefronts with hanging cloth banners, dirt road with dust,
commoners in rough Hanfu robes walking, grey tiled rooftops,
overcast natural daylight, wide establishing shot, vertical 9:16
```

### 桃园夕阳
```
Cinematic film still, photorealistic ancient Chinese peach blossom garden in full bloom at sunset,
rows of old peach trees with pink flowers, warm golden hour lighting, dirt ground,
distant mountains, romantic peaceful atmosphere, wide establishing shot, vertical 9:16
```

## 四、关键帧模板

### 单人动作
```
[角色模板] + [具体动作：推木车/站摊位/席地而坐] + [场景模板] + [自然光/特定时段]
```

### 双人/三人对峙
```
[角色1模板] on left, [角色2模板] center, [角色3模板] right,
tense atmosphere, eye contact, natural daylight, vertical 9:16
```

## 五、"太假"诊断清单（用户否决后逐项查）

| 问题 | 原因 | 修法 |
|---|---|---|
| 脸太光滑 | AI默认美颜 | 加 `detailed skin texture with pores and wrinkles, sunburn` |
| 铠甲太新 | AI默认崭新 | 加 `weathered old iron armor with scratches and rust` |
| 颜色太鲜艳 | AI默认高饱和 | 加 `worn and faded clothes`，用阴天/自然光压饱和度 |
| 像CG不像真人 | 缺胶片感 | 加 `grainy 16mm film texture` |
| 表情夸张 | 卡通化 | 加 `dignified serious expression`，不用怒吼模板 |

## 六、两条路线不要混

| 项目 | 选哪条 |
|---|---|
| 红果/抖音短剧·真人感 | 真人剧照质感（本文件） |
| 儿童/治愈/绘本 | 厚涂插画（见 `田伟平电影动画aicg大师/references/drama-quality-rubric.md` 竖屏漫剧量产模板） |
| 科幻/赛博 | 赛博朋克（见 cyberpunk.md） |
| 情感/文艺 | 王家卫（见 wong-kar-wai.md） |
