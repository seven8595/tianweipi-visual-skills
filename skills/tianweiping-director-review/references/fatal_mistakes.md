# AI 出图典型致命错误图鉴（v2 新增）

本地 ComfyUI 出图最常见的 12 种翻车。每项给：识别方法 → prompt 修法 → 高级修法。

---

## 1. 招牌 / 文字乱码

**识别**：店铺招牌、海报标题、屏幕上的字符全是鬼画符。
**为什么**：SD/Flux 不是 OCR 模型，长文本几乎一定崩。
**Prompt 修法**：
- 让文字虚化：`blurred signage, out of focus shop windows, illegible but atmospheric signs`
- 减少文字量：`no text, minimal signage, only abstract logos`
**高级修法**：
- 生图后 inpaint 区域 + 用 PS / Figma 后期贴真字
- 用 Flux-Text / Font LoRA（试验性）
- ControlNet lineart 锁版式，单独在 PS 里打字

## 2. 多手指 / 畸形手

**识别**：人物手 6 指、融合、扭曲。
**Prompt 修法**：`beautiful hands, normal anatomy, natural hands, perfect fingers`
**负向加**：`extra fingers, missing fingers, deformed hands, fused fingers, malformed hands`
**高级修法**：
- 直接不让手出现：`hands in pockets, arms crossed, back view`
- inpaint 手部区域重抽
- ControlNet openpose 锁姿势

## 3. 透视崩 / 垂直线歪

**识别**：建筑向中心倾倒、地面没透视、人物和建筑比例失调。
**Prompt 修法**：`28mm lens, eye-level camera 1.6m, vertical lines corrected, no tilt shift, architectural photography, professional archviz`
**负向加**：`tilted vertical lines, converging verticals, wide angle distortion, fisheye, crooked buildings`
**高级修法**：
- ControlNet mlsd（建筑线）/ lineart 锁透视
- 参考一张真实街景做 img2img，denoise 0.6

## 4. 塑料质感

**识别**：石材像塑料、金属像玩具、皮肤像蜡像。
**Prompt 修法**：`PBR materials, physically based rendering, micro surface details, roughness variation, glass reflection, stone texture, brushed metal, ray traced soft shadows`
**负向加**：`plastic material, CGI look, 3d render toy, cheap texture, oversaturated`
**高级修法**：
- 加 Realistic LoRA（权重 0.5）
- 用 Juggernaut XL / RealVisXL 这类写实底模

## 5. 复制人 / 克隆人

**识别**：街上 10 个人长得一样、衣服一样。
**Prompt 修法**：`diverse crowd, different ages, different outfits, natural variety, pedestrians walking in different directions`
**负向加**：`duplicate people, cloned people, identical faces, same outfit repeated`
**高级修法**：
- Regional Prompter 分区写不同人物
- inpaint 几个人物重抽

## 6. 镜面反射地面

**识别**：雨后地面像镜子，倒影比实物还清楚。
**Prompt 修法**：`slightly wet pavement, soft reflections of warm lights, faint pedestrian reflections, not mirror-like, subtle sheen`
**负向加**：`mirror reflection, unrealistic water reflection, perfectly reflective floor`

## 7. 光源矛盾

**识别**：左边建筑有侧光、右边人物有顶光、地上影子方向不一致。
**Prompt 修法**：`consistent warm 3000K interior light spilling from shops, single main light direction, soft shadows cast to the right, blue hour ambient light`
**负向加**：`mixed lighting, inconsistent shadows, multiple light sources, conflicting illumination`

## 8. 色彩饱和过度

**识别**：整图艳得像游戏截图，廉价。
**Prompt 修法**：`muted color palette, desaturated, editorial photography, film look, subtle color grading, cinematic`
**负向加**：`oversaturated, cartoon colors, neon overload, cheap CGI, candy colors`

## 9. 元素堆砌（AI 味）

**识别**：画面每个角落都塞满东西，没有呼吸。
**为什么**：prompt 里堆了太多关键词。
**修法**：
- 删 prompt 里 30% 形容词
- 加 `minimal, uncluttered, generous negative space, editorial composition`
- 参考原研哉/深泽直人方向

## 10. 招牌 LOGO 堆砌

**识别**：画面里 8 个牌子，每个都想看清。
**修法**：`only 2-3 visible shop signs, rest blurred, subtle branding, not logo-heavy`
**负向加**：`multiple logos, brand logos everywhere, sign spam, visible text everywhere`

## 11. 人物比例错（巨人 / 矮人）

**识别**：人比门高、人头比窗大。
**修法**：`realistic human scale, people proportionate to buildings, correct height reference, 1.7m average human`
**负向加**：`giant people, tiny people, disproportionate figures, wrong scale`
**高级修法**：ControlNet depth 锁空间关系。

## 12. 圣诞灯串过度

**识别**：树上满是 LED 彩灯，像过年。
**修法**：`subtle warm string lights, restrained ambient lighting, not christmas decoration`
**负向加**：`christmas lights, holiday lights, excessive led strips, over-decorated`

---

## 通用急救包（写负向 prompt 时必带）

```
low quality, cartoon, anime, cheap CGI, plastic material, overexposed, 
oversaturated, distorted architecture, crooked buildings, warped windows, 
incorrect perspective, tilted vertical lines, floating objects, duplicate people, 
deformed hands, extra fingers, broken text, gibberish text, illegible signage, 
empty street, flat lighting, unrealistic mirror reflections, extreme wide angle distortion, 
fisheye, watermark, signature, jpeg artifacts, blurry
```
