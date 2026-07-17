# 猫精灵素材（Desktop-Cat，MIT 协议）

来源：https://github.com/1ilit/Desktop-Cat （MIT License，可商用）
画风：72×64 像素风，Q 版大头猫，灰白配色+粉耳+蓝项圈+黄铃铛

## 已有动画
- idle_01~04：待机（4 帧）
- walk_left_01~04：向左走（4 帧）
- walk_right_01~04：向右走（4 帧）
- sleep_01~06：睡觉（6 帧）
- zzz_01~04：呼噜气泡（4 帧，叠加在 sleep 上）
- angry_01：生气（1 帧）

## 缺失动画（后续补充，补好后改 _pose_to_anim 映射）
- pounce（扑击）：目前用 walk 代替
- play_swat / play_jump（玩弄）：目前用 angry 代替
- alert / confused（警觉/困惑）：目前用 idle 代替

补充素材放进本目录，命名 <anim>_NN.png，然后在
cat/models/catsprite/model.py 的 _pose_to_anim 改映射。
