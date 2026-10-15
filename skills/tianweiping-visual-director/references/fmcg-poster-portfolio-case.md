# 快消品视觉作品集：零经验快速补位案例（已验证）

> 来源：田伟平 2026-09 求职脉思数字营销「视觉设计总监/经理」实战。11 年视觉经验但零快消作品，HR 当天下午要。本文件记录跑通的做法，不是理论。

## 一、核心判断

零快消作品时，**不要硬凑假商业案例**（会被问穿）。改做视觉统一的**概念品牌**，项目性质如实标"概念设计项目"，面试被问就承认是个人概念提案。HR 看的是你能不能把产品拍得高级、字排得准、系列感统一——不是你有没有服务过雀巢。

## 二、概念品牌设定（一次锁定，全系列复用）

- 品牌名：**本朴 BENPU**
- 定位：都市青年日常家居
- 视觉关键词：留白 / 自然材质 / 低饱和暖调 / 窗光
- 色板：米白 #F5F1EA · 暖灰 #C9C2B8 · 深棕 #4A3F35 · 苔绿 #7A8471
- 禁用：大红促销字、金色堆砌、徽章贴纸、复杂三维效果
- 第二个副品牌：**醒 XING COFFEE**（即饮黑咖，炭黑+芥末黄+苔绿，暗调戏剧布光）

## 三、产品摄影生成模板

**关键：生成产品图时明确说"不要文字"**。所有文字后期用 PIL 叠，避免 AI 生成乱码包装字。

每品类提示词骨架：
```
商业产品摄影：[产品描述]，[动态元素如牛奶飞溅/气泡/水花]。背景纯[色]。
产品[斜放/居中]，[动态元素]环绕。[调性]商业广告。不要文字。
```

20 个品类矩阵（已验证）：
| 类别 | 品类 |
|---|---|
| 家居个护 | 抽纸、毛巾、咖啡杯、冷萃咖啡、身体乳、蜂蜜 |
| 食品饮料 | 棒棒糖、巧克力、薯片、苏打水、番茄酱、冰淇淋、饼干、麦片 |
| 美妆个护 | 香水、洗发水、防晒 |
| 概念/编辑 | 封面、编辑人像、地平线概念 |

## 四、海报排版模板（PIL 叠字）

商业海报统一模板（3:4 竖版 1080×1440）：
- 顶部居中：`BENPU` kicker（小字 Medium）
- 上部 10-22%：**巨大 serif 英文产品词**（如 `lolly` / `break` / `fizz`）
- 22% 处：中文副标题（如"本朴 · 童年味道"）
- 底部 94%：`本朴 BENPU` 落款
- 文字色按背景反选：深底白字 / 浅底深棕字

极简本朴版（九张）模板不同：
- 左上角 `BENPU` + 系列名
- 左下角中文产品名 + 英文小字
- 大量留白，不压大字

## 五、PDF 组装（Linux PIL 已验证）

```python
from PIL import Image
imgs = [Image.open(f).convert('RGB') for f in files]
imgs[0].save('out.pdf', save_all=True, append_images=imgs[1:], resolution=150)
```

中文字体（Linux）：`/usr/share/fonts/opentype/noto/NotoSansCJK-{Light,Regular,Medium,Bold,Black}.ttc` 和 `NotoSerifCJK-{Regular,Bold}.ttc`。

## 六、Windows 端补封面/封底（pypdf）

当需要给纯海报 PDF 加封面联系信息时：
1. PIL 生成 1080×1440 封面图（米白底 + 品牌名 + 用户姓名电话）
2. `img.save('cover.pdf', 'PDF', resolution=150)`
3. pypdf 合并：`PdfWriter.append()` 依次加 cover + 原 PDF + closing

Windows 字体：`C:\Windows\Fonts\msyhbd.ttc`（粗黑）、`msyhl.ttc`（细黑）、`simsun.ttc`（宋体）。

## 七、两版交付（HR 沟通驱动）

HR 原话："您只需要放作品就可以 不用诠释的 这样更直观一些 也更效率 都是非常有经验的人 一看作品就晓得啦"

→ 交付策略：
- **V1 HR 快投版**：纯 20 张海报，无封面无封底，8.4MB，微信直发
- **V2 完整版**：封面（姓名+电话）+ 20 张 + 封底（THANKS + 联系方式），面试/正式投递用

**不要默认两版都做封面解释页**。HR 明确说不要诠释时，越干净越好。

## 八、Windows 环境坑

1. **PowerShell cwd 失效**：如果项目目录被删/切换，PowerShell 工具会报 `cwd does not exist` 且无法执行任何命令（连 `echo` 都不行）。此时改用 `computer_use_tool(plane="cu")` 跑 Python，Python 里用绝对路径 `os.makedirs(..., exist_ok=True)` 重建目录。
2. **Bash 在 Windows host 不可用**，别尝试。
3. pypdf 首次需 `pip install pypdf`。
4. 下载云端 URL 用 `urllib.request.urlretrieve(url, out)` 即可，不需要 Invoke-WebRequest。

## 九、已知限制（不隐瞒）

- 所有产品图是 AI 生成，包装上的品牌字是 AI 乱码（如"PUMZO tomato"），后期叠的 `BENPU` 字是 PIL 加的，**包装本身没做真实版式**。面试被问要承认是概念视觉，不是量产包装。
- 20 张海报排版模板偏单一（顶部 kicker + 大词 + 中文副标题），系列感强但单张差异不够大。如果 HR 觉得"都一个样"，下一轮要给每张换不同的字体角色和版式（参考 Chupa Chups 巨型字压产品 / Kit Kat 上下白字夹产品 / ZYLYRA 分栏几何块）。
- 没有真实投放数据、客户反馈、销售结果。案例叙述里不写这些。
