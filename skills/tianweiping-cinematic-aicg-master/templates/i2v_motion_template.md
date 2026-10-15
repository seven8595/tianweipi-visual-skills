# i2v 运动 Prompt 模板

## 原则
首帧图已锁定画面，运动prompt只写：动作 + 运镜 + 环境动效。
不要重复描述角色外观、场景、色彩——图已经定了。

## 三段式结构

```
[角色动作] + [摄影机运动] + [环境/次要运动]
```

## 动作镜头（3秒）

```
She draws the katana in a fast horizontal slash, hair and kimono sleeve
flare outward, blade leaves a faint red trail. Camera holds static,
slight handheld shake on impact. Rain falls steadily in background.
```

## 静止情绪镜头

```
She stands motionless, slowly lowering her head as the katana returns
to its sheath. Camera slowly pushes in. Rain drops run down the blade.
Background neon flickers softly.
```

## 行走镜头

```
She walks slowly forward away from camera, hair swaying with each step.
Camera slowly dollies backward keeping her in frame. Rain and fog drift
through the alley depth. Neon signs glow on both sides.
```

## 禁用词（会触发AI杂讯）

- glow / glowing / luminous（全息UI）
- reflection on face（塑料反光）
- flickering light（频闪）
- particles floating（鬼物粒子乱飞）
- dramatic camera zoom（突兀推拉）

## 已知失败模式

- 极特写手/眼 → 肢体变形
- 同一张正面肖像做所有镜头 → 脸出现3次
- prompt写glow/reflection → 全息UI杂讯
- length>5秒 → 后期崩坏
