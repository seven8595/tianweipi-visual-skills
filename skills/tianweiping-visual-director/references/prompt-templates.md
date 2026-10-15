# 提示词模板库（6 类 · 中英对照 · 可直接粘贴）

> 用法：`[主体描述] + [空间/场景] + [大师风格后缀] + [光线/材质/构图] + [质量词]`
> 负面提示词统一加在末尾。
> 大师后缀从 `master-style-lexicon.md` 复制，不要在 prompt 里堆大师名字（模型认风格参数，不认人名）。

---

## 通用负面提示词（Negative Prompt）

```
low quality, blurry, deformed, bad anatomy, extra fingers, missing fingers,
watermark, text artifacts, garbled characters, Chinese characters mistakes,
distorted perspective, floating furniture, plastic texture, overexposed,
underexposed, cluttered, AI artifacts, random objects, ugly, cartoon,
anime, oversaturated, lens flare abuse, HDR halos
```

中文场景补充：
```
无水印，无乱码文字，无畸形手指，无透视崩坏，无漂浮家具，无塑料质感，
无过度饱和，无多余装饰，画面干净
```

---

## 模板 1：建筑外观效果图（日景/夜景）

### 中文
```
[项目类型，如：一栋3层现代混凝土住宅]，
人视高度 1.5m，50mm 标准镜头，下午3点侧光，
[大师风格后缀，如：fair-faced concrete wall with uniform tie-hole grid, minimalist zen architecture, strong light and shadow contrast]，
[环境，如：建筑前一片浅水面反射，周围苔藓绿植，天空淡蓝薄云]，
超写实建筑可视化，物理正确材质，PBR，Octane Render 质感，
[MIR 电影感后缀：blue-hour dusk, warm interior glow through glass facade, atmospheric mist, cinematic wide shot]
```

### English
```
A [3-story minimalist concrete house],
eye-level 1.5m, 50mm standard lens, late afternoon side light,
[master style suffix e.g. fair-faced concrete wall with uniform tie-hole grid,
minimalist zen architecture, strong chiaroscuro],
[context e.g. shallow reflecting pool in front, mossy landscape, pale blue sky with thin clouds],
hyperrealistic architectural visualization, physically based materials,
Octane Render quality, cinematic wide shot,
8k, ultra detailed, professional architectural photography
```

### 夜景变体追加
```
转化成夜景，蓝调时刻（blue hour），天空深蓝紫渐变 #1E3A5F to #4A6B8A，
室内暖橙光 2700K 从玻璃透出，水面反射建筑倒影，
远处城市薄雾，小人剪影走在广场上，冷暖对比强烈，MIR 风格电影感。
```

---

## 模板 2：室内效果图（白模重绘 / 三图融合）

### 中文（白模直接重绘）
```
首先精准识别模型图中的窗户位置、尺寸与朝向，据此判断自然光的入射方向，
自然光从窗外柔和射入，主光均匀照亮室内主体，墙面漫反射辅光自然补亮暗部，
环境光通透柔和。
[风格后缀，如：Vincent Van Duysen monochromatic warm greige palette, textured plaster walls, bleached oak wide plank floor, low linen sofa]，
全视角材质纹理、光影层次、物体样式完全一致，
画面干净无多余元素，无水印无文字，透视准确，空间真实还原。

【硬约束】
- 禁止改变原始 3dmax/SU/酷家乐模型场景结构、物体位置和几何形状
- 保持所有家具、灯具、装饰品的原始样式与比例
- 材质转换为高精度符合物理规律的真实材质
- 保持原图比例、结构、主体、所有物体与细节不变
```

### English
```
Carefully identify window positions, dimensions and orientations in the input model,
determine natural light direction, soft daylight streaming through windows,
key light evenly illuminating the main interior, bounced fill light on walls,
transparent ambient atmosphere.
[Style suffix e.g. Vincent Van Duysen monochromatic warm greige, textured plaster walls,
bleached oak wide-plank floor, low linen sofa, single black articulating floor lamp],
consistent material textures, lighting layers and object styles across all views,
clean image, no watermark, no text, accurate perspective, true spatial representation.

Hard constraints:
- Do NOT alter original 3dmax/SU/Kujiale scene structure, object positions or geometry
- Preserve original furniture, lighting fixtures and decor proportions
- Convert to physically accurate high-quality materials
- Maintain original ratio, structure, subject and all details
```

### 三图融合版
```
在图一基础上，附着图二的〔材质/砖缝颜色〕，参考图三的〔配色和软装〕，生成效果图。
不要改变图一的比例以及模型细节。
```

---

## 模板 3：平面图 → 3D 视角

### 中文
```
参考图一平面户型图，按图二红框选定的〔客厅/主卧/餐厅〕房间、
红箭头朝向的相机位置（站在 XX 角，看向 XX 方向），
生成人视高度 1.5m 的 3D 写实效果图。
相机 28mm 广角，下午自然光从〔南窗/落地窗〕射入。
[风格后缀，如：奶油风，暖白微水泥，浅橡木地板，米白布艺沙发]。
不改变平面图墙体、门窗位置和房间划分。
```

