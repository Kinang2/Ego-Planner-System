
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

VENV_PYTHON = os.path.expanduser(
    '~/Ego-planner-stystem/src/object_decetion/venv/bin/python3'
)
DETECTOR_SCRIPT = os.path.expanduser(
    '~/Ego-planner-stystem/src/object_decetion/object_decetion/detector_node.py'
)

def generate_launch_description():

    # ── Bridge：IMX214 → /rgb_image ───────────────────────────────
    imx214_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='imx214_rgb_bridge',
        arguments=[
            '/world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/image'
            '@sensor_msgs/msg/Image[gz.msgs.Image',
        ],
        remappings=[
            ('/world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/image',
             '/rgb_image')
        ],
        output='screen'
    )

    # ── YOLOv8 检测节点（虚拟环境 Python）────────────────────────
    detector_proc = ExecuteProcess(
        cmd=[
            VENV_PYTHON,
            DETECTOR_SCRIPT,
            '--ros-args',
            '-p', 'weights_path:=/home/guo/Ego-planner-stystem/src/object_decetion/weights/yolov8n.pt',
            '-p', 'conf_threshold:=0.5',
            '-p', 'device:=cuda:0',
            '-p', 'image_topic:=/rgb_image',
        ],
        output='screen'
    )

    ld = LaunchDescription()
    ld.add_action(imx214_bridge)
    ld.add_action(detector_proc)
    return ld
