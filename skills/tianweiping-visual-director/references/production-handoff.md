# 结构化制作与返修交接

## 编译可复制的任务

```powershell
python .\scripts\build_handoff.py .\assets\image-project.json
python .\scripts\build_handoff.py .\assets\video-project.json --format json
```

输出到终端，不写入原项目、生成媒体或提交付费任务。用UTF-8保存终端结果后可交给豆包。结构错误或明确的参数/机位冲突会返回失败；退出码0表示交接文本准备完成。

项目可增加capabilities，每个item可增加scene、camera、reference_roles、generation、repair_history。旧版字段继续可用。

## 场景与参考

```json
{
  "scene": {
    "subject": "原创圆耳角色，米白毛色，蓝围巾",
    "action": "抬头看灯光亮起后停顿",
    "environment": "窗边的安静房间",
    "composition": "中景，主体在画面左侧",
    "lighting": "右侧柔光",
    "style": "柔和绘本插画"
  },
  "camera": {"mode": "fixed", "movement": "none"},
  "reference_roles": []
}
```

scene存在时以其明确字段组成主体提示词，prompt仍保留作原稿；scene缺少的重要内容应先补齐。编译器再加入所引用人物卡的身份锚点、keep和参考图作用，不自行生成“更好看”的审美判断。

camera.mode为fixed或moving；固定机位的movement为none，移动机位写具体运动。参考角色允许同一图承担多种明确作用；每个asset_id必须在该item.references内，按其顺序对应参考图编号。role值为identity、style、composition、action、first_frame或last_frame。

## 能力卡与参数

```json
{
  "capabilities": {
    "entry": "本次实际入口",
    "model": "本次实际模型或版本",
    "status": "unknown",
    "modes": [],
    "parameters": {}
  }
}
```

未核验时保持unknown。核验后改verified，补source和checked_on（YYYY-MM-DD），填写真实支持的modes及参数描述。参数描述支持type（string/integer/number/boolean）、choices、数值min/max。这是跨工具的本地项目格式，不是豆包或火山方舟API请求格式；mode命名由实际适配器约定。

item.generation包含mode与parameters。模式不支持、参数未声明、类型/枚举/范围不合会阻止交接。未知能力下参数列入unverified_parameters，execution_parameters为空。声明已核验也只通过本地相容性检查；当前账户权限、素材输入组合与价格仍需当次确认，不从能力卡推断已授权。

执行参数与自然语言提示词分开，避免向豆包聊天复制其他API的旗标。编译器不读取供应商账户、不检验source网页内容，也不提供模型调用接口。

## 版本与返修

已有fail评审必须记录实际问题及被评审文件的asset_id和sha256。编译器会对能读取的该文件计算当前哈希：matched才进入局部返修；stale或unavailable先review_current_version。不要把旧版本的错误直接套到新版本。

repair_history记录method、outcome（improved/unchanged/unknown）、before_asset_id与after_asset_id；前后ID要不同且存在于assets。两次连续相同method且outcome均为unchanged时，建议change_method。代码不验证历史反馈是否真实，未经观看不要填写improved。

返修队列将事实、身份、结构与文字失败默认列为critical，其他失败为major；可据用户用途调整，不是统一审美分数。编译结果中的already_repaired始终为false，只有实际执行和验收以后才能在项目记录中改状态。

## V3 总监交接字段

direction包含task、purpose、audience、message，可选facts、assumptions、preserve、structural_changes_allowed、constraints、deliverables。task支持architecture/interior/poster/illustration/character/video/other；事实和假设都为字符串数组。

constraints每项包含id、source_asset_id、instruction；item.constraint_ids引用它，其源素材必须同时在该item.references内。拟修改内容用item.planned_changes声明，每项category与target；category支持geometry/material/lighting/camera/composition/text/props/identity。structural_changes_allowed为false时拒绝显式geometry变更；代码不识别所有文字暗示或生成后的结构漂移。

deliverables每项id、item_id、purpose；编号必须唯一，item_id要存在。参考role增加structure、material、annotation，作用说明见视觉总监参考。编译器在文本中标注尚未提供的参考文件，不因此声称已经分析其内容。

启用direction或item.design_reviews时，交付阶段要求12维记录。记录结构沿用reviews，dimension使用视觉总监表的代码；result另允许na，但必须有reason。需要文字的项目不能将typography排除。pass/fail必须对应当前产物、真实证据与查看方式，不能使用media_probe代表视觉判断。

设计失败进入返修队列时维度写成design:概念代码，保留原始证据与文件版本；默认优先级仍由主创按用途调整。V3未启用的旧项目继续按V2规则校验。
