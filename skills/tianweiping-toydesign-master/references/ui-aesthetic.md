> 来源：原 ui-design-aesthetic

# UI Design Aesthetic — 前端UI设计审美校准器

解决：AI生成的网页"能用但丑"、"像Tailwind默认模板"、"配色像2018年"、"间距全靠猜"。

核心：**把设计师的经验翻译成AI能执行的硬规则**，不是靠"高级感"这种形容词。

## 1. 配色系统（AI最常翻车的地方）

### AI默认配色 = 立刻廉价
- ❌ 紫蓝渐变 `#667eea → #764ba2`（Tailwind默认）
- ❌ 全屏深色 + 霓虹青色边框
- ❌ 红/黄/绿按钮各一个颜色
- ❌ 文字用纯黑`#000`或纯灰`#999`

### 正确做法：三色制 + 中性色阶

```
主色：1个，占60%（品牌色/文字/边框）
强调色：1个，占5%（按钮/链接/焦点）
中性色：5级灰阶，占35%
```

| 用途 | 色值参考 |
|---|---|
| 页面背景 | `#FAFAF9`（暖白，不是纯白#FFF） |
| 卡片背景 | `#FFFFFF` |
| 主文字 | `#1C1917`（不是纯黑） |
| 次要文字 | `#78716C`（暖灰，不是#999冷灰） |
| 弱化文字 | `#A8A29E` |
| 边框 | `#E7E5E4` |
| 主按钮 | 深色`#1C1917`底 + 白字（不是蓝色！） |
| 强调 | 选一个有性格的色：橙`#EA580C`/墨绿`#166534`/酒红`#9F1239` |

**规则**：一个页面最多1个品牌色+1个强调色，其他全用中性灰。

## 2. 排版系统（间距和字体）

### 字体选择
| 场景 | 选择 | 不要 |
|---|---|---|
| 中文正文 | 思源黑体/系统默认 | 微软雅黑全屏 |
| 英文标题 | Inter / Manrope / Geist | 默认sans-serif |
| 英文装饰 | 不用花哨字体 | Comic Sans/艺术字 |
| 代码 | JetBrains Mono / Fira Code | 默认等宽 |

### 字号层级（8px基准）
```
Display:  57px / 行高1.05 / 字重700
H1:      45px / 行高1.1  / 字重600
H2:      36px / 行高1.2  / 字重600
H3:      28px / 行高1.3  / 字重600
H4:      24px / 行高1.4  / 字重500
Body:    16px / 行高1.6  / 字重400
Small:   14px / 行高1.5  / 字重400
Caption: 12px / 行高1.4  / 字重400
```

### 间距网格（8px基准）
所有间距必须是8的倍数：
```
4px  = 图标和文字间距
8px  = 紧凑间距
16px = 默认间距（卡片内边距）
24px = 区块间距
32px = 大区块间距
48px = 章节间距
64px = 页面section间距
```

**禁止**：`padding: 13px`、`margin: 17px`这种奇数间距。

## 3. 组件规范

### 按钮
| 类型 | 样式 |
|---|---|
| 主按钮 | 深色底`#1C1917` + 白字 + 圆角8px + padding 12px 24px |
| 次按钮 | 白底 + 1px边框`#E7E5E4` + 深色字 |
| 文字按钮 | 无底无边 + 强调色文字 |
| 禁止 | 蓝色渐变按钮、胶囊按钮全屏、阴影过重 |

### 卡片
- 圆角：12px（不是8px也不是24px）
- 阴影：`0 1px 3px rgba(0,0,0,0.05)`（极淡，不是大黑影）
- 边框：1px solid `#E7E5E4`（可选）
- 内边距：24px
- 禁止：玻璃态毛玻璃全屏、渐变边框、悬浮动效过度

### 导航
- 固定顶部 + 模糊背景`backdrop-blur`
- 高度：64px
- Logo左，菜单中，CTA右
- 不要侧边栏全屏深色

## 4. 动画原则（高级感动画 vs 廉价动效）

| 做 | 不做 |
|---|---|
| 缓动`cubic-bezier(0.4, 0, 0.2, 1)` | `ease-in-out`全程 |
| 时长200-300ms | 1秒以上 |
| hover微抬升`translateY(-2px)`+阴影 | 放大1.2倍 |
| 页面加载stagger（错开100ms） | 所有元素同时出现 |
| scroll-trigger淡入 | 全屏视差滚动 |
| 数字计数动画 | 粒子效果 |

## 5. 布局规则

- **容器最大宽度**：1200px居中，不要全屏拉到2560px
- **左右边距**：桌面24px，移动端16px
- **section间距**：上下80-120px
- **不要居中所有东西**：左对齐正文，标题可以居中
- **留白比内容多**：一个section内容占60%，留白40%
- **禁止**：三列等宽卡片塞满脸、所有元素居中、icon+标题+描述重复6遍

## 6. 工程思维

- HTML语义化（nav/header/main/section/footer）
- 响应式：移动端优先
- 图片用`next/image`或懒加载
- 字体用`font-display: swap`
- 颜色用CSS变量，不要硬编码
- 不要Tailwind classes一堆，抽组件

## 7. 出图/出代码后Checklist

- [ ] 配色不是默认蓝紫渐变？
- [ ] 主按钮是深色不是蓝色？
- [ ] 间距都是8的倍数？
- [ ] 字号有层级（不是所有文字16px）？
- [ ] 有足够留白（不是塞满内容）？
- [ ] 卡片圆角统一（不是一会8一会24）？
- [ ] 阴影极淡（不是大黑影）？
- [ ] 动效克制（不是粒子+视差+自动播放视频）？
- [ ] 文字用暖灰不是纯黑？
- [ ] 容器有最大宽度（不是全屏拉满）？

## 8. Prompt模板（给AI写网页时加这段）

```
Design requirements:
- Color: warm white background #FAFAF9, dark text #1C1917, 
  warm gray secondary #78716C, one accent color only
- Spacing: 8px grid system (all multiples of 8)
- Typography: Inter for English, system Chinese, clear hierarchy
- Components: rounded-12px cards, subtle shadow, dark primary button
- Layout: max-w-1200px centered, generous whitespace
- Motion: 200-300ms ease, subtle hover, no particles/parallax
- Do NOT use: purple-blue gradients, neon borders, glassmorphism everywhere,
  default Tailwind indigo, centered everything, odd pixel values
```
