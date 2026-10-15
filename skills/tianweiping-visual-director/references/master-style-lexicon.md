# 设计大师风格词典（Master Style Lexicon）

> 用途：把 13 位建筑/室内/平面/建筑可视化大师的视觉语言，压缩成可直接拼进 AI 生图提示词的参数卡。
> 使用方式：选定一位大师 → 把"英文提示词片段"直接粘贴到生图模型 prompt 末尾作风格后缀；按需要叠加自己的主体描述。
> 红线：学视觉参数，不抄可识别的具体作品造型与标志元素。
> 调研日期：2026-10-13

---

## 一、建筑设计

### 1. 安藤忠雄 Tadao Ando

**3 个视觉关键词**：清水混凝土 / 光缝 / 几何纯粹

**核心理念**：用最朴素的混凝土方盒子围合出绝对黑暗，再切一条缝让光进入，让光成为空间唯一的装饰。强调实体与虚空、明与暗的二元张力，把建筑做成"凝固的精神容器"。

**标志性手法**：
- 18mm 对缝清水混凝土墙面，模板螺栓孔（plywood formwork tie holes）成规则网格排列
- 墙顶/墙侧切 20–50mm 窄缝，自然光从顶缝或侧缝斜射进暗室
- 纯几何体块（长方体、立方体）咬合，偶尔一面斜墙 15° 打破秩序
- 不挂画、不加装饰，"太阳是唯一的画家"
- 室外配浅水镜面水池反射建筑，倒影与实体各占一半画面

