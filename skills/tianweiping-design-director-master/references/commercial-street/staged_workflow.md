# 11 阶段闭环 Prompt 模板（V2）

每一轮 seed 固定，构图 / 机位 / 透视完全不变，只改该轮 prompt 片段。
先选定主参考图（图1–图5），把对应 DNA 关键词块作为基础，再按 11 阶段逐层加。

---

## 阶段 01 · 概念设计

**目标**：定主张、调性、参考大师、尺度。

输出（不生图，只写 brief）：
- 项目类型 / 定位 / 受众
- 一句话主张（如"在城市核心区，创造一个让人愿意停留的开放街区"）
- 3 个调性关键词（如：克制 / 温暖 / 都市）
- 主参考图（图1–图5 选 1）
- 输出画幅（横 3840×2160 / 竖 2160×3840）

---

## 阶段 02 · 总体空间（体块）

**目标**：建筑体块、道路宽高比、动线、前中后景、主入口、下沉 / 连廊关系。不要灯光不要人不要招牌。

### Positive
```
architectural massing study, open-air shopping district, 2-3 story retail podium with high-rise residential/commercial towers in background, clear street width to building height ratio, main pedestrian axis, aerial sky bridges connecting buildings, sunken plaza in midground, corner entrance pavilion, foreground open plaza with planters, midground building volumes, background city towers, two-point perspective, 26mm lens, eye-level camera 1.6m, vertical lines perfectly vertical, neutral overcast daylight, no people, no signage, no warm lighting, no decoration, architectural model quality, rational urban design, human scale, study rendering
```

### Negative
```
people, crowd, pedestrians, shop signs, brand logos, warm lighting, neon, golden hour, blue hour, decorative elements, trees, cafe tables, outdoor seating, cars, fantasy architecture, twisted building, distorted perspective, tilted verticals, wide angle distortion, fisheye, floating buildings, cartoon, anime, cheap CGI
```

### 参数
- 分辨率：`1344×768`（横版）/ `768×1344`（竖版）
- Steps：Flux 24 / SDXL 30
- **Seed 固定**，后面 9 轮都用这个 seed。

### 检查
- [ ] 建筑体块合理，人走得通
- [ ] 道路宽高比舒服
- [ ] 裙房 2–3F + 背景高层 比例对
- [ ] 前中后景三层纵深
- [ ] 有连廊 / 下沉 / 主入口节点

---

## 阶段 03 · 建筑深化

**目标**：锁阶段 02 构图，只深化立面。

### Positive（在 S02 基础上替换 / 追加）
```
architectural massing preserved, open-air shopping district, 2-3 story retail podium, two-point perspective, 26mm lens, eye-level 1.6m, vertical lines corrected,
facade material hierarchy: ground floor natural stone cladding, upper floor brushed metal panels and large glass curtain wall, timber slat fins as vertical accents, deep recessed shop windows, stone cornice and eaves, wood soffit under terraces, metal railings on setback balconies, corner glass shopfront, main entrance with deep canopy, curved commercial podium edge (reference image 1 / 5),
sky bridges with black metal railings, sunken plaza with light stone,
no people, no signage, neutral daylight, rational material palette, international high-end commercial architecture, detailed facade proportion, honest materials
```

### Negative
```
people, crowd, shop signs, brand logos, warm lighting, neon, blue hour, exaggerated ornament, fake classical columns, plastic texture, cartoon, cheap CGI, distorted perspective
```

### 检查
- [ ] 材料比例有节奏（石 / 金属 / 玻璃 / 木）
- [ ] 檐口、橱窗、退台、连廊有细节
- [ ] 建筑不单调（不是两排一样的楼）

---

## 阶段 04 · 景观深化

**目标**：加植物、座椅、水景、构筑物、停留节点。学图4 的景观总监思维。

### Positive（追加）
```
...S03 保留...
+ landscape design: mature canopy trees along pedestrian axis (reference image 1 / 3), wild planting at ground level (shrubs, perennials, ornamental grasses, reference image 4), curvilinear wooden bench seating wrapping around tree pits, circular planters with integrated uplighting, shallow reflecting pool in foreground (reference image 1), membrane canopy with timber columns as gathering node (reference image 4), stone pavement with geometric pattern, continuous seating system, outdoor dining terraces with wooden tables
+ landscape is not just decorative trees, but a designed public space system
```

### Negative（追加）
```
neatly trimmed lawn, single species planting, trees in uniform rows, empty hardscape, no seating
```

### 检查
- [ ] 乔灌草层次完整（不是只有草坪）
- [ ] 有"坐"的系统（多种座椅）
- [ ] 植物自然，不是摆盆景
- [ ] 有停留节点（不是只是走的路）

---

## 阶段 05 · 商业运营

**目标**：加业态、外摆、橱窗、导视。不加人（下一轮加）。

