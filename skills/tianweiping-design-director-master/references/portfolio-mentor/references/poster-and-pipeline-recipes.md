# 已验证的实操 Recipe（2026-09-28 田伟平项目沉淀）

本文件记录在真实项目中跑通的具体做法，不是抽象原则。新 agent 接手时直接复用。

## 一、快消食品海报已验证组合

**用户认可的风格 DNA**（不要再用 PIL 叠字试"大师风"）：
- 撕纸效果从单一方向破开，露出真实食材（抹茶粉/咖啡豆/果酱液/番茄酱）
- 产品瓶/罐/袋居中偏下，带独立设计标签
- 大衬线英文标题在顶部（如 matcha / Fresh Roast / cocoa / New Batch / almond / Homemade / GUMMY POP）
- 手写体副标（Green & Pure / Brew Love / Dark & Rich / Spread Joy / Plant Based / Mangi）
- 单色系背景（抹茶绿、米色、可可棕、果酱红、杏仁米、番茄红、Y2K 明黄）
- 右下角竖排卖点标签（SINGLE ORIGIN / MEDIUM ROAST 等）

**AI 生图文字可靠性**：
- 大标题（英文衬线，1-2 个词）→ 可靠，直接用
- 中文短标题（<8 字，如"秋季新品上市""夏日冰饮"）→ 可靠
- 产品标签上的品牌名（MIDORU / ROAST No.12 / NOIR 70%）→ 基本可靠
- **英文小字（成分、净含量、营养表）→ 必乱码**，接受为缩略图不可见，不重生成
- **H5 卡片内积分/价格小字 → 必乱码**，标注"概念稿，真实数据接后台"
- 英文花体手写大段 → 乱码重灾区，避免

**已否决的做法**：
- PIL 在产品图上叠"大师风"字（用户："质量太差"）
- 所有品类用同一个品牌名"本朴/BENPU"
- 英文花体手写作为主标题

## 二、互联网活动物料三件套（对应 JD）

- 横版 Banner 16:9：左侧大标题+副标题，右侧三产品，右下 CTA 按钮
- H5 活动页 9:16：顶部导航，中央大标题+副标题，三档奖励卡片，底部 CTA
- 方形资源位 1:1：顶部品类名，中央产品，底部促销条

## 三、PDF 组装流水线（Linux 已验证）

环境：Python3 + Pillow + Noto Sans CJK。

```python
# 字体
SANS_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
SANS_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
SANS_L = "/usr/share/fonts/opentype/noto/NotoSansCJK-Light.ttc"

# 页面
W, H = 1080, 1440
BG = (245, 241, 234)  # 米色
INK = (50, 45, 40)
GRAY = (140, 128, 115)
```

结构：
1. 封面：姓名（78pt Black）+ 职位（34pt Light）+ 分隔线 + 能力索引（22pt）+ 电话（18pt 灰色）
2. 项目简介页：项目编号（24pt Light 灰）+ 项目名（46pt Black）+ 短线 + 简介（22pt）+ 9 行列表（20pt）
3. 作品页：直接嵌图，左下角加水印
4. 导出：`pages[0].save(OUT, save_all=True, append_images=pages[1:], resolution=150)`

水印做法：
```python
wm_font = ImageFont.truetype(SANS_R, 22)
# 半透明黑底圆角矩形 + 白字 "凯文 KevinShuge"
# 位置：左下 16px 边距
```

## 四、坑与修复

| 现象 | 原因 | 修复 |
|---|---|---|
| curl 下载图片为 0 字节 | 网络抖动/CDN 重定向 | 重新 curl，不要 retry 三次就放弃 |
| 文件名带 `)` | shell printf 格式串写错 | tr -d ')' 批量改名 |
| PDF 页数不对 | glob 排序或漏文件 | ls *.jpg 先确认数量 |
| 中文方块字 | 字体路径错或没装 Noto CJK | fc-list :lang=zh 查 |
| 角色披风变翅膀 | AI 自由发挥 | prompt 显式写 "NO wings, NO bat wings, just red cloth fabric" |
| 标签小字乱码 | 模型不擅长小字 | 接受，不重生成；或后期 PIL 排字 |
