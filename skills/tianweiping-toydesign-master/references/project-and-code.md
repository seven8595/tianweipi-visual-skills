# 项目数据与代码用法

## 运行

复制 `assets/video-project.json` 或 `assets/image-project.json` 到项目目录，填写本次真实数据。路径相对 JSON 所在目录；支持本地绝对路径。原样模板是策划示例，尚无输出文件或验收记录。

```powershell
python .\scripts\check_project.py .\assets\video-project.json --stage plan
python .\scripts\check_project.py .\assets\video-project.json --stage delivery
```

在 skill 目录执行上述命令；其他位置请使用实际绝对路径。输出是 JSON；脚本只读输入与相关本地文件。不访问云端，不运行生成任务，不修改媒体。Python 3.10+，无需 pip 依赖。

退出码：`0`=本次阶段的结构检查通过；`1`=发现工程问题或失败的交付检查；`2`=输入错误/无法读取；`3`=交付项尚未完成评审。退出码0不是作品完美或生成授权。

## 字段约定

| 字段 | 作用 |
|---|---|
| schema_version / project_id / kind | 版本1、项目名、image 或 video |
| width / height | 计划尺寸，正整数；不代表已探测输出 |
| fps / target_frames | 视频时间线帧率与总帧数；图片不用 |
| text_required / audio_required | 实际画面含须核对文字/视频有声音；视频音频默认需要 |
| characters | id 唯一，anchors 是必须保留的可见特征 |
| assets | id、path、approved，可选 sha256；approved 只是记录，不替代评审 |
| items | 按时间线顺序；id、prompt、characters、references、keep |
| frames / overlap_previous_frames | 本镜已经选定的编辑帧数、与前镜重叠帧数 |
| output_asset_id | 实际产物对应的素材ID；策划阶段可为 null |
| reviews | 针对当前产物版本的评审记录；策划可为空 |
| subtitles | start_frame、end_frame、text，可选 track，成片全局坐标 |
| subtitle_max_chars / subtitle_max_cps | 可选预警线，可为 null；不代替实际试听 |
| budget | currency、limit、spent、planned_new_calls、max_new_calls、estimated_next_cost |

字幕计数是非空白 Unicode 码点数，组合表情可能占多个码点，不是完整字素测量。`estimated_next_cost` 为所有拟执行调用的费用合计，未知填 null；不能以未知代替零。脚本预算仅依据声明值，不查询价格、账户余额或历史消费。

交付阶段读取 `assets` 中列出的全部文件；未使用的策划素材若仍未取得，可从这次交付清单移出并保留在原策划版本。成片可以作为一个完整视频 item 验收，逐镜清单另外保留；逐镜通过不能取代最终导出片的验收。

## 评审记录

检查维度由内容决定：brief、identity、structure、composition、export始终需要；有文字增加text；多个图片item增加continuity；视频增加motion与continuity，有声视频再增加sound。字幕非空时必须声明text_required为true。

每个维度一个当前结论。`result` 为 pass、fail 或 unknown。pass/fail 必须包含 evidence、reviewer、method、asset_id 与对应真实文件的sha256。更新文件后重新评审，不能把旧hash复制到新输出。

```json
{
  "dimension": "motion",
  "result": "unknown"
}
```

真正播放镜头以后才填写 pass/fail 和证据。方法值为 image_view、video_playback、audio_listen、media_probe、user_review；motion 要 video_playback，sound 要 audio_listen，export 要 media_probe。文件规格用可用媒体探测工具检查，证据中写实际尺寸/帧率/时长；本脚本不会调用探测器。

`recorded_delivery_ready` 仅表示文件版本与声明的检查记录齐全，不能证明评审真实或美感合格。验收者仍负责观看、听音和最终判断。预算未知不使已完成、无需再生成的作品自动失败，但它不能成为继续付费的依据。

## V2 实际媒体探测

```powershell
python .\scripts\check_project.py .\project.json --stage delivery --probe --ffprobe '已安装的ffprobe.exe绝对路径'
python .\scripts\probe_media.py '实际媒体文件绝对路径' --ffprobe '已安装的ffprobe.exe绝对路径'
```

不指定ffprobe路径时从PATH查找；找不到时返回未知。入口只接受本地路径，调用已有工具，探测限制为file协议，不安装工具或上传素材。

项目校验会比较实际输出的像素尺寸、视频平均帧率、声音需求与可用帧覆盖；不把参数声明当成实际文件。`trim_in_frame` 为从源片开始剪入的帧号，默认0；源片至少覆盖trim_in_frame+frames。多出的余量可保留。最终精确导出片可设置`exact_output_frames: true`，此时不允许同时剪入源片。

优先使用文件头的nb_frames；没有时用时长×平均帧率估算，并标注精确帧数未知。文件头帧数不是完整解码计数，变帧率、时间戳异常或文件损坏需另行检查。旋转信息非零时要验证实际显示方向。图像检查仅识别常用静态图像编码和尺寸，不检验像素内容、ICC色彩、透明边缘或审美。

开启探测也不会填造人工验收记录；文件规格匹配以后，仍需实际看图、播放、听音和检查最终导出。
