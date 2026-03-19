from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    # 获取当前功能包的 share 路径
    pkg_share = get_package_share_directory('simulation_start')
    
    # 1. MAVROS 启动命令 (注意一定要写 cmd=)
    mavros_start_cmd = ExecuteProcess(
        cmd=["ros2 launch mavros px4.launch fcu_url:=udp://:14540@127.0.0.1:14555"],
        output="both",
        shell=True
    )

    # 2. Micro XRCE Agent (PX4 <-> ROS2)
    micro_xrce_start_cmd = ExecuteProcess(
        cmd=['MicroXRCEAgent', 'udp4', '-p', '8888'],
        output='screen'
    )

    # 3. PX4 路径配置
    PX4_DIR = os.path.expanduser('~/github/PX4-Autopilot')
    PX4_BIN = os.path.join(PX4_DIR, 'build/px4_sitl_default/bin/px4')

    # 4. PX4 实例启动
    px4_instance0 = ExecuteProcess(
        cmd=[PX4_BIN, '-i', '0'],
        additional_env={
            'PX4_GZ_STANDALONE': '1',
            'PX4_SYS_AUTOSTART': '4001',
            'PX4_GZ_MODEL_POSE': '-6,0',
            'PX4_SIM_MODEL': 'gz_x500_depth'
        },
        output='screen'
    )

    # 5. Gazebo 启动脚本
    script_path = os.path.join(pkg_share, 'simulation_gazebo.py')
    gazebo_simulation_cmd = ExecuteProcess(
        cmd=['python3', script_path],
        output='screen'
    )

    # 6. Bridge 1: 深度图 (Gazebo -> ROS2)
    depth_bridge_node = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='depth_camera_bridge',
        arguments=['/depth_camera@sensor_msgs/msg/Image[gz.msgs.Image'],
        output='screen'
    )

    #桥接彩色相机
    imx214_bridge_node = Node(
    package='ros_gz_bridge',
    executable='parameter_bridge',
    name='imx214_bridge',
    arguments=[
        '/world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/image'
        '@sensor_msgs/msg/Image[gz.msgs.Image',
    ],
    output='screen'
    )


    # # 7. Bridge 2: 深度相机点云 (Gazebo -> ROS2)
    # depth_points_bridge_node = Node(
    #     package='ros_gz_bridge',
    #     executable='parameter_bridge',
    #     name='depth_points_bridge',
    #     arguments=['/depth_camera/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked'],
    #     output='screen'
    # )

    # 8. 深度图编码转换脚本 (将原始图转为 32FC1)
    depth_bridge_script = os.path.join(pkg_share, 'depth_gz_bridge.py')
    best_effort_depth_img_pub = ExecuteProcess(
        cmd=['python3', depth_bridge_script],
        output='screen'
    )

    return LaunchDescription([
        mavros_start_cmd,
        gazebo_simulation_cmd,
        px4_instance0,
        micro_xrce_start_cmd,
        depth_bridge_node,
        # depth_points_bridge_node,
        imx214_bridge_node,
        best_effort_depth_img_pub,
    ])