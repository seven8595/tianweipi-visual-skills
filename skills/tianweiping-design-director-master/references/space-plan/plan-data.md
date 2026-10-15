# 空间数据与本地导出

在技能目录执行：

```powershell
python .\scripts\build_whitebox.py .\assets\demo-plan.json --output '一个尚不存在的输出目录'
```

Python3.10+，标准库即可。输出目录已存在时拒绝覆盖；换新目录名继续。demo-plan是明确虚构的工程样例，不是从用户附件恢复出的真实户型。

## 数据

单位固定为米；x向右、y向内、z向上。floor包含width/depth/thickness。墙段start/end为二维中心线，thickness/height为厚与高；墙体几何以中心线两侧各半墙厚生成。轮廓边缘的中心线需向内退半墙厚。

opening包含offset（从墙段起点沿中心线的距离）、width、bottom、height。门的bottom通常为0，但以实际项目为准；未知尺寸必须在assumptions里说明。相交/越界开口拒绝导出，不能靠修提示词解决结构数据错误。

家具用id、center（三维）、size（三维）表示包围盒，保持在项目平面范围内。脚本不检查通行、人体工程、消防或无障碍规范，也不证明盒子之间不会碰撞；按用途另做实际空间检查。

cutaway_walls列出展示中隐藏的墙ID。full-walls.obj仍保留全部墙段；cutaway.obj只隐藏列出的墙，二者共享同一数据。不开屋顶，不称完整建筑模型。

生成门窗洞口的方法是墙面分格并省略开口格，网格由命名的盒状部件组成，保留编辑性；不是复杂拓扑优化或参数化CAD。导入其他软件时核验单位、坐标与材质，不能仅按扩展名声称工程正确。

输出包括两个OBJ、materials.mtl、top-plan.svg和build-report.json。报告保存实际输入哈希、对象/顶点/面数与假设。SVG是从同一几何数据绘制的顶部示意，没有从渲染图反推平面。
