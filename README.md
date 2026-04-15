# Ego-Planner-System

> 基于 ROS2 + PX4 + Gazebo 的无人机自主规划与仿真系统，集成 EGO-Swarm 轨迹规划算法、深度相机感知与 Offboard 飞行控制。

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

---


## 目录

- [项目简介](#项目简介)
- [系统架构](#系统架构)
- [功能包介绍](#功能包介绍)
- [依赖环境](#依赖环境)
- [安装与编译](#安装与编译)
- [启动流程](#启动流程)
- [飞行控制指令](#飞行控制指令)
- [话题说明](#话题说明)
- [常见问题排查](#常见问题排查)

---

## 项目简介

本项目是将 [EGO-Swarm](https://github.com/ZJU-FAST-Lab/ego-planner-swarm) 轨迹规划算法移植到 **ROS2** 环境的完整仿真系统，参考实现来自 [ego-swarm-ros2](https://github.com/DongnanHu6556/ego-swarm-ros2)。系统以 **PX4 SITL + Gazebo** 作为仿真后端，使用 **MAVROS** 和 **Micro XRCE-DDS Agent** 双通道与飞控通信，支持深度相机感知、局部地图构建和自主避障轨迹规划。

**核心特性：**

- EGO-Planner 梯度优化轨迹规划，支持动态避障
- PX4 SITL 软件在环仿真，无需真实硬件
- x500_depth 无人机模型，搭载深度相机
- MAVROS 提供飞行模式切换、位姿控制等高级接口
- Micro XRCE-DDS 提供 PX4 uORB 消息到 ROS2 话题的直接映射
- 键盘实时切换飞行模式（手动 / 定点 / Offboard / 降落）
- RViz2 可视化路径规划与点云地图

---

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                     ROS2 层                              │
│                                                         │
│  ego_planner ──→ /drone_0_planning/pos_cmd              │
│      ↑                    ↓                             │
│  /depth_camera_bestef   offboard_control_test           │
│      ↑                    ↓                             │
│  depth_gz_bridge     MAVROS / px4_msgs                  │
└──────────────┬────────────────────┬────────────────────┘
               │  MAVROS (MAVLink)  │  Micro XRCE-DDS
               ↓                    ↓
┌─────────────────────────────────────────────────────────┐
│                    PX4 SITL                             │
└──────────────────────────┬──────────────────────────────┘
                           │ GZ Transport
┌──────────────────────────↓──────────────────────────────┐
│               Gazebo Harmonic (gz sim)                  │
│           世界: ego.sdf  模型: gz_x500_depth             │
└─────────────────────────────────────────────────────────┘
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
  python3-cv-bridge
```

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

### 输出话题（发布）

| 话题 | 类型 | 说明 |
|------|------|------|
| `/depth_camera_bestef` | `sensor_msgs/Image` | 转换后的 32FC1 深度图 |
| `/mavros/setpoint_position/local` | `geometry_msgs/PoseStamped` | 位置控制目标点 |
| `/fmu/in/trajectory_setpoint` | `px4_msgs/TrajectorySetpoint` | PX4 轨迹指令 |

---

## 常见问题排查

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
│   ├── ego-swarm-ros2/          # EGO-Planner ROS2 移植版本
│   │   └── ego_planner/         # 核心规划包
│   └── px4-ego-start/
│       ├── simulation_start/    # 仿真环境启动包
│       │   ├── launch/
│       │   │   └── px4_sitl_ros2.launch.py
│       │   └── simulation_start/
│       │       ├── simulation_gazebo.py
│       │       └── depth_gz_bridge.py
│       └── px4_offboard_control/ # 飞行控制包
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
