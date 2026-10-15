# 提示词槽位表 + 三套现成模板

> 原则：**一个槽位只放一件事。** 写成一大段抒情文字，模型只能靠猜。
> 同场景多镜头：**只改【主体】和【动作】，其余逐字复制。**

---

## 1. 槽位取值表

### 景别 shot
| 中文 | 英文 token | 画面占比 |
|---|---|---|
| 大远景 | extreme wide shot, tiny subject in vast landscape | 主体 <5% |
| 远景 | wide shot, subject in full environment | 10% |
| 全景 | full shot, whole body visible | 30% |
| 中景 | medium shot, waist up | 50% |
| 中近景 | medium close-up, chest up | 65% |
| 近景 | close-up, head and shoulders | 75% |
| 特写 | close-up, face or object fills frame | 90% |
| 大特写 | extreme close-up, macro detail | 100% |
| 微距 | macro shot, texture fills the frame | 100%（材质） |

### 机位 angle
`平视 eye-level`／`俯视 high angle looking down`／`仰视 low angle looking up`／
`过肩 over-the-shoulder`／`主观 first-person POV`／`顶俯 top-down bird's eye`／
`荷兰角 dutch tilt`／`背面 from behind`

### 焦段 lens
`14` 超广角强透视／`24` 广角／`35` 纪实自然／`50` 标准无畸变／
`85` 人像柔压缩／`135` 长焦强压缩／`微距` 100mm macro

### 光圈 aperture
`1.4` 纸薄景深／`2` 浅景深／`2.8` 柔和分离／`4` 中等／`5.6` 平衡／`8` 深焦／`11` 全清晰

### 光位 light
`顺光 flat frontal`／`侧光 side light, strong form shadow`／
`侧逆光 rim light from behind-side, glowing edge`／`逆光 backlit, silhouette edge glow`／
`顶光 top light, dramatic shadow`／`窗光 soft window light from one side`／
`柴火 warm firelight from below`／`烛光 candlelight, small warm pool`／
`阴天 overcast diffuse light, no hard shadow`／`黄金时刻 golden hour, long warm shadow`／
`蓝调 blue hour, cool ambient`／`棚拍 studio softbox, even clean light`

### 色温 wb
`暖 2800-3400K`／`暖中性 4200K`／`中性 5600K`／`冷中性 6500K`／`冷 7500-9000K`

### 质感 texture
`胶片颗粒 fine film grain`／`哑光 matte finish`／`水彩 watercolor wash`／
`蜡笔 crayon texture`／`陶瓷 glazed ceramic`／`木纹 visible wood grain`／
`布纹 fabric weave`／`蒸汽 haze and steam in air`／`干净数码 clean digital`

### 运动 motion（视频）
`固定 static`／`推 slow dolly in`／`拉 slow dolly out`／`摇 slow pan`／
`移 lateral truck`／`跟 tracking`／`升降 crane up`／`手持 handheld`／`环绕 slow orbit`

### 画面比例 ratio
`16:9`／`9:16`／`1:1`／`4:3`／`3:4`／`21:9`／`2.39:1 anamorphic scope`

---

## 2. 锁色块怎么写

不要写"暖色调""高级灰"这种形容词。**写十六进制。**

```
【色】锁定调色板 #E4744A #2E4756 #F0B65A（共 3 色，单色面积不超过 60%）
```

三种拿到色值的方式：
1. `shot.py build ... --from-image 参考图.png` —— 自动从参考图提取
2. `vqc.py palette 参考图.png --n 4` —— 手动看
3. 品牌规范里直接抄

**为什么必须写死**：不写死的色相跨度实测能到 90°+（画面花），
写死后能压到 20° 以内。这是"同一套图看起来像一套"的第一杠杆。

---

## 3. 三套现成模板

### 模板 A：产品主图（电商 1:1）

```
【主体】<产品名>，完整出现在画面中，正面略 3/4 角
【动作】<使用状态/静置>
【镜头】中景 · 平视 · 50mm · f/5.6
【光】棚拍 · 中性色温
【色】锁定调色板 <主色> <辅色> <点缀色>（共 3 色，单色面积不超过 60%）
【质感】哑光
【画面】1:1 square
【补充】背景干净，产品占画面 55-65%，四周留出安全边距
【禁止】多余的手指、肢体错位、文字乱码、水印、logo 变形、过饱和、塑料感、模糊、过曝
```
参数：分辨率 ≥1600×1600，步数 26-32，CFG 5-7，一次出 4-6 张。
出图后：`vqc.py pick out/*.png --profile product` → 修 → `textsafe` 查文字。

### 模板 B：品牌海报（A3 竖版）

```
【主体】<核心视觉元素>，占据画面中部
【动作】<静态/动态>
【镜头】中景 · 平视 · 85mm · f/4
【光】窗光 · 暖中性色温
【色】锁定调色板 <纸色> <深色> <主色> <点缀色>（共 4 色，主色面积 ≤35%）
【质感】哑光
【情绪】<三到五个词>
【画面】3:4 portrait
【补充】上方留出标题区（约占 22% 高度），底部留出信息区（约占 12%）
【禁止】...（同上）
```
参数：长边 ≥2480（A3 300dpi），步数 28-34，一次出 4 张。
**海报必须留白**：`textsafe` 查标题区和信息区，底噪 < 0.10 才合格。

### 模板 C：故事分镜（同场景多镜头）

先写一份 `shots.json`：

```json
{
  "profile": "illustration",
  "base": {
    "shot": "中景", "angle": "平视", "lens": "35", "aperture": "2.8",
    "light": "窗光", "wb": "暖中性", "texture": "胶片颗粒", "ratio": "16:9",
    "palette": ["#FBF5E9", "#2E4756", "#E4744A"],
    "mood": "温暖、安静、乡下"
  },
  "shots": [
    {"name": "灶屋的火", "subject": "柴火灶与铁锅，锅口冒着热气", "action": "火光照亮蹲着的人"},
    {"name": "小小的人", "subject": "灶台前的一张小板凳", "action": "孩子站在凳子上看锅里"},
    {"name": "藤椒", "subject": "后山藤椒坡与竹背篓", "action": "伸手进带刺的藤椒丛里摘"}
  ]
}
```

```bash
python shot.py spec --file shots.json -o prompts/
# 产出 01_灶屋的火.txt / 02_小小的人.txt / ... + _locks.md（一致性锁）
```

`_locks.md` 就是 base 那一段，**每个镜头的提示词里都带上**。
出图后：`vqc.py series out/` 查一致性，<70 就 `vfix.py unify --ref 最好那张`。

---

## 4. 负向词（默认清单）

```
多余的手指、肢体错位、文字乱码、水印、logo 变形、过饱和、塑料感、模糊、过曝
```

按场景增补：
- 人像：`多余肢体、面部不对称、眼睛变形、牙齿错乱`
- 产品：`标签错字、瓶身变形、反光死白、倒影杂乱`
- 建筑：`透视扭曲、窗户错位、结构不合理`

**不要塞几十条负向词**：超过 15 条会显著降低画面丰富度，模型开始"怕动笔"。
