# Ego-Planner-System

> 基于 ROS2 + PX4 + Gazebo 的无人机自主规划与仿真系统，集成 EGO-Swarm 轨迹规划算法、深度相机感知、YOLOv8 目标检测与 Offboard 飞行控制。

---
🎥 **演示视频见下方，支持完整自主避障飞行流程**

---

## 🎬 演示视频

👉 **B站演示（强烈推荐观看）：**  
[【ego-planner视觉加避障px4+ros2】](https://www.bilibili.com/video/BV1enAnzgErY/?share_source=copy_web&vd_source=5445edc75bd404289e45d33b108b4bd1)

---

## 🔗 项目参考 / 致谢

> 本项目基于 DongnanHu 的工作进行二次开发与系统集成

- 👉 https://github.com/DongnanHu6556/ego-planner-ros2-sim
- 👉 https://github.com/DongnanHu6556/ego-swarm-ros2
- 👉 https://github.com/ZJU-FAST-Lab/ego-planner-swarm

## 目录

- [项目简介](#项目简介)
- [系统架构](#系统架构)
- [功能包介绍](#功能包介绍)
- [依赖环境](#依赖环境)
- [安装与编译](#安装与编译)
- [启动流程](#启动流程)
- [飞行控制指令](#飞行控制指令)
- [话题说明](#话题说明)
- [目标检测模块](#目标检测模块)
- [常见问题排查](#常见问题排查)

---

## 项目简介

本项目是将 [EGO-Swarm](https://github.com/ZJU-FAST-Lab/ego-planner-swarm) 轨迹规划算法移植到 **ROS2** 环境的完整仿真系统，参考实现来自 [ego-swarm-ros2](https://github.com/DongnanHu6556/ego-swarm-ros2)。系统以 **PX4 SITL + Gazebo** 作为仿真后端，使用 **MAVROS** 和 **Micro XRCE-DDS Agent** 双通道与飞控通信，支持深度相机感知、局部地图构建和自主避障轨迹规划。

**核心特性：**

- EGO-Planner 梯度优化轨迹规划，支持动态避障
- PX4 SITL 软件在环仿真，无需真实硬件
- x500_depth 无人机模型，搭载深度相机与 IMX214 彩色相机
- MAVROS 提供飞行模式切换、位姿控制等高级接口
- Micro XRCE-DDS 提供 PX4 uORB 消息到 ROS2 话题的直接映射
- 键盘实时切换飞行模式（手动 / 定点 / Offboard / 降落）
- RViz2 可视化路径规划与点云地图
- **YOLOv8 实时目标检测，GPU 加速推理，独立 Python 虚拟环境隔离**

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        ROS2 层                               │
│                                                             │
│  ego_planner ──→ /drone_0_planning/pos_cmd                  │
│      ↑                    ↓                                 │
│  /depth_camera_bestef   offboard_control_test               │
│      ↑                    ↓                                 │
│  depth_gz_bridge     MAVROS / px4_msgs                      │
│                                                             │
│  /rgb_image ──→ detector_node (venv Python)                 │
│      ↑               ↓              ↓                       │
│  imx214_bridge  /detection_image  /detected_objects         │
└──────────────┬──────────────────────────┬───────────────────┘
               │  MAVROS (MAVLink)        │  Micro XRCE-DDS
               ↓                          ↓
┌─────────────────────────────────────────────────────────────┐
│                      PX4 SITL                               │
└──────────────────────────┬──────────────────────────────────┘
                           │ GZ Transport
┌──────────────────────────↓──────────────────────────────────┐
│               Gazebo Harmonic (gz sim)                      │
│     世界: ego.sdf  模型: gz_x500_depth                       │
│     深度相机 → /depth_camera                                  │
│     IMX214 彩色相机 → /world/.../IMX214/image                 │
└─────────────────────────────────────────────────────────────┘
```

**通信双通道说明：**

| 通道 | 协议 | 用途 |
|------|------|------|
| MAVROS | MAVLink UDP 14540 | 飞行模式切换、arm/disarm、位姿订阅 |
| Micro XRCE-DDS Agent | UDP 8888 | uORB 消息直接映射为 ROS2 话题（/fmu/*） |

---

## 功能包介绍

### `simulation_start`

仿真环境启动包，负责拉起整个仿真栈。

| 文件 | 功能 |
|------|------|
| `px4_sitl_ros2.launch.py` | 主 launch 文件，一键启动全部仿真组件 |
| `simulation_gazebo.py` | 启动 Gazebo，自动下载/检查模型文件 |
| `depth_gz_bridge.py` | 将 Gazebo 深度图（RGB编码）转换为 ROS2 标准 `32FC1` 格式 |

### `px4_offboard_control`

飞行控制包，负责 Offboard 模式下的轨迹跟踪与模式管理。

| 文件 | 功能 |
|------|------|
| `offboard_control_test.py` | 订阅 EGO-Planner 位置指令，通过 MAVROS 执行 Offboard 控制 |
| `mode_key.py` | 键盘节点，发布飞行模式切换指令到 `/mode_key` 话题 |

### `ego-swarm-ros2`（`ego_planner`）

EGO-Swarm 轨迹规划核心，基于梯度优化的局部避障规划器。接收目标点后生成平滑无碰轨迹，发布到 `/drone_0_planning/pos_cmd`。

### `object_decetion`

YOLOv8 实时目标检测包，使用 IMX214 彩色相机图像进行推理。**运行在独立 Python 虚拟环境中**，与系统 Python 环境隔离，避免依赖冲突。

| 文件 | 功能 |
|------|------|
| `object_decetion/detector.py` | YOLOv8 推理封装，与 ROS2 无关，可单独测试 |
| `object_decetion/detector_node.py` | ROS2 节点，订阅 `/rgb_image`，发布检测结果 |
| `launch/detection.launch.py` | 启动 IMX214 bridge 和检测节点 |
| `third_party/ultralytics/` | YOLOv8 v8.2.0 完整源码（含 train.py/predict.py） |
| `weights/yolov8n.pt` | 预训练权重（COCO 80类） |
| `venv/` | 独立 Python 虚拟环境（含 torch、torchvision） |
| `datasets/` | 自定义训练数据集目录 |

---

## 依赖环境

### 基础环境

| 组件 | 版本 |
|------|------|
| Ubuntu | 24.04 |
| ROS2 | Jazzy |
| Gazebo | Harmonic (gz 8.x) |
| PX4-Autopilot | 主线版本（支持 gz_x500_depth 模型） |

### ROS2 依赖包

```bash
sudo apt install \
  ros-jazzy-mavros \
  ros-jazzy-mavros-extras \
  ros-jazzy-ros-gz-bridge \
  ros-jazzy-tf2-ros \
  ros-jazzy-tf2-tools \
  ros-jazzy-rviz2 \
  ros-jazzy-vision-msgs \
  python3-cv-bridge
```

### 目标检测依赖（虚拟环境）

目标检测模块使用独立 Python 虚拟环境，**不影响系统 Python 和其他 ROS2 包**。

| 组件 | 版本 | 说明 |
|------|------|------|
| Python venv | `--system-site-packages` | 继承系统 rclpy、cv_bridge |
| torch | 2.10.0+cu128 | GPU 推理 |
| torchvision | 0.25.0 | 图像处理 |
| numpy | 1.26.4 | 与 cv_bridge 兼容（需 <2.0） |
| YOLOv8 源码 | v8.2.0 | `third_party/ultralytics/` |
| NVIDIA GPU | RTX 系列 | 推荐，CPU 也可运行 |

### 外部工具

```bash
# Micro XRCE-DDS Agent（PX4 <-> ROS2 桥接）
sudo snap install micro-xrce-dds-agent --edge
# 或从源码编译
git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git
cd Micro-XRCE-DDS-Agent && mkdir build && cd build
cmake .. && make && sudo make install

# MAVROS 地理坐标数据集
sudo /opt/ros/jazzy/lib/mavros/install_geographiclib_datasets.sh
```

---

## 安装与编译

```bash
# 1. 克隆项目
cd ~
git clone <本仓库地址> Ego-planner-stystem
cd Ego-planner-stystem

# 2. 确认 PX4-Autopilot 路径正确（launch 文件中默认为 ~/github/PX4-Autopilot）
ls ~/github/PX4-Autopilot/build/px4_sitl_default/bin/px4

# 3. 编译所有包
colcon build --symlink-install

# 4. Source 环境
source install/setup.bash
# 建议加入 ~/.bashrc
echo "source ~/Ego-planner-stystem/install/setup.bash" >> ~/.bashrc
```

### 目标检测模块额外安装步骤

> 虚拟环境（`venv/`）不上传 git，需要在本地通过脚本一键创建。

```bash
# 确保已 source ROS2 环境
source /opt/ros/jazzy/setup.bash

# 进入包目录，运行一键安装脚本
cd ~/Ego-planner-stystem/src/object_decetion
bash setup_venv.sh
```

脚本会自动完成以下步骤：

- 创建 Python 虚拟环境（`--system-site-packages` 继承 ROS2 库）
- 安装 `requirements.txt` 中的所有依赖（torch、torchvision 等）
- 确认 numpy < 2.0（与 cv_bridge 兼容）
- 克隆 YOLOv8 v8.2.0 源码（如 `third_party/ultralytics/` 不存在）
- 下载 `yolov8n.pt` 预训练权重（如 `weights/` 目录为空）
- 验证所有关键依赖是否正常

**如需手动安装（不使用脚本）：**

```bash
# 1. 创建虚拟环境
python3 -m venv ~/Ego-planner-stystem/src/object_decetion/venv \
    --system-site-packages

# 2. 激活并安装依赖
source ~/Ego-planner-stystem/src/object_decetion/venv/bin/activate
pip install -r ~/Ego-planner-stystem/src/object_decetion/requirements.txt
pip install "numpy<2.0"   # 必须 <2.0，与 cv_bridge 兼容

# 3. 克隆 YOLOv8 源码
cd ~/Ego-planner-stystem/src/object_decetion/third_party
git clone https://github.com/ultralytics/ultralytics.git
cd ultralytics && git checkout v8.2.0
# 修复 torch 2.6+ 兼容问题
sed -i 's/torch.load(file, map_location="cpu")/torch.load(file, map_location="cpu", weights_only=False)/g' \
    ultralytics/nn/tasks.py

# 4. 下载权重
wget -O ~/Ego-planner-stystem/src/object_decetion/weights/yolov8n.pt \
    https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt
```

> **注意：** 不要安装 `pip install opencv-python`，使用系统 cv2（通过 `--system-site-packages` 继承），否则会与 cv_bridge 产生 numpy 版本冲突。

```bash
# 5. 编译 object_decetion 包
cd ~/Ego-planner-stystem
colcon build --packages-select object_decetion --symlink-install
```

> **注意：** 若 PX4 路径不同，请修改 `simulation_start/launch/px4_sitl_ros2.launch.py` 中的 `PX4_DIR` 变量。

---

## 启动流程

### 第一步：确保没有残留的 Gazebo 进程

每次启动前务必清理旧进程，否则会出现双 Gazebo 实例冲突：

```bash
pkill -f "gz sim"
sleep 2
```

### 第二步：启动仿真环境

```bash
# 新终端
source ~/Ego-planner-stystem/install/setup.bash
ros2 launch simulation_start px4_sitl_ros2.launch.py
```

等待以下关键日志出现，说明仿真正常连接：

```
[px4-3] INFO  [init] Gazebo simulator 8.x.x
[px4-3] INFO  [commander] Ready for takeoff!
[mavros_node-1] [INFO] FCU: APM:Copter ...
```

### 第三步：启动 EGO-Planner 规划节点

```bash
# 新终端
source ~/Ego-planner-stystem/install/setup.bash
ros2 launch ego_planner single_uav_gazebo.launch.py
```

### 第四步：启动 Offboard 控制节点

```bash
# 新终端
source ~/Ego-planner-stystem/install/setup.bash
ros2 run px4_offboard_control offboard_control_test
```

### 第五步：启动键盘控制节点

```bash
# 新终端
source ~/Ego-planner-stystem/install/setup.bash
ros2 run px4_offboard_control mode_key
```

### 第六步：启动 RViz2 可视化

```bash
# 新终端
source ~/Ego-planner-stystem/install/setup.bash
ros2 launch ego_planner rviz.launch.py
```

### 完整启动顺序总览

```
终端1: ros2 launch simulation_start px4_sitl_ros2.launch.py   ← 仿真环境
终端2: ros2 launch ego_planner single_drone.launch.py          ← 规划器
终端3: ros2 run px4_offboard_control offboard_control_test     ← 控制器
终端4: ros2 run px4_offboard_control mode_key                  ← 键盘控制
终端5: ros2 launch ego_planner rviz.launch.py                  ← 可视化
终端6: ros2 launch object_decetion detection.launch.py         ← 目标检测（可选）
```

---

## 飞行控制指令

在 `mode_key` 节点终端中，输入字母后按回车发送指令：

| 按键 | 功能 |
|------|------|
| `m` | 切换为手动模式（Manual） |
| `p` | 切换为定点模式（Position Control） |
| `o` | 切换为 Offboard 模式（启动自主飞行） |
| `l` | 降落（Land） |

**典型飞行流程：**

```
1. 输入 p  → 切换定点模式
2. 在 QGroundControl 中 Arm 解锁
3. 输入 o  → 切换 Offboard，无人机开始自主飞行
4. 在 RViz2 中用 2D Nav Goal 点击目标点
5. EGO-Planner 自动规划轨迹并飞向目标
6. 输入 l  → 降落
```

---

## 话题说明

### 输入话题（订阅）

| 话题 | 类型 | 说明 |
|------|------|------|
| `/depth_camera` | `sensor_msgs/Image` | Gazebo 原始深度图 |
| `/drone_0_planning/pos_cmd` | 自定义 | EGO-Planner 位置指令 |
| `/mode_key` | `std_msgs/String` | 飞行模式切换指令 |
| `/mavros/state` | `mavros_msgs/State` | 飞控当前状态 |
| `/rgb_image` | `sensor_msgs/Image` | IMX214 彩色图像（目标检测输入） |

### 输出话题（发布）

| 话题 | 类型 | 说明 |
|------|------|------|
| `/depth_camera_bestef` | `sensor_msgs/Image` | 转换后的 32FC1 深度图 |
| `/mavros/setpoint_position/local` | `geometry_msgs/PoseStamped` | 位置控制目标点 |
| `/fmu/in/trajectory_setpoint` | `px4_msgs/TrajectorySetpoint` | PX4 轨迹指令 |
| `/detection_image` | `sensor_msgs/Image` | 标注检测框的彩色图像 |
| `/detected_objects` | `vision_msgs/Detection2DArray` | 检测结果（类别、置信度、bbox） |

---

## 目标检测模块

### 模块说明

目标检测模块基于 **YOLOv8 v8.2.0 源码**实现，使用无人机搭载的 IMX214 彩色相机进行实时推理。模块运行在独立 Python 虚拟环境中，与系统 ROS2 环境完全隔离。

```
object_decetion/
├── object_decetion/
│   ├── detector.py        # YOLOv8 推理封装（可单独运行测试）
│   └── detector_node.py   # ROS2 节点（虚拟环境 Python 运行）
├── launch/
│   └── detection.launch.py
├── third_party/
│   └── ultralytics/       # YOLOv8 v8.2.0 完整源码
│       ├── ultralytics/   # 核心库（models/engine/data 等）
│       ├── train.py       # 训练脚本
│       └── predict.py     # 预测脚本
├── weights/
│   └── yolov8n.pt         # 预训练权重（COCO 80类）
├── datasets/              # 自定义训练数据集目录
└── venv/                  # 独立 Python 虚拟环境
```

### 启动目标检测

```bash
# 确保仿真环境已启动（终端1已运行 px4_sitl_ros2.launch.py）
source ~/Ego-planner-stystem/install/setup.bash
ros2 launch object_decetion detection.launch.py
```

启动后可用 rqt 查看标注图像：

```bash
rqt
# Plugins → Visualization → Image View → 选择 /detection_image
```

### 启动参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `weights_path` | `weights/yolov8n.pt` | 权重文件路径，训练后改为自定义权重 |
| `conf_threshold` | `0.5` | 置信度阈值，越高误检越少 |
| `device` | `cuda:0` | 推理设备，无 GPU 改为 `cpu` |

```bash
# 示例：使用自定义权重和更高置信度阈值
ros2 launch object_decetion detection.launch.py \
  weights_path:=/path/to/best.pt \
  conf_threshold:=0.7 \
  device:=cuda:0
```

### 单独测试推理（不启动 ROS2）

```bash
source ~/Ego-planner-stystem/src/object_decetion/venv/bin/activate

python3 ~/Ego-planner-stystem/src/object_decetion/object_decetion/detector.py \
    --image /path/to/test.jpg \
    --conf 0.5 \
    --device cpu

# 结果保存至 /tmp/yolov8_result.jpg
```

### 自定义模型训练

#### 数据集准备

按 YOLOv8 标准格式组织数据集：

```
datasets/my_dataset/
├── images/
│   ├── train/    ← 训练图像（.jpg/.png）
│   └── val/      ← 验证图像
├── labels/
│   ├── train/    ← 标注文件（.txt，每行: class_id cx cy w h）
│   └── val/
└── data.yaml
```

`data.yaml` 示例：

```yaml
path: /home/guo/Ego-planner-stystem/src/object_decetion/datasets/my_dataset
train: images/train
val:   images/val
nc: 2
names: ['person', 'obstacle']
```

#### 训练命令

```bash
source ~/Ego-planner-stystem/src/object_decetion/venv/bin/activate

cd ~/Ego-planner-stystem/src/object_decetion/third_party/ultralytics

python3 train.py \
    --data ../../datasets/my_dataset/data.yaml \
    --model ../../weights/yolov8n.pt \
    --epochs 100 \
    --imgsz 640 \
    --batch 16 \
    --device 0 \
    --project ../../weights/runs \
    --name my_model
```

训练完成后权重位于：

```
weights/runs/my_model/weights/best.pt
```

将 `detection.launch.py` 中的 `weights_path` 改为 `best.pt` 路径即可使用自定义模型。

### numpy 版本说明

虚拟环境中 numpy 必须保持 `<2.0`，否则与系统 cv_bridge 冲突：

```bash
source venv/bin/activate
pip install "numpy<2.0"
# 不要安装 pip 版 opencv-python，使用系统 cv2（通过 system-site-packages 继承）
```

---

### Gazebo 启动后 PX4 一直 "Waiting for Gazebo world"

**原因：** 存在多个 Gazebo 实例冲突，或 `simulation_gazebo.py` 未正确安装。

```bash
# 检查是否有残留进程
ps aux | grep gz
# 全部杀掉
pkill -f "gz sim"
# 检查脚本是否安装
ls install/simulation_start/share/simulation_start/simulation_gazebo.py
```

### QGroundControl 显示位置异常（高度 -2536 万米）

**原因：** PX4 连接的是旧的 Gazebo 实例，传感器数据异常。

```bash
pkill -f "gz sim" && pkill -f px4
# 重新启动
ros2 launch simulation_start px4_sitl_ros2.launch.py
```

### `ros2 run px4_offboard_control offboard_control_test` 提示 "No executable found"

**原因：** setuptools 新版本将下划线转为横线，可执行文件生成在 `px4-offboard-control/` 目录。

```bash
# 在 setup.cfg 中添加以下内容
cat >> src/px4-ego-start/px4_offboard_control/setup.cfg << 'EOF'

[develop]
script_dir=$base/lib/px4_offboard_control
[install]
install_scripts=$base/lib/px4_offboard_control
EOF

# 重新编译
rm -rf build/px4_offboard_control install/px4_offboard_control
colcon build --packages-select px4_offboard_control --symlink-install
source install/setup.bash
```

### `detector_node` 启动报 `numpy` 版本冲突

**原因：** 虚拟环境里 numpy >= 2.0，与系统 cv_bridge 不兼容。

```bash
source ~/Ego-planner-stystem/src/object_decetion/venv/bin/activate
pip install "numpy<2.0"
# 验证
python3 -c "import cv_bridge; import numpy as np; print('OK, numpy:', np.__version__)"
```

### `setup_venv.sh` 提示 "未检测到 ROS2 环境"

```bash
source /opt/ros/jazzy/setup.bash
# 再运行脚本
bash ~/Ego-planner-stystem/src/object_decetion/setup_venv.sh
```

### `detector_node` 报 `ModuleNotFoundError: No module named 'cpuinfo'`

```bash
source ~/Ego-planner-stystem/src/object_decetion/venv/bin/activate
pip install py-cpuinfo
```

### RViz2 不显示坐标轴 / Fixed Frame 报错

**原因：** TF 树断链，`map → odom → base_link` 链路不完整。

```bash
# 查看 TF 树
ros2 run tf2_tools view_frames
# 确认 Fixed Frame 名称
ros2 topic echo /tf --once
```

将 RViz2 左侧 **Global Options → Fixed Frame** 设置为 `map`，并确保 ego_planner 和 offboard_control 节点均已启动。

---

## 项目结构

```
Ego-planner-stystem/
├── src/
│   ├── ego-swarm-ros2/              # EGO-Planner ROS2 移植版本
│   │   └── ego_planner/             # 核心规划包
│   ├── object_decetion/             # YOLOv8 目标检测包
│   │   ├── launch/
│   │   │   └── detection.launch.py  # 检测模块启动文件
│   │   ├── object_decetion/
│   │   │   ├── detector.py          # YOLOv8 推理封装
│   │   │   └── detector_node.py     # ROS2 检测节点
│   │   ├── third_party/
│   │   │   └── ultralytics/         # YOLOv8 v8.2.0 源码
│   │   ├── weights/
│   │   │   └── yolov8n.pt           # 预训练权重
│   │   ├── datasets/                # 训练数据集目录
│   │   ├── requirements.txt         # 虚拟环境依赖清单
│   │   ├── setup_venv.sh            # 一键创建虚拟环境脚本
│   │   └── venv/                    # 独立 Python 虚拟环境（不上传 git）
│   └── px4-ego-start/
│       ├── simulation_start/        # 仿真环境启动包
│       │   ├── launch/
│       │   │   └── px4_sitl_ros2.launch.py
│       │   └── simulation_start/
│       │       ├── simulation_gazebo.py
│       │       └── depth_gz_bridge.py
│       └── px4_offboard_control/    # 飞行控制包
│           └── px4_offboard_control/
│               ├── offboard_control_test.py
│               └── mode_key.py
├── build/
├── install/
└── log/
```

---

## 参考资料

- [EGO-Planner-Swarm 原版 (ROS1)](https://github.com/ZJU-FAST-Lab/ego-planner-swarm)
- [ego-swarm-ros2 移植版](https://github.com/DongnanHu6556/ego-swarm-ros2)
- [PX4 官方文档](https://docs.px4.io/main/en/)
- [MAVROS 文档](https://github.com/mavlink/mavros)
- [Micro XRCE-DDS Agent](https://github.com/eProsima/Micro-XRCE-DDS-Agent)
- [ROS2 Jazzy 文档](https://docs.ros.org/en/jazzy/)
