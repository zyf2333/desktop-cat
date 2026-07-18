# 猫精灵素材（Desktop-Cat，MIT 协议）

来源：https://github.com/1ilit/Desktop-Cat （MIT License，可商用）
画风：72×64 像素风，Q 版大头猫，灰白配色+粉耳+蓝项圈+黄铃铛

## 已有动画
- idle_01~04：待机（4 帧）
- walk_left_01~04：向左走（4 帧）
- walk_right_01~04：向右走（4 帧）
- sleep_01~06：睡觉（6 帧）
- zzz_01~04：带 Z 的完整睡猫（4 帧，直接播放，不能叠加到 sleep 上）
- angry_01：生气（1 帧）
- swat_left_01~04 / swat_right_01~04：从原始待机猫制作的左右抬爪抓取（各 4 帧）

## 复杂动作的连贯处理

当前素材没有独立的扑击、潜行、拍打、翻滚和困惑序列。为了避免不同来源的
像素猫在动作切换时脸型、鼻子或配色突变，渲染器统一从上述原始帧派生：

- pounce / stalk：行走帧配合压低、横向拉伸、腾空和落地形变
- alert / confused：待机原帧配合轻微跳起、绷紧、歪头和摇晃
- play_swat：专用抬爪序列；wrestle：待机原帧配合趴低和弹动

所有派生动作都保留原图的脸、鼻子、蓝项圈、黄铃铛和描边，可以与待机/行走
无缝衔接。未来若加入专用帧，命名为 `<anim>_NN.png` 并更新
`cat/models/catsprite/model.py` 的 `_pose_to_anim` 映射即可。
