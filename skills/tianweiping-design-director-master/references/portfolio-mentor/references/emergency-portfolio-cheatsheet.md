# 应急作品集 Cheatsheet（零经验 · 当天交付）

> 触发条件：用户说"我没做过这个品类但今天/明天就要交"、"下午要给 HR"、"帮我快速凑一份作品集"。直接按本文件执行，不重新讨论策略。

## 一、90 分钟交付流程

| 阶段 | 时长 | 动作 |
|---|---|---|
| 1. 锁定概念品牌 | 5 min | 起一个中性品牌名，写死色板/关键词/禁用项 |
| 2. 生成产品图 | 20 min | 一次批量 8-12 个品类，提示词末尾必加"不要文字" |
| 3. PIL 叠字排版 | 15 min | 跑统一模板脚本，3:4 竖版 1080×1440 |
| 4. 拼 PDF | 5 min | PIL 合并 JPG 为 PDF |
| 5. 加封面封底（可选） | 10 min | pypdf 合并，封面写用户姓名电话 |
| 6. 本地保存+交付 | 5 min | urllib 下载到用户项目目录 |

## 二、概念品牌锁定表（一次写死）

```
品牌名：[用户偏好或自拟，2-4 字中文 + 英文拼音]
定位：[一句话，如"都市青年日常家居"]
视觉关键词：[3 个，如 留白/自然材质/低饱和暖调]
色板：[4 个 HEX]
禁用：[3 个，如 大红促销字/金色堆砌/徽章贴纸]
项目性质：概念设计项目（面试被问要承认）
```

## 三、产品图批量提示词模板

```
商业产品摄影：[产品描述]，[动态元素如牛奶飞溅/气泡/水花/蔬果环绕]。
背景纯[单一色]。产品[斜放/居中]，[动态元素]环绕。[调性]商业广告。不要文字。
```

一次 image_gen 调用 8 张，每张独立 request。品类选择优先覆盖：
- 饮品 2（苏打水/咖啡）
- 食品 3（巧克力/薯片/冰淇淋）
- 个护 2（洗发水/身体乳）
- 美妆 1（香水/防晒）

## 四、PIL 叠字脚本（直接改字段跑）

```python
from PIL import Image, ImageDraw, ImageFont
import os

D = r"产品图目录"
# Windows: C:\Windows\Fonts\msyhbd.ttc / msyhl.ttc
# Linux:   /usr/share/fonts/opentype/noto/NotoSansCJK-{Light,Medium,Bold}.ttc
F_HEI = "C:/Windows/Fonts/msyhbd.ttc"
F_LIGHT = "C:/Windows/Fonts/msyhl.ttc"

def crop34(img):
    sw, sh = img.size
    nw = int(sh * 3/4)
    nl = (sw - nw) // 2
    return img.crop((nl, 0, nl+nw, sh))

def poster(src, out, word, cn, text_color=(255,255,255), sub_color=(220,220,220)):
    img = crop34(Image.open(f"{D}/{src}").convert("RGB"))
    d = ImageDraw.Draw(img)
    W, H = img.size
    d.text((W//2, int(H*0.04)), "BENPU", font=ImageFont.truetype(F_HEI, int(W*0.016)),
           fill=text_color, anchor="ma")
    d.text((W//2, int(H*0.10)), word, font=ImageFont.truetype(F_HEI, int(W*0.10)),
           fill=text_color, anchor="ma")
    d.text((W//2, int(H*0.22)), cn, font=ImageFont.truetype(F_LIGHT, int(W*0.03)),
           fill=sub_color, anchor="ma")
    d.text((W//2, int(H*0.94)), "本朴 BENPU", font=ImageFont.truetype(F_HEI, int(W*0.014)),
           fill=text_color, anchor="ma")
    img.save(f"{D}/{out}", quality=92)
```

## 五、拼 PDF

```python
from PIL import Image
files = ["01.jpg", "02.jpg", ...]  # 按顺序
imgs = [Image.open(f).convert("RGB") for f in files]
imgs[0].save("作品集.pdf", save_all=True, append_images=imgs[1:], resolution=150)
```

## 六、加封面封底（pypdf）

```python
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfWriter

# 1. 先生成封面/封底单页 PDF
cover = Image.new("RGB", (1080, 1440), (245,241,234))
d = ImageDraw.Draw(cover)
d.text((540, 600), "本 朴", font=ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 110),
       fill=(74,63,53), anchor="mm")
d.text((540, 1280), "田伟平  Seven", font=ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 26),
       fill=(74,63,53), anchor="mm")
cover.save("cover.pdf", "PDF", resolution=150)

# 2. 合并
w = PdfWriter()
w.append("cover.pdf")
w.append("作品集.pdf")
w.append("closing.pdf")  # 同样方法做封底
with open("完整版.pdf", "wb") as f:
    w.write(f)
```

首次需 `pip install pypdf`。

## 七、Windows cwd 失效时的绕过

PowerShell 报 `cwd does not exist` 时，所有 PowerShell/Bash 命令都跑不了（连 echo 都不行）。改用：

```python
# computer_use_tool(plane="cu", code="...")
import os, urllib.request
os.makedirs(r"C:\目标目录", exist_ok=True)
urllib.request.urlretrieve("https://云端URL", r"C:\目标目录\文件.pdf")
print(os.path.getsize(r"C:\目标目录\文件.pdf"))
```

Python 不受 cwd 影响，用绝对路径即可。

## 八、交付两版

- **V1 HR 快投版**：纯 N 张海报 PDF，无封面封底，微信直发
- **V2 完整版**：封面 + N 张 + 封底（含姓名电话），面试/正式投递

HR 说"只放作品不用诠释"时，V1 就够。

## 九、不能做的事

- 不写"销量增长 XX%"、"服务过 XX 客户"
- 不把 AI 生成的包装字当真实版式（包装上的字是 AI 乱码，后期 PIL 叠的才是真的）
- 不伪造手绘过程、草图、客户反馈
- 面试被问就说"这是个人概念提案，用于展示视觉系统设计能力"
