# character-ip-studio 项目交接卡

> 生成时间：2026-09-29 23:55
> 用途：新对话框直接发这段，不用重述前情。

---

## 一、当前项目状态

用户在搭建 `character-ip-studio` skill（玩具/动画角色 IP 设计工作流）。skill 已完成主体搭建，正在跑第一个练习任务 ART-TOY-001（收集雨声的小修补匠），同时提炼用户个人视觉风格（SEVEN 风格档案 v0.2）。

---

## 二、关键文件路径

| 文件 | 路径 |
|---|---|
| 主 SKILL.md | `C:\Users\seven\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.user_skills\character-ip-studio\SKILL.md`（30KB，14章） |
| SEVEN 风格档案 | `...\character-ip-studio\references\seven-style-profile.md`（v0.2） |
| 参考方法包（zip解压后） | `...\character-ip-studio\_reference_pack\`（含 methods.md / sources.md / exercises.md / 色彩对照实验） |
| 用户手绘原稿 | `C:\Users\seven\Desktop\手绘\` 共 14 张 jpg |

---

## 三、skill 章节结构（14章）

0 主创分工 / 1 五阶段工作流 / 2 艺术家研究 / 3 角色设计执行（标准卡9字段+三视图+豆包提示词模板）/ 4 AI痕迹修复 / 5 审美六维 / 6 持续学习 / 7 艺术指导创意筛选 / 8 有来源艺术训练（9个URL入口+8项练习A-H）/ 9 SEVEN个人视觉语言 / 10 方法卡M01-M08 / 11 来源索引S01-S11 / 12 边界 / 13 接到任务第一步

---

## 四、用户已拍板的方向（v0.2 锁定）

1. **最终质感**：手绘铅笔/彩铅笔触，不要 3D 光滑渲染，不要数字粉系光滑插画
2. **装饰密度**：和风密集装饰是目标方向（参考 R03 和用户自己的 P10 宝石眼泪蝴蝶女）
3. **角色方向**：选 A01 圆胖罐形（不是 B01 高瘦竹筒）
4. **署名**：凯文 KevinShuge / 田伟平（二选一，未定）
5. **用户风格核心**：
   - 重交叉排线 + 眼睛画最重
   - 学院派静物功底 + 表现主义速写并存
   - 反复画安静内省的日常瞬间（窗前看月、贴电话、宝石眼泪蝴蝶）
   - 彩铅作品里暖黄/橙做主体，宝石色点睛

---

## 五、当前练习 ART-TOY-001 进度

**任务**：设计"收集雨声的小小修补匠"——好奇雨声但怕收藏瓶被淋湿。

**已生成版本**：
- A01 原版（3D 光滑潮玩）：https://aka.doubaocdn.com/s/1SnJ2mZHi9  → 已否定
- B01（3D 高瘦竹筒）：https://aka.doubaocdn.com/s/UB1fOVuFgf  → 已否定
- A01'（铅笔排线但眼睛太凶）：https://aka.doubaocdn.com/s/5ViwqPVDOx  → 已否定
- **A01''（当前最新，待用户验收）**：https://aka.doubaocdn.com/s/wAIl2guwF4
  - 圆胖罐形 + 双手抱瓶 + 头顶提灯
  - 铅笔交叉排线 + 暖黄灯芯
  - 眼睛平和不凶，安静好奇
  - 周围有雨丝、瓶花纹、脚边水花
  - **待改进**：装饰密度还不够密，要往 P10 宝石蝴蝶那种密度靠

**等用户确认**：
- A01'' 方向对不对？
- 署名用 KevinShuge 还是田伟平？
- 主设定稿装饰密度够不够，还是从现在开始就堆满？

---

## 六、新对话框接续指令（直接复制给新豆包）

```
继续 character-ip-studio 项目。交接卡见上文。
当前最新角色 A01'' 在 https://aka.doubaocdn.com/s/wAIl2guwF4
等我对 A01'' 的反馈后，按 SEVEN 风格档案 v0.2 继续。
不要重新分析手绘原稿，不要重做 skill 主体。
```

---

## 七、未完成事项

- [ ] 用户对 A01'' 拍板
- [ ] 署名定下来
- [ ] A01'' 通过后：出三视图（正面/侧面/背面），基于 core-ip 用 image_edit
- [ ] 出一张密集装饰版场景海报（雨景+蝴蝶/宝石纹样，密度对标 P10/R03）
- [ ] ART-TOY-001 完结后开新题"给种子送信的夜班信使"验证方法迁移
- [ ] 4.5节"光影与材质统一"半节仍缺原文（用户从未补发"不让毛绒……"后内容）