### Positive（追加）
```
...S04 保留...
+ ground floor retail: cafés, restaurants, fashion boutiques, lifestyle stores, large display windows with merchandise visible (blurred interior), outdoor dining terraces with 4-6 tables each, wayfinding sign (minimal, not prominent), art installation in plaza center,
+ at most 2-3 blurred shop signs, no legible brand logos
```

### Negative（追加）
```
brand logos everywhere, sign spam, legible Chinese characters, garbled text, neon signs, billboards
```

### 检查
- [ ] 业态有层次（咖啡 + 餐饮 + 零售）
- [ ] 外摆自然
- [ ] 招牌要么模糊要么不出现
- [ ] 没有广告位抢戏

---

## 阶段 06 · 灯光（Blue Hour）

**目标**：锁空间，改时间到蓝调时刻。

### Positive（替换 / 追加）
```
...S05 保留...
+ blue hour sky: deep blue to purple gradient, 6500K cool ambient, sunset glow on horizon
+ interior commercial lighting: warm 2700-3500K light spilling from shop windows, key shop entrances and dining terraces well lit, secondary areas naturally dim
+ architectural lighting: continuous LED strip under curved eaves (reference image 1), uplighting on trees, bollard lights along pedestrian path, ground-level linear LED guiding flow (reference image 3)
+ ground: slightly wet stone pavement, soft warm reflections, not mirror-like
+ lighting hierarchy: bright / mid / dark three levels, not whole street glowing gold
```

### Negative（追加）
```
whole street glowing gold, flat lighting, christmas lights, excessive string lights, overexposed interior, mirror reflection, pure black sky
```

### 检查
- [ ] 天空是深蓝→蓝紫
- [ ] 室内暖光 2700–3500K
- [ ] 有亮区 / 次亮区 / 暗区
- [ ] 地面反射克制
- [ ] 没有整条街金灿灿

---

## 阶段 07 · 人物

**目标**：加少量真实活动的人，作为尺度和运营氛围。

### Positive（追加）
```
...S06 保留...
+ sparse but natural pedestrians as scale reference:
  - a few people walking away from camera on main axis
  - one couple chatting at distance
  - customers seated at outdoor cafe tables (backs to camera)
  - window shoppers glancing into boutiques
  - family with child walking
  - person sitting on bench reading
  - cyclist passing through
+ realistic human scale, natural movement, no posing, no facing camera, no crowd
```

### Negative（追加）
```
crowded street, dozens of people, people facing camera, posing tourists, duplicate clones, deformed hands, giant heads, giant people, tiny people
```

### 检查
- [ ] 人是点景不是主角
- [ ] 没有大量正脸
- [ ] 人比例正确
- [ ] 活动多样（走 / 坐 / 吃 / 亲子）

---

## 阶段 08 · 材质

**目标**：提升材质真实感，PBR。

### Positive（追加材质关键词块）
```
PBR materials, physically based rendering, realistic reflections, micro surface details, roughness variation, glass reflection showing sky and surrounding buildings, natural stone texture with weathered variation, brushed metal, warm wood soffit with visible grain, concrete with subtle texture, global illumination, ray traced soft shadows, volumetric warm light haze, cinematic architectural photography, professional archviz, ultra detailed, natural depth of field, HDR
```

### Negative（追加）
```
plastic material, CGI toy, cheap texture, oversaturated, over-sharpened, waxy skin, fake glass, mirror reflection
```

### 检查
- [ ] 玻璃 / 石材 / 金属 / 木 有真实粗糙度
- [ ] 反射合理（不是镜子）
- [ ] 没有塑料感

---

## 阶段 09 · QA

按 SKILL.md 第 5 节 12 维 checklist 逐项打勾。任何 ❌ 进入 SMART REPAIR，不进下一阶段。

---

## 阶段 10 · 局部修复（inpaint）

| 问题 | 修复 prompt |
|---|---|
| 招牌乱码 | `blurred out-of-focus shop window, frosted glass, no text` |
| 多手指 / 畸形手 | `hands in pockets, arms crossed, back view, natural hand` |
| 玻璃反射假 | `realistic glass reflection, subtle sky reflection, faint interior visibility` |
| 树假 / 塑料感 | `natural deciduous tree, realistic bark, soft leaves, natural up-light` |
| 人脸崩 | `pedestrian walking away, back view, out of focus face` |
| 建筑接缝穿模 | `clean building junction, stone corner detail, realistic construction joint` |

---

## 阶段 11 · 高清输出

1. 前面 10 轮都在 `1344×768`（横）/ `768×1344`（竖）跑。
2. 选最好的一张，img2img（denoise 0.4–0.5）在 `1920×1080` / `1080×1920` 重绘一次。
3. Real-ESRGAN x4+ 或 4x-UltraSharp 超到 `3840×2160` / `2160×3840`。
4. 印刷用 A3 300 DPI 时单独处理（不在生图节点拉 4961×3508）。

---

## 一句话

**像建筑师一样思考，像景观设计师一样布置，像商业顾问一样运营，像照明设计师一样控光，像建筑摄影师一样取景，像修图师一样修局部。** 不要一次做完所有事。
