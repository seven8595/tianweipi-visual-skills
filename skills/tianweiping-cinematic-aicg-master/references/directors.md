# 导演视觉签名库（Director Visual Signatures）

把每位导演的"视觉签名"拆成可直接拼到 AI 视频提示词里的参数。每位导演按统一字段描述：
构图 / 色彩 / 光影 / 运镜 / 空间 / 典型符号 / 雷区 / 可复用 prompt 片段。

目录：
- [Wes Anderson 韦斯·安德森](#wes-anderson-韦斯安德森)
- [Wong Kar-wai 王家卫](#wong-kar-wai-王家卫)
- [Christopher Nolan 诺兰](#christopher-nolan-诺兰)
- [Akira Kurosawa 黑泽明](#akira-kurosawa-黑泽明)
- [Jean Renoir 让·雷诺阿](#jean-renoir-让雷诺阿)
- [Stanley Kubrick 库布里克](#stanley-kubrick-库布里克)
- [Roger Deakins（DP）罗杰·迪金斯](#roger-deakinsdp罗杰迪金斯)
- [Denis Villeneuve 维伦纽瓦](#denis-villeneuve-维伦纽瓦)
- [Andrei Tarkovsky 塔可夫斯基](#andrei-tarkovsky-塔可夫斯基)
- [Bong Joon-ho 奉俊昊](#bong-joon-ho-奉俊昊)
- [Hirokazu Kore-eda 是枝裕和](#hirokazu-kore-eda-是枝裕和)
- [David Fincher 大卫·芬奇](#david-fincher-大卫芬奇)
- [Ridley Scott 雷德利·斯科特](#ridley-scott-雷德利斯科特)
- [场景→导演速查表](#场景导演速查表)

---

## Wes Anderson 韦斯·安德森

**一眼签名**：对称童话盒子、复古糖果色、舞台剧式精确布景。

- **构图**：极致中心对称；人物永远钉在画面正中或绝对几何点；左右严格平衡；正面平视机位；大量正俯视（top-down）。
- **色彩**：粉彩复古调色盘——脏粉、芥末黄、鼠尾草绿、婴儿蓝、砖红；整帧限 2–3 个主色，不杂色。
- **光影**：平光、均匀、少硬阴影；像橱窗/玩偶屋；没有戏剧性明暗切割。
- **运镜**：正面 dolly-in / dolly-out 直推直拉；90° 垂直横移（tracking sideways）；慢速对称升降；绝不手持。
- **空间**：房间像布景板，家具、道具、人物站位全部对齐画面网格；每样东西都"被安排"。
- **典型符号**：复古制服/校服、斜体英文卡片字幕、飞船/火车/博物馆、宠物狗、扁平地形、对称花园。
- **雷区**：不要斜角手持、不要混乱构图、不要高饱和霓虹、不要自然主义光影。
- **prompt 片段**：
  > "perfectly symmetrical centered composition, flat frontal lighting, pastel retro palette (dusty pink / mustard yellow / sage green), dollhouse-like set design, static camera with slow straight dolly-in, Wes Anderson style, whimsical storybook tone."

---

## Wong Kar-wai 王家卫

**一眼签名**：色彩替人物说话、遮挡制造距离、慢门拖影。

- **构图**：不追求稳；人物常被门框/玻璃/雨丝/前景植物"切"住；画面故意挤、故意堵。
- **色彩**：
  - 红 = 欲望、危险、热烈（酒吧、霓虹巷、旗袍）
  - 绿 = 疏离、不安、怀旧（旧公寓、雨夜）
  - 蓝 = 孤独、距离、冷战
  - 黄/琥珀 = 回忆、年代感
- **光影**：霓虹混合钨丝灯；强烈色溢（color spill）；烟雾/雨/磨砂玻璃柔化边缘；暗部偏青绿。
- **运镜**：手持轻晃；慢动作 + 动态拖影（motion blur）表现记忆/情绪；人物擦镜头而过；偶尔 12–18fps 抽帧感。
- **空间**：狭窄走廊、电话亭、出租车后座、雨夜街口；前景永远挡点什么。
- **典型符号**：挂钟、路灯、雨、霓虹招牌、香烟、旗袍/西装、擦肩而过、凤梨罐头、暧昧独白旁白。
- **雷区**：不要明亮日间、不要清爽白底、不要整齐对称、不要快切动作片节奏。
- **prompt 片段**：
  > "Wong Kar-wai mood, neon-tinged night street, shallow depth of field, foreground rain streaks / glass reflections blocking half frame, color-spilled lighting (emerald green + crimson red), slow motion with motion blur, melancholic nostalgic atmosphere, 1960s Hong Kong, hazy film grain."

---

## Christopher Nolan 诺兰

**一眼签名**：IMAX 巨物压迫、冷蓝金属质感、交叉剪辑的时间张力、实拍级物理重量。

- **构图**：低角度仰拍巨物（飞机/建筑/炸弹/海浪）；宽画幅塞满天际线；人物在巨大环境中占极小比例。
- **色彩**：冷蓝、钢灰、沙黄、军绿；低饱和；金属高光硬。
- **光影**：硬光、强对比；夜景多用火光/爆炸/手电做唯一光源；昼景则是阴天漫射冷光。
- **运镜**：IMAX 实拍感——手持追拍、跟跑、紧凑过肩对话；少 CG 漂浮感；镜头"有重量"。
- **空间**：狭窄走廊、时间胶囊、机舱、战场、潮汐海岸；空间本身就是谜题。
- **典型符号**：旋转走廊、折叠城市、潮汐浪、钟表、西装、定时炸弹、黑板数学、多线交叉。
- **雷区**：不要糖果色、不要卡通化、不要平滑 CG 推拉、不要过度滤镜。
- **prompt 片段**：
  > "Christopher Nolan IMAX look, low-angle shot of a massive wave / structure dwarfing a lone figure, cold desaturated steel-blue palette, hard directional light, handheld chase cinematography, practical explosive lighting, epic tense atmosphere, shot on 70mm film grain."

---

## Akira Kurosawa 黑泽明

**一眼签名**：三角人物调度、风雨天气、正面迎击、动态长镜。

- **构图**：画面用 3 点人物排布（三角构图）；正面群像列队；大量风把草/旗/衣吹向同一方向。
- **色彩**：早期黑白高反差；彩色后期偏自然大地色（红披风、黄麦田、青竹林）。
- **光影**：正午硬顶光、雨后湿地面反光；门内门外光明暗切。
- **运镜**：机位常在腰高正面对峙；动作段落用长镜头+快速切；风镜头必慢。
- **空间**：竹林、麦田、城门、泥泞战场；纵向纵深极强。
- **典型符号**：武士、佩剑、草帽、旗帜、风、雨、泥泞、七人列队。
- **雷区**：不要赛博霓虹、不要手持抖到看不清动作、不要过度慢动作。
- **prompt 片段**：
  > "Kurosawa-style samurai standoff, three-point triangular blocking, strong wind blowing grass and cloaks, wet muddy ground reflections, frontal symmetrical framing, dynamic long take, epic feudal Japanese atmosphere, high contrast natural light."

---

## Jean Renoir 让·雷诺阿

**一眼签名**：诗意现实主义、镜头穿过真实生活、温柔的景深。

- **构图**：门框/窗套作为自然画框；人物在画面里走动而不是摆 pose；景深大，前中后景同时有人活动。
- **色彩**：战后法式棕、土黄、旧墙绿；低饱和、生活气。
- **光影**：自然光为主；窗光斜切；不打戏剧光。
- **运镜**：流畅的长镜头推轨；人物进进出出画框；像跟着一个人在街上走。
- **空间**：乡间庄园、河岸边、小酒馆、战时法国街道；空间有生活痕迹。
- **典型符号**：河流、野餐、旧式西装、窗户、门帘、普通人的尊严。
- **雷区**：不要网红滤镜、不要摆拍感、不要夸张打光。
- **prompt 片段**：
  > "French poetic realism, deep focus composition through a doorway, natural window light, muted earthy palette (ochre / moss green / worn brown), gentle tracking long take, everyday people in a 1930s riverside village, warm humanist tone."

---

## Stanley Kubrick 库布里克

**一眼签名**：一点透视走廊、中心消失点、冰冷对称、神视角。

- **构图**：极端一点透视（one-point perspective）；走廊/教堂/长桌把视线钉到消失点；正俯视上帝视角。
- **色彩**：猩红（The Shining）、深蓝墨绿（2001）、医院冷白；高饱和主色压住全场。
- **光影**：对称布光；强明暗；霓虹+镜面反射；空间像手术台。
- **运镜**：极平稳的 dolly/steadicam 慢速推进；像幽灵飘过去；绝不手持。
- **空间**：无尽走廊、迷宫地毯、太空舱、象棋棋盘、黑白方格地砖。
- **典型符号**：镜子反射、婴儿脸、象棋、红星、地毯图案、门缝窥视。
- **雷区**：不要晃、不要暖融融的日常感、不要杂乱。
- **prompt 片段**：
  > "Kubrick one-point perspective corridor, perfect symmetrical vanishing point, slow ghostly dolly-in, stark single-color palette (blood red on deep teal), geometric tiled floor, cold ominous atmosphere, voyeuristic framing."

---

## Roger Deakins（DP）罗杰·迪金斯

**一眼签名**：极简构图、雾霾蓝、单光源、干净到冷酷。

- **构图**：大留白；人物常放在画面 1/3 甚至边角；地平线压低或抬高。
- **色彩**：雾霾蓝（haze blue）、晨雾灰、沙漠金；整帧往往只有冷暖两个色。
- **光影**：单方向自然光；晨雾/黄昏；轮廓光干净；数字打光极克制。
- **运镜**：1917 式一镜到底长跟；或极度克制的固定镜头。
- **空间**：开阔荒原、一战战壕、西部峡谷、伦敦雾夜；空气感强。
- **典型符号**：火光、战壕、雾、火车、孤树、晨光。
- **雷区**：不要多光源花哨打光、不要高饱和、不要噪点堆砌。
- **prompt 片段**：
  > "Roger Deakins cinematography, minimal composition with vast negative space, single natural light source, hazy desaturated blue tone, thin morning fog, lone figure in an open landscape, quiet epic atmosphere, anamorphic lens flare."

---

## Denis Villeneuve 维伦纽瓦

**一眼签名**：巨型纪念碑、薄雾、慢推、宗教式敬畏。

- **构图**：巨物压迫人物（沙丘、母舰、纪念碑）；对称或极简；人物小小一个。
- **色彩**：沙漠橙红 + 冷蓝阴影；夜戏近乎单色；高对比但柔。
- **光影**：体积光（god rays）穿过雾；逆光剪影；低照度。
- **运镜**：极慢推、极慢拉；镜头像在朝拜；少剪辑。
- **空间**：沙漠、外星遗迹、未来巨城、浓雾废墟；空气里有颗粒。
- **典型符号**：沙虫、母舰、黑混凝土、黑袍、雾、仪式感。
- **雷区**：不要快速切、不要 comedy 节奏、不要鲜艳卡通。
- **prompt 片段**：
  > "Denis Villeneuve scale, slow deliberate dolly-in toward a colossal monolith, tiny silhouetted figure in foreground, volumetric light through thin desert haze, burnt orange sky with cold blue shadows, sacred meditative sci-fi atmosphere, Dune-esque epic."

---

## Andrei Tarkovsky 塔可夫斯基

**一眼签名**：长镜头、雨、火、水反射、怀旧棕绿。

- **构图**：画面像油画；故意不对中；水面/镜面反射叠层。
- **色彩**：棕、墨绿、锈黄、灰白；低饱和到褪色。
- **光影**：窗光、烛光、火光；大面积暗部；阴影有重量。
- **运镜**：极慢横移/推拉；一个镜头几十秒；时间在画面里流动。
- **空间**：旧俄罗斯木屋、雨中森林、泥泞田野、旧教堂；永远潮湿。
- **典型符号**：雨、火、蜡烛、水洼反射、马、旧书、风吹窗帘。
- **雷区**：不要快节奏、不要电子霓虹、不要现代都市标签。
- **prompt 片段**：
  > "Tarkovsky style, long contemplative take, rain on old wooden window, candle flame reflection in a puddle, faded sepia and moss-green palette, soft overcast window light, meditative slow cinema, water and fire motifs."

---

## Bong Joon-ho 奉俊昊

**一眼签名**：高低机位切阶层、楼梯透视、灰蓝首尔。

- **构图**：楼梯/坡道把人物切成上下层；俯拍穷人、仰拍富人；几何透视强烈。
- **色彩**：半地下室的霉绿 vs 豪宅的米白；雨夜冷蓝。
- **光影**：半地下室低照度；豪宅大落地窗自然光；雨夜景湿反光。
- **运镜**：流畅长镜头穿过走廊/楼梯；偶尔疯狂横移。
- **空间**：楼梯、地下室、豪宅客厅、地铁、山坡；空间本身就是阶级隐喻。
- **典型符号**：楼梯、半地下室、石头、桃子、下雨、披萨店、地下室灯。
- **雷区**：不要纯文艺、不要纯搞笑；类型片节奏+社会讽刺并存。
- **prompt 片段**：
  > "Bong Joon-ho framing, extreme low-angle vs high-angle cut between upstairs and downstairs, stairwell perspective, cold Seoul rainy night, cramped semi-basement greenish light vs bright mansion window light, class satire atmosphere."

---

## Hirokazu Kore-eda 是枝裕和

**一眼签名**：自然光家庭日常、暖黄浅焦、不煽情。

- **构图**：生活流手持轻晃；人物常在厨房/餐桌/院子；框中框（从门外拍屋内）。
- **色彩**：暖黄、米白、番茄红、木色；低对比、舒服。
- **光影**：窗边自然光；午后阳光斜切；不补戏剧光。
- **运镜**：固定中景为主；轻轻跟；人物自然出画入画。
- **空间**：小独栋、厨房、洗衣场、海边、老家；道具全是用过的旧物。
- **典型符号**：饭团、洗衣、晾衣绳、夏天风铃、海边、兄妹。
- **雷区**：不要大悲大喜、不要炫技运镜、不要强戏剧光。
- **prompt 片段**：
  > "Kore-eda family drama, soft natural window light in a small Japanese kitchen, warm yellow domestic palette, medium static framing, everyday quiet moment around a dining table, gentle shallow depth of field, summer afternoon, understated humanist tone."

---

## David Fincher 大卫·芬奇

**一眼签名**：冷青低饱和、精确运镜、数字级控制。

- **构图**：人物常在画面边缘；故意不对称但稳定；阴影切脸。
- **色彩**：青灰、墨绿、办公室冷白；低饱和到接近单色。
- **光影**：低调照明（low-key）；硬阴影切脸；夜戏只有屏幕光/台灯。
- **运镜**：极精确的慢推/慢拉；一个镜头拍 50 次那种控制感；绝不乱晃。
- **空间**：办公室、暗巷、地下室、数据库；现代都市冷感。
- **典型符号**：电脑屏幕光、雨伞、西装、雨夜、绿屏幕、文字信息。
- **雷区**：不要暖黄怀旧、不要手持纪录片感、不要喜剧光。
- **prompt 片段**：
  > "David Fincher look, cold desaturated teal-and-gray palette, low-key lighting with shadow cutting half the face, precise slow dolly-in, quiet tense modern office at night, only monitor glow on face, meticulous controlled composition."

---

## Ridley Scott 雷德利·斯科特

**一眼签名**：烟雾剪影、金色 hour、史诗广告片质感。

- **构图**：人物逆光大剪影；大量烟雾/尘；宽画幅要塞满天际线。
- **色彩**：金橙落日 vs 深蓝夜；金属反射；广告级调色。
- **光影**：逆光轮廓、体积光、烟雾中丁达尔；单方向硬光。
- **运镜**：史诗级横移；战车/人群移动；慢动作英雄镜头。
- **空间**：沙漠、罗马军团、未来都市、ALIEN 走廊；永远有烟。
- **典型符号**：逆光剪影、烟雾、旗帜、马群、未来高楼、机甲。
- **雷区**：不要小清新、不要手持纪实、不要干净白底。
- **prompt 片段**：
  > "Ridley Scott epic, backlit silhouettes through thick desert smoke, golden-hour volumetric light, sweeping wide tracking shot, army / chariots / futuristic column, hero slow-motion, cinematic commercial grade, dust particles in air."

---

## 场景→导演速查表

| 你想拍的场景 | 首选导演 | 备选 |
|---|---|---|
| 童话感 / 广告 / 玩具风 / 对称可爱 | Wes Anderson | 库布里克 |
| 暧昧 / 夜戏 / 怀旧 / 情绪向 MV | 王家卫 | 是枝裕和 |
| 战争 / 巨物 / 时空谜题 / 硬核预告 | 诺兰 | 维伦纽瓦 |
| 武士对峙 / 古风 / 群像调度 | 黑泽明 | 雷德利·斯科特 |
| 乡村 / 日常人文 / 长镜头生活流 | 让·雷诺阿 | 是枝裕和 |
| 恐怖 / 悬疑 / 几何压迫 / 心理惊悚 | 库布里克 | 大卫·芬奇 |
| 荒原 / 一战 / 西部 / 极简史诗 | 罗杰·迪金斯 | 维伦纽瓦 |
| 科幻巨物 / 外星 / 纪念碑感 | 维伦纽瓦 | 雷德利·斯科特 |
| 文艺 / 长镜头 / 雨火 / 诗意 | 塔可夫斯基 | 让·雷诺阿 |
| 阶级 / 都市讽刺 / 楼梯空间 | 奉俊昊 | 大卫·芬奇 |
| 家庭 / 夏日 / 治愈 / 日常 | 是枝裕和 | 让·雷诺阿 |
| 犯罪 / 现代都市 / 冷峻精密 | 大卫·芬奇 | 罗杰·迪金斯 |
| TVC 广告 / 英雄产品 / 史诗品牌片 | 雷德利·斯科特 | Wes Anderson |

## 拼接 prompt 的通用顺序

生成视频提示词时按这个顺序串：
`[景别+机位] + [人物/主体动作] + [导演签名：构图/色彩/光影/运镜] + [空间/符号] + [氛围词] + [镜头规格：35mm / anamorphic / IMAX / film grain]`
