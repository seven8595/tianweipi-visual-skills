# Hero Frame Prompt 模板

## 用途
每个镜头生成一张hero frame（关键帧），用户QA通过后再做i2v。

## 模板

```
cinematic anime semi-realism editorial portrait,
[CHARACTER]: [角色DNA：发型/角/服装/道具/纹身],
[ACTION]: [角色在这个镜头做什么],
[SCENE]: [场景：雨夜巷子/屋顶/废墟，潮湿/雾/霓虹],
[DIRECTOR_MIX]: [导演配方关键词：黑泽明框中框/雷德利雾雨/王家卫散景],
[COMPOSITION]: [机位/景别/人物占画面比例],
[LIGHT]: [光源/轮廓光/阴影],
[MATERIAL]: [缎面/皮革/金属/钢/皮肤可区分],
[MOOD]: [情绪：克制/警觉/孤独/决绝],
premium illustration-photography hybrid, film grain, 16:9
```

## 反面词

```
anime cartoon, 2d flat, plastic skin, generic AI girl, watermark, text,
extra fingers, deformed hands, holographic UI, glow particles, daylight,
multiple people, center composition, over-smoothed
```

## 斩鬼都市5镜头参考

| 镜头 | 景别 | 人物占比 | 导演重点 |
|---|---|---|---|
| SHOT01 背影站巷 | 中景 | 60% | 黑泽明框中框（两侧柱子） |
| SHOT02 转头按刀 | 近景 | 75% | 王家卫霓虹散景 |
| SHOT03 拔刀斩 | 中景动态 | 65% | 黑泽明横向运动 |
| SHOT04 收刀鬼散 | 中景 | 55% | 王家卫静止情绪 |
| SHOT05 转身走远 | 远景 | 30% | 雷德利消失点+雾 |
