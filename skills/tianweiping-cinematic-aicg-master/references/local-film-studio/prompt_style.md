# 电影质感Prompt模板 — 反塑料感关键词库

## 全局正面关键词（每个镜头必加）

```
35mm film grain, gritty realistic texture, physical material detail,
cinematic still, anamorphic lens, shallow depth of field,
imperfect lighting, natural film look, not CG plastic,
wet surfaces with water droplets, weathered textures,
Tsui Hark directing style, high contrast chiaroscuro
```

## 全局负面提示词（negative prompt）

```
CGI plastic, smooth skin, perfect lighting, video game graphics, 3d render,
cartoon, anime, oversaturated, clean, pristine, toy-like, plastic texture,
generic cyberpunk, neon overload, flat lighting, artificial,
over-smoothed, airbrushed, doll-like, waxy skin
```

## 按风格分类的关键词

### 赛博武侠
```
traditional Chinese wuxia meets cyberpunk, ancient architecture with neon signs,
samurai sword with energy core, rain-soaked streets, ink-wash atmosphere,
jianghu underworld, martial arts choreography, flowing robes in wind,
oriental cyber aesthetics, eastern philosophy meets future tech,
cyber jianghu, not generic cyberpunk, Chinese ink painting mood,
misty mountains with holographic screens, temple roofs with fiber optic cables
```

### 东方赛博美学（参考"纳米大片流水线"风格）
```
oriental cyber aesthetic, not neon overload, restrained color palette,
traditional Chinese architecture merged with technology,
ink wash gradients, misty atmosphere, philosophical emptiness,
minimal neon, maximum atmosphere, wuxia underworld,
weathered ancient materials with subtle tech implants,
not cyberpunk cliché, not bladerunner copy,
eastern melancholy meets future melancholy
```

### 赛博武侠核心原则（反塑料感关键）
> 重点不是给古装随便加点霓虹，而是让**东方轮廓、机械材质和镜头运动**真正融合在一起。

- **东方轮廓**：建筑是飞檐翘角、斗拱结构，不是西式摩天楼加中文招牌
- **机械材质**：金属是做旧的、有磨损的，不是崭新光滑的CG塑料
- **镜头运动**：是徐克式的凌厉快切+诗意长镜，不是匀速平移
- **色彩克制**：主色调是墨色、青色、暗金，霓虹只是点缀，不是铺满
- **空间纵深感**：用雾、雨、空气透视营造东方意境，不是堆满细节

### 雨夜霓虹
```
heavy rain, neon reflections on wet pavement, blue and orange color contrast,
fog in light beams, water droplets on camera lens, moody atmospheric
```

### 徐克式动作
```
fast dynamic camera, quick cuts, exaggerated movement, wire-fu aesthetic,
dramatic silhouettes, weapon trails, cinematic fight choreography,
unusual angles, tilted composition
```

### 逆光剪影
```
backlit silhouette, strong rim light, dark foreground, glowing background,
dramatic shadow, heroic composition, wind blowing hair and clothes
```

## 镜头prompt结构模板

每个镜头按这个格式写：

```
[主体描述], [场景描述], [动作描述],
[镜头运动], [光照描述], [质感关键词],
[风格参考], [分辨率]
```

### 示例：开场空镜
```
Wide shot of a cyberpunk Chinese city at night, heavy rain,
narrow alley looking up between tall neon-lit buildings,
camera slowly rises from puddle ground level up,
neon reflections shimmering on water, cold blue and warm orange contrast,
35mm film grain, gritty realistic texture, not CG plastic,
Tsui Hark wuxia style, 832x480
```

## 分辨率适配

| 目标输出 | 生成分辨率 | Upscale倍数 |
|---|---|---|
| 720p | 480p (832x480) | 1.5x |
| 1080p | 480p (832x480) | 4x |
| 4K | 720p (1280x720) | 4x |

> 16GB VRAM最高跑480p生成，720p需要24GB VRAM。
