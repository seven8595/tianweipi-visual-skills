# 风格变体 Prompt Patch

所有变体都基于 SKILL.md 第 8 节的"母 prompt"做**最小替换 / 追加**，不要整张重写。使用方法：
1. 先把母 prompt 粘出来。
2. 按用户选定的风格，替换下表中的对应段落。
3. 在末尾追加"附加关键词块"。
4. 负向 prompt 保持不变，按风格补充 1–2 个词。

---

## A. 现代高端（默认，母 prompt 本身就是）
- 适用：城市核心区、招商提案、高端地产
- 关键词：blue hour, stone cladding, glass curtain wall, brushed metal, warm 3000K light, restrained luxury
- 人流密度：medium

## B. 年轻潮流街区
- 适用：Z 世代、亚文化、潮牌集合、文创园改造
- **替换**建筑段：`concrete and exposed brick facades, spray-paint murals on side walls, pop-up kiosks, container-style storefronts, neon signs in limited spots, oversized fashion display windows, skate-able plinth`
- **追加**：`street art murals, colorful graffiti, skateboarders, young crowd in streetwear, selfie tourists, vinyl record shop, sneaker store, coffee roaster, plants in tire planters, warm string lights, lively social atmosphere`
- 人流密度：medium-high
- 负向追加：`empty street, boring architecture`

## C. 夜经济街区
- 适用：餐饮夜市、酒吧街、深夜食堂
- **替换**时间：`late night, deep indigo sky, street fully lit, restaurant facades glowing`
- **追加**：`outdoor dining terraces fully occupied, food steam rising from hotpot restaurants, bar entrances with warm pendant lights, people dining and drinking at long tables, lanterns, food stalls, menu boards in Chinese, lively night market vibe, moderate neon signs`
- 人流密度：high
- 负向追加：`empty tables, closed shops`

## D. 文旅商业街（古镇 / 旅游目的地）
- 适用：文旅小镇、古城步行街、景区商业
- **替换**建筑：`traditional Chinese tiled roof overhangs, timber columns, grey brick walls, lanterns hanging under eaves, stone slab pavement, wooden shop signs with handwritten calligraphy`
- **追加**：`tourists in casual summer wear, souvenir shops, tea houses, traditional snack stalls, red lanterns, wooden facade carvings, misty evening, warm yellow lantern light, cultural tourism atmosphere`
- 注意：不要写成纯中式（见 G 新中式）；文旅 = 传统 + 现代商业混合。

## E. 滨水商业街
- 适用：运河、江景、湖畔、港口商业
- **追加**：`canal or river on one side, wooden promenade railing, reflection of buildings in water, passing sightseeing boat, waterfront dining terraces, weeping willows, evening breeze, water ripples`
- **构图**：一侧建筑 + 一侧水面，不要两排建筑夹路。

## F. 下沉广场商业
- 适用：综合体地下一层、地铁上盖、中庭下沉
- **替换**空间：`sunken plaza shopping center, 3 level circular atrium, escalators connecting ground floor to sunken level, glass skylight above, shops wrapping around the sunken courtyard, green terraces`
- **机位**：从地面层往下俯视 30°，不是街眼高度。
- **追加**：`natural daylight from skylight mixing with warm shop lights, people walking down stairs, central fountain or installation`

## G. 新中式商业街
- 适用：高端中式商业、茶文化、江南意境
- **替换**建筑：`modern reinterpretation of Chinese architecture, grey tiled pitched roofs simplified into geometric forms, large glass panels with dark steel frames, timber lattice screens, water feature in courtyard, minimalist Chinese lanterns`
- **追加**：`ink-wash aesthetic, quiet and refined, pine trees in planters, stone lanterns, restrained color palette (charcoal, grey, wood, off-white), tea house, bookshop, incense shop`
- 注意：是"新"中式，不要雕梁画栋。

## H. 日式商业街（京都 / 东京下町）
- **替换**：`narrow pedestrian shopping street, low 2-story wooden and plaster storefronts, noren fabric curtains at entrances, paper lanterns, small izakaya, coffee shop, fluorescent strip lights under eaves, dense power lines overhead`
- **追加**：`pedestrian only, narrow lane, warm yellow tungsten light, locals walking, evening commute vibe, retro Japan Showa atmosphere`

## I. 欧式商业街（意大利 / 法式）
- **替换**：`European arcade shopping street, stone facades with cornices and pilasters, wrought iron balconies, café awnings in red or striped, gas-style street lamps, arched doorways`
- **追加**：`cobblestone pavement, outdoor Parisian café seating, people sipping espresso, warm 2700K tungsten light, romantic evening, refined European charm`

## J. 赛博朋克商业街
- **替换**：`neon-drenched cyberpunk street, wet reflective asphalt, holographic ads on building facades, vertical megasigns in Chinese and Japanese, mix of futuristic glass and gritty concrete, fog and light haze`
- **追加**：`magenta, cyan and orange neon reflections, dense rain, people with umbrellas, flying vehicles in distant sky, high contrast between neon glow and dark shadows`
- 负向追加：`pastel colors, daylight`
- 注意：本变体与"高端"调性冲突，不要默认用。

## K. 社区商业（邻里中心）
- **替换**：`neighborhood community commercial street, low-rise 2-story buildings, grocery store, bakery, pharmacy, childcare, small restaurant, casual and welcoming`
- **追加**：`families with kids, elderly residents walking, after-school crowd, bright clean facade, soft daylight or early evening, moderate density, everyday life atmosphere`
- 人流密度：medium-low

## L. 城市更新商业街（旧厂房 / 老街区改造）
- **替换**：`adaptively reused industrial heritage buildings, exposed red brick, weathered concrete, steel windows, inserted glass volumes, rooftop addition, signage integrated into original brick`
- **追加**：`creative office, design studio, specialty coffee, independent bookstore, plants climbing on brick, industrial chic, raw and authentic textures`

---

## 使用顺序
1. 先和用户确认走哪一类（A–L）。
2. 把母 prompt 对应段替换。
3. 追加该变体的附加关键词块。
4. 负向 prompt 默认 SKILL.md 第 8 节那套，再补 1–2 个变体专属负向词。
5. 出图后按 SKILL.md 第 11 节 QA。