### 带生活感
```
同上，加一个生活化人物（女性，穿家居服，不看镜头，不酷脸）坐在沙发上看书，
旁边有一杯咖啡和一本书，人物占画面比例不超过 15%。
```

---

## 模板 4：轴测图 / 剖透视（概念阶段）

### 中文（Alex Hogrefe 风格概念图）
```
建筑概念轴测图，白色体块建筑模型放置在抽象的〔朱砂红/钴蓝〕色块地面上，
可见数字笔触和图层叠加质感，风格化非写实，
[建筑形态描述，如：悬挑方盒子+下沉庭院+屋顶花园]，
人物和树作为尺度参照，背景淡天空留白，
Alex Hogrefe 式概念图解，大胆色块对比，叙事性强。
```

### English
```
Conceptual architectural axonometric, white massing model building on abstract
[cinnabar red / cobalt blue] color-block ground, visible digital brushstrokes,
layered painterly texture, stylized not photorealistic,
[building description e.g. cantilevered box with sunken courtyard and green roof],
small human figures and trees for scale, pale sky background,
Alex Hogrefe style concept diagram, bold color blocking, narrative composition.
```

### 剖透视（带内部空间）
```
建筑剖透视，沿〔主楼梯/中庭〕剖切，可见内部〔房间/走廊/光线路径〕，
剖面线清晰，周围保留环境，标注主要空间名称（英文小标签），
[风格后缀]，概念设计汇报图。
```

---

## 模板 5：海报 KV / 品牌主视觉

### 中文（原研哉极简留白）
```
[产品/项目名称] 主视觉海报，
本白背景 #F5F1E8，大面积留白 ≥70%，
[主体物，如：一个黑色陶瓷杯/建筑局部剪影] 居中偏下，
[一句 slogan] 用极细无衬线字体排在角落，
纸张触感，哑光不反光，平坦漫射光，
原研哉式空的哲学，无印良品式克制，
不要装饰，不要渐变，不要投影。
```

### English
```
[Product/project name] key visual poster,
warm off-white background #F5F1E8, negative space ≥70%,
[subject e.g. a black ceramic cup / architectural silhouette] centered below middle,
[one slogan] in ultra-thin sans-serif at corner,
matte paper texture, flat diffuse light,
Kenya Hara MUJI-style emptiness, restrained and quiet,
no decoration, no gradient, no drop shadow.
```

### 佐藤可士和超级符号版
```
[品牌名] 主视觉，一个醒目几何符号居中（红色 #E60012 方块/圆形），
纯白底，超粗黑体大字贴边，三原色红/黄/蓝硬边色块，
10 米外一眼识别，平面矢量感，无渐变无阴影，
Kashiwa Sato 式超级符号，超整理术风格。
```

---

## 模板 6：日转夜 / 暗调氛围

### 日转夜（已有白天图）
```
转化成夜景，外景柔和的低饱和度蓝色月光与室内暖黄灯光形成强烈冷暖对比，
光线细腻有层次，
[空间描述]，
窗外可见城市夜景散景（bokeh），
室内灯具体现温暖 2700K，
MIR 风格蓝调时刻电影感，水面/地面反射灯光，
小人剪影在室内走动。
```

### 暗调氛围（从零出）
```
一束光穿透黑暗，仅依靠〔单一光源，如：水晶吊灯/壁龛灯带〕散发的漫反射光
微弱勾勒〔空间主体〕，逼真物理材质，Octane Render 渲染，光线追踪，
戏剧性的光影氛围，极致纯净的画面质感，
大面积暗部占 70%，高光集中在主体，
电影感低调照明（low-key lighting）。
```

---

## 组合示例：从一句话到完整 prompt

用户："帮我出一套奶油风三居室客厅效果图"

1. Brief：住宅 / 业主自看 / 调性=温暖治愈 / Van Duysen 方向
2. 风格后缀：`Vincent Van Duysen monochromatic warm greige palette, textured plaster walls, bleached oak wide-plank floor, low linen sofa, single black articulating floor lamp, nordic-minimalist warmth, tactile materials`
3. 套模板 2（室内）
4. 加负面提示词
5. 批量：主空镜 + 带人物版 + 日转夜 + 材质特写 2 张
6. 给用户 4 张候选选终稿
7. Real-ESRGAN 超分到 4K

---

## 提示词组装槽位（背下来）

```
[用途声明] → [主体/空间] → [相机/镜头] → [光线] → [大师风格后缀]
        → [材质/色彩] → [构图/留白] → [质量词/渲染器名] → [负面提示词]
```

**反面**：不要堆"8K/超清/大师杰作/电影级/摄影大片"——这些词模型见太多了，用 Octane Render / physically based / 50mm lens 这种具体词更有效。