**风格卡**：
- 材质：raw fair-faced concrete, exposed plywood formwork tie holes in regular grid, matte smooth grey concrete, no paint, no ornament
- 光线：single slit of daylight entering a dark room, hard rectangular light beam projected on floor and wall, high contrast chiaroscuro, soft ambient bounce
- 色彩：monochrome cool grey concrete (~#B8B8B4), near-black shadow void, single warm-white daylight patch as accent
- 构图：eye-level interior corner shot, strong perspective vanishing to the light slit, deep shadow foreground, generous negative space, centered symmetrical composition
- **EN prompt snippets**：`fair-faced concrete wall with uniform tie-hole grid, cruciform or horizontal slit daylight cutting through a dark room, monolithic concrete volume, minimalist zen interior, high contrast light and shadow, shallow reflective water pool in front`
- **中文提示词片段**：`清水混凝土墙面带规则螺栓孔网格，一道十字/水平光缝射入暗室，整浇混凝土方盒子，极简禅意室内，强烈明暗对比，建筑前一片浅水面反射`

**红线**：不要直接复刻"光之教堂"那面完整 4m 高十字缝墙、不要复刻住吉长屋的窄天井原型；取"混凝土+窄光缝"的语法，换到别的空间。

**参考**：
- https://www.archdaily.com/101260/ad-classics-church-of-the-light-tadao-ando
- https://www.studiomatrx.org/guides/church-of-the-light

---

### 2. 扎哈·哈迪德 Zaha Hadid

**3 个视觉关键词**：流体曲线 / 参数化 / 反重力

**核心理念**：建筑像被水流和风场冲刷而成，没有开始也没有结束，墙、地、顶连续流动、消融边界。源于至上主义（马列维奇）的"轻盈、浮动、结构轻轻着地"，用参数化软件生成连续非线性形态。

**标志性手法**：
- 墙、地、天花一体化翻折，找不到直角和明确交接缝
- 流线型带状曲线连续蜿蜒，如冰川、河流、 ribbon
- 建筑体块与地面若即若离，局部悬挑、反重力漂浮感
- 白/银灰光滑曲面（GRC 或白色复合板），少见砖与木
- 室内中庭多层贯通，坡道代替楼梯，动线本身是雕塑

**风格卡**：
- 材质：smooth white GRC composite panels, seamless curved surfaces, glossy gradient glass, no visible joints, parametrically bent aluminum
- 光线：soft diffuse daylight from above, interior linear LED strips following curved ribbon edges, no hard shadows, even ambient
- 色彩：monochrome white / ice grey / silver, occasional single bold accent (hot red or acid yellow) on furniture or signage
- 构图：low wide-angle shot exaggerating the curve, long sweeping diagonal composition, strong foreground curve leading eye into depth, no horizon line
- **EN prompt snippets**：`parametric fluid architecture, continuous ribbon-like curved surfaces, seamless white composite facade, deconstructivist flowing interior, gravity-defying cantilever, smooth gradient glass, Zaha Hadid style`
- **中文提示词片段**：`参数化流体建筑，连续飘带状曲面，无缝白色复合板立面，解构主义流动室内，反重力悬挑，渐变玻璃`

**红线**：不要直接画大兴机场的海星状放射平面、不要画广州大剧院的双砾石造型；取"连续曲线+白曲面"语法，不要复制具体项目轮廓。

**参考**：
- http://m.toutiao.com/group/7589486901460173355/
- http://m.toutiao.com/group/6450596934263505166/

---

### 3. 隈研吾 Kengo Kuma

**3 个视觉关键词**：负建筑 / 木格栅 / 消隐于环境

**核心理念**："让建筑消失"，用木、竹、石、瓦等自然细碎材料做半透格栅，把建筑消解成一层与植被同节奏的表皮，与风土共振，不与环境对抗。

**标志性手法**：
- 45–60cm 深竖向木格栅（落叶松/杉木）包覆立面，木条间隙透进柔和漫射光
- 室内外界面用木格栅+和纸半透明隔断模糊掉
- 大量重复的小模数构件（瓦、石片、竹条）形成鳞片/雨帘质感
- 建筑退台式种植屋顶，草从屋顶长下来
- 与旁边树木的竖向线条故意对齐（如表参道 One 项目的木竖梃）

**风格卡**：
- 材质：vertical cedar or larch louvers 45cm deep, semi-transparent washi paper screens, small-scaled stone shingles, bamboo battens, raw untreated wood
- 光线：soft dappled light filtering through wooden slats, gentle diffused daylight, no direct hard sunbeam, warm 3500K ambient
- 色彩：natural wood tones (pale cedar #C9B896), moss green, stone grey-brown, low saturation, earth palette
- 构图：eye-level facade detail shot, rhythmic vertical repetition, half-exterior half-interior blur, tree foliage overlapping the building, shallow depth of field
- **EN prompt snippets**：`vertical wooden louver facade, semi-transparent washi screen, Kengo Kuma style, building dissolving into nature, rhythmic timber battens, dappled daylight through slats, mossy green context`
- **中文提示词片段**：`竖向木格栅立面，半透明和纸隔断，隈研吾式，建筑消隐于自然，韵律木条，光影透过格栅洒落，苔藓绿环境`

**红线**：不要直接复刻长城脚下竹屋的管状竹筒、不要复刻根津美术馆的完整屋檐比例；取"木格栅+消隐"语法。

**参考**：
- https://kkaa.co.jp/project/one-omotesando/?language=en
- https://m.thepaper.cn/newsDetail_forward_6863804

---

### 4. 卒姆托 Peter Zumthor

**3 个视觉关键词**：片麻岩 / 氛围 / 沉默

**核心理念**：建筑是材料、温度、光线、回声、气味共同调制的"氛围"，不是形式游戏。就地取材，把石头切开打磨让它内部的质感露出来，营造近乎虔诚的沉默空间。

**标志性手法**：
- 四万片灰色片麻岩（quartzite gneiss）薄片横叠墙身，每片厚 3–5cm，缝宽 5mm
- 屋顶切一条横向长光带（slit skylight），自然光从顶缝扫过石墙
- 墙、地、顶统一用同一种石材，像在山体里凿出的岩洞
- 蒸汽、水雾、水面反射让石面湿润发亮，干处哑光
- 小窗洞高侧窗，光线斜射进暗室，光斑随时间移动

**风格卡**：
- 材质：layered grey quartzite gneiss slabs, rough-hewn local stone, dark stained concrete, wet polished stone surface with water sheen, matte dry stone
- 光线：narrow horizontal skylight band at roof level, raking light grazing across stone layers, steam and water vapor softening the light, low ambient, warm 3000K against cool stone
- 色彩：dominant grey-green stone (#6B6E68), near-black shadow, warm water-reflected highlight, desaturated overall
- 构图：close-up interior detail of stone wall meeting water, low horizon, heavy solid mass overhead, tiny human figure for scale, contemplative stillness
- **EN prompt snippets**：`layered grey gneiss stone walls, thermal bath interior, narrow skylight raking light, steam rising over water, Peter Zumthor atmosphere, monastic silence, wet stone reflections`
- **中文提示词片段**：`层叠灰色片麻岩墙，温泉浴场室内，窄高侧光斜射，蒸汽水面升起，卒姆托式氛围，修道院般沉默，湿润石材反射`

**红线**：不要直接复制瓦尔斯浴场的 15 块巨石体块组合；取"片麻岩层叠+顶缝光+水蒸汽"语法。

**参考**：
- https://www.archiposition.com/items/20180525102501
- https://www.myswitzerland.com/zh-hans/planning/about-switzerland/the-swiss-art-and-culture-scene/contemporary-swiss-architecture/

---

### 5. 路易·康 Louis Kahn

**3 个视觉关键词**：砖拱 / 银之光 / 房间

**核心理念**："房间是建筑的起点"。区分"服务空间"（楼梯、管道、结构塔）与"被服务空间"（人待的房间），让结构诚实受力——砖就该做成拱，混凝土拉杆就该受拉。光从顶部下来，被金属反射器漫反射成全室"银色的光"。

**标志性手法**：
- 巨大砖拱（印度管理学院、孟加拉国会），拱脚处一道暴露的混凝土拉杆
- 天井/天窗在穹顶或屋顶中央开洞，光从顶上下来
- 角部独立方形空心柱（特伦顿浴室），结构同时是入口/储藏
- 厚墙深窗洞，窗洞斜切，光斜射进室内
- 清水混凝土与红砖并置，材料各按天性受力

**风格卡**：
- 材质：exposed red brick with visible mortar joints, board-formed concrete, massive thick walls, cycloid-shaped concrete vault, matte texture
- 光线：top-lit skylight oculus, natural light filtered through perforated metal reflector, "luminosity of silver", raking light through deep reveals
- 色彩：warm terracotta brick (#A0522D), pale sand concrete, silver-grey diffuse light, deep shadow blue in corners
- 构图：symmetrical axial composition, looking up into a vaulted room, deep reveal frames the light, monumental stillness, strong geometric order
- **EN prompt snippets**：`massive red brick arch with exposed concrete tie beam, top-lit cycloid vault, Louis Kahn served and servant spaces, monumental monastic interior, silver diffuse daylight, deep window reveal`
- **中文提示词片段**：`巨大红砖拱配暴露混凝土拉杆，顶部采光摆线拱顶，路易·康式服务/被服务空间，纪念性修道院室内，银色漫射天光，深窗洞斜光`

**红线**：不要直接复刻孟加拉国会的八边形金字塔顶、不要复刻萨尔克庭院的对称序列；取"砖拱+顶光+厚墙"语法。

**参考**：
- https://www.studiomatrx.org/architecture-canon/kimbell-art-museum
- https://50.kimbellart.org/architecture/the-louis-i-kahn-building/

---

## 二、室内设计

### 6. Axel Vervoordt

**3 个视觉关键词**：侘寂 wabi-sabi / 做旧 / 时间痕迹

**核心理念**：把古老器物重新安置、赋予新生命。美在不完美、无常、质朴里。用原木、石材、灰泥保留粗糙肌理，大面积留白，降低饱和度，让空间有历史厚重感和情绪稳定性。

**标志性手法**：
- 墙面手工灰泥/微水泥，带不规则抹痕和色差，不追求平整
- 古董木梁、老木门、残墙碎片直接留在空间里
- 亚麻帘、粗陶、单枝枯枝、一件旧雕塑做点缀
- 墙面留白率 ≥65%，家具占地 ≤30%
- 光从高侧窗或天井斜射，光斑在灰泥墙上缓慢移动

**风格卡**：
- 材质：hand-troweled lime plaster walls with uneven patches, reclaimed oak beams, aged wood, rough travertine, coarse linen fabric, unpolished clay
- 光线：soft oblique daylight from a high small window, dramatic raking light revealing wall texture, low ambient, no artificial light visible
- 色彩：warm greige, raw sienna, weathered taupe, faded bone, all desaturated, single piece of dark patinated bronze as accent
- 构图：very sparse, single antique object centered in empty room, long horizontal composition, visible wall surface dominates, negative space > 60%
- **EN prompt snippets**：`wabi-sabi interior, hand-troweled lime plaster wall, Axel Vervoordt style, reclaimed ancient oak beam, sparse antique ceramic vessel, muted earth tones, oblique raking light, zen stillness, imperfection and patina`
- **中文提示词片段**：`侘寂室内，手工抹痕灰泥墙，Axel Vervoordt 风，回收老木梁，粗陶古器孤件，低饱和大地色，斜射侧光，禅意静止，残缺与包浆`

**红线**：不要变成"做旧家具堆砌"——枯枝+粗陶+亚麻帘全堆上就是淘宝侘寂风；真正的 Vervoordt 是"少而精的古董+大面积空墙"。

**参考**：
- http://m.toutiao.com/group/6281485336306041090/
- https://www.to8to.com/yezhu/z358464.html

---

### 7. Vincent Van Duysen

**3 个视觉关键词**：暖灰极简 / 触觉材质 / 光即材料

**核心理念**：比利时极简主义，但拒绝冷感。光像砖一样是一种建材，用来雕刻情绪。空间在"充满光的房间"和"暗室"之间交替，靠材质触觉（砂岩石、拉丝木、抹灰墙）而非颜色制造温暖。

**标志性手法**：
- 单色暖灰体系（sand / bone / plaster / ash），全屋不超过 3 个色阶
- 墙面 textured plaster 带细微肌理，光一照显纹理
- 宽板白蜡木/橡木地面（lye 处理后浅米色）
- 家具像"微缩建筑"，方正规整，参考 Donald Judd 雕塑
- 一件大号黑色摇臂工业灯（如 Apparatus / VV 自设计）做唯一黑色点

**风格卡**：
- 材质：textured light plaster walls, pale sandstone floor, wide-plank bleached oak, castano walnut volumes, matte linen upholstery, brushed black metal
- 光线：soft north diffuse daylight through tall grid windows, gentle light-shadow balance, no harsh contrast, 3200K warm ambient
- 色彩：monochromatic warm greige palette — bone #D8D2C4, sand #C4B8A4, ash grey #9A958C, single matte black lamp as punctuation
- 构图：long horizontal living room shot, low sofa as horizontal anchor, one abstract artwork on wall, symmetrical off-center composition, tall window grid in background
- **EN prompt snippets**：`Vincent Van Duysen interior, monochromatic warm greige palette, textured plaster walls, bleached oak wide plank floor, low linen sofa, one black articulating floor lamp, nordic-minimalist warmth, tactile materials`
- **中文提示词片段**：`Van Duysen 室内，单色暖灰米色板，肌理抹灰墙，漂白橡木宽板地，低矮亚麻沙发，一盏黑色摇臂落地灯，北欧极简温暖，触觉材质`

**红线**：Vervoordt 是"旧、暗、古董、斑驳"；Van Duysen 是"干净、新、当代、单色"。不要把两者混——不要在 VVD 空间里堆古董和做旧墙。

**参考**：
- https://vincentvanduysen.com/uploads/projects/VVDA_2023_VVD_interview_June_23.pdf
- https://stylishclub.pt/news-media/vincent-van-duysen-the-beauty-of-simplicity/

---

### 8. 如恩设计 Neri&Hu（郭锡恩 + 胡如珊）

**3 个视觉关键词**：新旧并置 / 浇筑混凝土进红砖壳 / 反思型怀旧

**核心理念**：在城市更新中不抹平历史，把老墙剥出红砖、再浇一个新混凝土体块"嵌"进去，新旧不互相覆盖，而是对话。捕捉城市脉络与弄堂记忆，让建筑成为时间的容器。

**标志性手法**：
- 保留旧砖墙，部分剥去白灰露出红砖，部分覆盖新抹灰
- 新浇清水混凝土体块像"模具里倒出来的"，嵌在旧砖墙壳内
- 混凝土偶尔渗出填补旧砖缺口、勾勒新开口
- 垂直弄堂（vertical lane house）：把上海里弄叠起来，天井、砖墙、窄缝空间
- 暴露的黑钢窗、老木门与新混凝土并置

**风格卡**：
- 材质：exposed red brick with peeling white plaster, board-formed cast-in-place concrete, blackened steel windows, weathered wood doors, raw industrial
- 光线：soft courtyard daylight penetrating narrow gaps, interior warm tungsten spots, contrast between rough brick and smooth concrete
- 色彩：weathered brick red-brown (#8B4A3A), raw concrete grey, matte black steel, warm wood — industrial nostalgic palette
- 构图：section-like interior view showing old wall meeting new concrete volume, narrow vertical space, visible construction joint, no polish
- **EN prompt snippets**：`Neri&Hu adaptive reuse, exposed red brick wall meeting cast-in-place concrete volume, peeling plaster revealing brick, black steel window, shanghai lane house typology, raw material honesty, old and new dialogue`
- **中文提示词片段**：`如恩式城市更新，裸露红砖墙与现浇混凝土体块并置，剥灰露砖，黑钢窗，上海里弄类型，材料诚实，新旧对话`

**红线**：不要把如恩做成"网红红砖咖啡馆"——真如恩有明确的新旧构造逻辑（混凝土嵌进砖壳），不是贴一层红砖皮。

**参考**：
- https://neriandhu.com/en/works/recast-lao-ding-feng-beijing
- https://www.architecturalrecord.com/articles/8259-the-waterhouse-at-south-bund

---

### 9. 琚宾 / 水平线设计 Horizontal Design

**3 个视觉关键词**：东西融合 / 宋韵留白 / 水墨灰度

**核心理念**：把中国文化（园林、水墨、宋瓷）用当代材料重述，"没有花木，依然成园林"。在灰、白、朦胧中模糊建筑与室内的界限，用镜面、绢布、宣纸建构迂回路径，让空间像一幅展开的水墨长卷。

**标志性手法**：
- 灰白灰阶体系，半透绢布/宣纸隔断做空间分隔
- 灰砖排序富于层次变化，回应传统瓦墙
- 镜面、水面、半透材料制造"模糊纵深"
- 艺术品沿凹龛序列排布，形成东西文化对话长廊
- 路径迂回曲折，曲径通幽，不一眼望穿

**风格卡**：
- 材质：grey brick with varied coursing, translucent silk and rice-paper screens, brushed stainless mirror, pale micro-cement, dark walnut furniture
- 光线：diffused soft ambient, no direct sunbeam, gentle shadowless light, paper-like glow, warm 3000K
- 色彩：dominant ink-wash greys — paper white, rice paper beige, ink grey #6B6B6B, cinnabar red as single accent, celadon green
- 构图：long axial corridor view, half-transparent screen framing a blurred background, asymmetric composition, large blank wall area, garden borrowed scenery
- **EN prompt snippets**：`Ju Bin horizontal design, contemporary Chinese ink-wash interior, translucent rice-paper screen, layered grey brick wall, curved winding corridor, zen garden atmosphere, muted monochrome with one cinnabar accent, Song-dynasty minimalist aesthetic`
- **中文提示词片段**：`琚宾水平线设计，当代中国水墨室内，半透宣纸隔断，层次灰砖墙，迂回长廊，禅意园林氛围，低饱和单一点朱砂，宋代极简审美`

**红线**：不要变成中式符号堆砌（红灯笼、太师椅、雕花）；琚宾是"用当代材料转译宋韵"，不是抄明清符号。

**参考**：
- https://www.cnhorizontal.com/cn/works/164.html
- https://c.m.163.com/news/a/JQ21D7D7051285HS.html

---

## 三、平面 / 视觉设计

### 10. 原研哉 Kenya Hara

**3 个视觉关键词**：白 / 空（emptiness）/ 纸张触感

**核心理念**：白不是颜色的空白，是能容纳所有想象的"信息容器"。"空"不是西方极简的"删到功能清晰"，而是"删到让使用者自己填入意义"。设计让观者在看到的瞬间自己觉醒，不靠文字解释。

**标志性手法**：
- 大面积米白/本白（不是纯白 #FFFFFF，是带温度的纸白 #F5F1E8）
- 一张地平线照片（地平线横贯画面下 1/3）作为 MUJI 广告母题
- 极细无衬线字体，大留白，文字只占版面 10%
- 纸张触感/触觉主题（HAPTIC 展）：鸡蛋、棉花、凹版纸
- 不做装饰，让"日常"本身成为美感

**风格卡**：
- 材质：matte uncoated paper texture, soft off-white stock, subtle fiber grain, embossed detail, no gloss
- 光线：flat even studio light, no shadow, paper-white seamless background, neutral 5500K
- 色彩：paper off-white (#F5F1E8), ink black text, single muted photo element, zero saturation accents
- 构图：extreme negative space (≥70%), one single centered image or horizon line, ultra-thin typography at corner, symmetrical calm
- **EN prompt snippets**：`Kenya Hara MUJI style, vast off-white negative space, single horizon line photograph, ultra-minimal Japanese graphic design, tactile paper texture, quiet emptiness, "emptiness not simplicity", soft diffuse light`
- **中文提示词片段**：`原研哉无印良品风，大面积本白留白，单张地平线照片，极简单日本平面设计，纸张触感，静谧空的哲学，空而非简，柔和漫射光`

**红线**：不要直接挪用 MUJI 地平线广告那张秘鲁盐湖照片、不要复制无印良品的宋体 logo；取"白+空+地平线"语法。

**参考**：
- https://www.muji.com.cn/cn/net/feature/shop/flagship/huaihai755/archive/hara.html
- https://blakecrosley.com/blog/design-philosophy-kenya-hara

---

### 11. 佐藤可士和 Kashiwa Sato

**3 个视觉关键词**：超级符号 / 超整理术 / 三色明快

**核心理念**：把品牌压缩成一个一眼可识别的符号——"强识别就是一个 icon"。先整理空间、信息、思考，剥到本质，再用一个符号、一种颜色、一句话跨语言传达。明快、冲击力、不暧昧。

**标志性手法**：
- 一个核心符号（Uniqlo 红方块、SMAP 三色旗、Samurai 黄黑武士）贯穿所有触点
- 原色对比：红/黄/蓝/黑，高饱和，硬边
- 统一外框把同类信息塞进去，标签分类
- 字体大、粗、黑，居中或贴边，强对比
- 画面干净到只剩符号+一句话，没有装饰

**风格卡**：
- 材质：flat solid color fields, no texture, no gradient, sharp vector edges, matte print on white stock
- 光线：flat graphic, no lighting, even print reproduction
- 色彩：primary red #E60012 + yellow #FFD500 + blue #0057B7 + black on white, high saturation, hard contrast
- 构图：single bold symbol centered, massive white margin, one line of bold sans-serif, symmetrical, immediate readability at 10 meters
- **EN prompt snippets**：`Kashiwa Sato iconic branding, single bold geometric symbol, primary red yellow blue color blocks, flat graphic design, hard-edge vector, ultra-minimal Japanese pop, bold sans-serif typography, "super-organization" method, instant recognition`
- **中文提示词片段**：`佐藤可士和超级符号，单一醒目几何图形，原色红黄蓝色块，平面设计，硬边矢量，日系波普，粗黑体大字，超整理术，一眼识别`

**红线**：不要直接画优衣库红方块 logo、不要复刻 SMAP CD 三色旗；取"单符号+三原色+硬边"语法，不要复制具体品牌标志。

**参考**：
- https://blakecrosley.com/blog/design-philosophy-kashiwa-sato
- https://kashiwasato.com/profile

---

## 四、建筑可视化表现

### 12. MIR（MIR Renderings, Norway）

**3 个视觉关键词**：电影级 / 蓝调时刻 / 大气故事感

**核心理念**：不做"干净广告级超写实"，而做有天气、季节、记忆、人存在的诗意画面。每张图像电影一帧，传达场所的情绪而非仅展示建筑。与 Snøhetta、隈研吾等合作。

**标志性手法**：
- 黄昏蓝调时刻（blue hour）：天空深蓝紫渐变，室内暖橙光从玻璃透出，冷暖强对比
- 大气透视：薄雾、轻烟、远处建筑褪色
- 水面反射：建筑倒影占画面下 1/3
- 人物是小黑点，成组聚集或独步，有生活感
- 季节感：雪、落叶、雾、长影，画面不"完美干净"

**风格卡**：
- 材质：hyperrealistic PBR materials, wet asphalt reflection, snow-dusted concrete, glass curtain wall with warm interior glow, cinematic depth
- 光线：blue-hour dusk sky (#1E3A5F to #4A6B8A gradient), warm interior 2700K spilling out, long soft shadows, atmospheric haze
- 色彩：dominant cool blue-teal sky, single warm amber interior glow as accent, desaturated overall, cinematic teal-orange grade
- 构图：wide establishing shot, building 1/3 frame, foreground water/snow/plaza reflecting, tiny human figures, horizon low, anamorphic widescreen feel
- **EN prompt snippets**：`MIR style architectural visualization, blue-hour dusk, warm interior glow through glass facade, atmospheric mist, water reflection, tiny silhouetted people, cinematic wide shot, hyperrealistic rendering, Nordic poetic mood, teal and orange cinematic grade`
- **中文提示词片段**：`MIR 建筑可视化风，黄昏蓝调时刻，室内暖光从玻璃透出，大气薄雾，水面反射，小人剪影，电影感宽幅，超写实渲染，北欧诗意氛围，青橙电影调色`

**红线**：不要直接抄 Snøhetta 奥斯陆歌剧院的白色斜面屋顶那张 MIR 成名图；取"蓝调+暖光+水面+人影"语法，换建筑主体。

**参考**：
- https://mrrendering.com/architectural-rendering-companies/

---

### 13. Alex Hogrefe（Visualizing Architecture）

**3 个视觉关键词**：手绘草图 / 叙事剖面 / 抽象撞色

**核心理念**：早期设计阶段的表达不是拍照，而是"带着观点的图"。通过笔触、色块、分层叠加、夸张色彩把设计概念讲清楚，用风格化（stylization）而非写实来突出想法。

**标志性手法**：
- 建筑本体用白/浅灰块面，像黏土模型
- 地面/环境用高饱和撞色（朱砂红、钴蓝、橙）做抽象色块
- 笔刷纹理/图层叠加感明显，可见笔触
- 剖面图带人物、树、活动，叙事性强
- 背景留白或淡天空，不做完整环境渲染

**风格卡**：
- 材质：digital painting brushstrokes, visible texture layers, flat color blocks, white massing model, watercolor-and-ink hybrid
- 光线：flat illustrative lighting, no photorealistic shadows, simple shade under eaves, even diagrammatic
- 色彩：white building mass + bold saturated ground (cinnabar red, cobalt blue, burnt orange), high contrast between clean architecture and abstract field
- 构图：axonometric or eye-level section, building as white volume, abstract color field as ground, minimal context, visible painterly texture
- **EN prompt snippets**：`Alex Hogrefe style conceptual illustration, white massing model building on abstract cinnabar-red and cobalt-blue ground, visible digital brushstrokes, stylized architectural concept diagram, painterly layered texture, not photorealistic, narrative axonometric, bold color blocking`
- **中文提示词片段**：`Alex Hogrefe 概念插画风，白色体块建筑置于朱砂红与钴蓝抽象地面，可见数字笔触，风格化建筑概念图，绘画图层质感，非写实，叙事轴测图，大胆色块`

**红线**：不要做成"水彩钢笔淡彩小清新"——Hogrefe 的力量来自白建筑+高饱和抽象地面的强对比，不是温柔水彩。

**参考**：
- https://visualizingarchitecture.com/abstract-illustrations-part-2/
- https://www.maxon.net/fr/article/architectural-rendering-techniques

---

## 速查表：风格速配

| 想要的感觉 | 用谁的后缀 |
|---|---|
| 混凝土+一束光的禅意 | 安藤忠雄 |
| 未来感流线白建筑 | 扎哈 |
| 木格栅+融于自然的酒店 | 隈研吾 |
| 石温泉/修道院沉默感 | 卒姆托 |
| 砖拱+顶光的纪念性空间 | 路易·康 |
| 旧古董+斑驳灰泥的侘寂 | Vervoordt |
| 干净暖灰极简样板间 | Van Duysen |
| 红砖+混凝土改造空间 | 如恩 |
| 宋韵水墨东方酒店 | 琚宾 |
| 品牌海报/极简留白 | 原研哉 |
| 品牌主视觉/超级符号 | 佐藤可士和 |
| 建筑效果图黄昏电影感 | MIR |
| 方案阶段概念草图 | Alex Hogrefe |
