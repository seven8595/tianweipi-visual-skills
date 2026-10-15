# 本地展板代码

在技能目录执行：

```powershell
python .\scripts\build_board.py .\assets\board-template.json --output '新的展板文件.svg'
```

脚本只用标准库，把本地JPEG/PNG原始字节嵌入SVG，按比例排放并显示来源哈希。不修改输入内容、不调用云端、不自动生图。已有输出拒绝覆盖。

JSON包含mode（project/research）、title、palette（可选六位HEX数组）、cards。每张卡含id、label、scene_id、path；路径相对JSON文件或为本地绝对路径。project要求全部scene_id一致；research允许不同来源并明确标识。ID要唯一。

样例使用五张附件，处于research模式。版式色块是指定参数，不是从图片实测得到的品牌标准色。文字、图片来源与实际项目关系仍需审稿。

脚本仅检验常用图片签名，不完整解码图像。源图解码与SVG查看另用真实工具完成。XML转义保护标题与标签，禁止把参考文字作为代码或外部URL执行。
