import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch.substitutions import PythonExpression
from launch.conditions import IfCondition, UnlessCondition
from launch.actions import LogInfo


def generate_launch_description():
    # LaunchConfiguration definitions
    map_size_x = LaunchConfiguration('map_size_x', default=40.0)
    map_size_y = LaunchConfiguration('map_size_y', default=20.0)
    map_size_z = LaunchConfiguration('map_size_z', default=4.0)
    init_x = LaunchConfiguration('init_x', default=0.0)
    init_y = LaunchConfiguration('init_y', default=0.0)
    init_z = LaunchConfiguration('init_z', default=0.0)
    target_x = LaunchConfiguration('target_x', default=20.0)
    target_y = LaunchConfiguration('target_y', default=20.0)
    target_z = LaunchConfiguration('target_z', default=1.0)
    drone_id = LaunchConfiguration('drone_id', default=0)
    odom_topic = LaunchConfiguration('odom_topic', default='/mavros/local_position/odom')
    depth_topic = LaunchConfiguration('depth_topic', default='/depth_camera_bestef')
    cloud_topic = LaunchConfiguration('cloud_topic', default='/disabled_cloud_unused')
    # goal_pose = LaunchConfiguration('goal_pose', default='/goal_pose')

    # DeclareLaunchArgument definitions
    map_size_x_cmd = DeclareLaunchArgument('map_size_x', default_value=map_size_x, description='Map size along x')
    map_size_y_cmd = DeclareLaunchArgument('map_size_y', default_value=map_size_y, description='Map size along y')
    map_size_z_cmd = DeclareLaunchArgument('map_size_z', default_value=map_size_z, description='Map size along z')
    init_x_cmd = DeclareLaunchArgument('init_x', default_value=init_x, description='Initial x position of the drone')
    init_y_cmd = DeclareLaunchArgument('init_y', default_value=init_y, description='Initial y position of the drone')
    init_z_cmd = DeclareLaunchArgument('init_z', default_value=init_z, description='Initial z position of the drone')
    target_x_cmd = DeclareLaunchArgument('target_x', default_value=target_x, description='Target x position')
    target_y_cmd = DeclareLaunchArgument('target_y', default_value=target_y, description='Target y position')
    target_z_cmd = DeclareLaunchArgument('target_z', default_value=target_z, description='Target z position')
    drone_id_cmd = DeclareLaunchArgument('drone_id', default_value=drone_id, description='ID of the drone')
    odom_topic_cmd = DeclareLaunchArgument('odom_topic', default_value=odom_topic, description='Odometry topic')
    depth_topic_cmd = DeclareLaunchArgument('depth_topic', default_value=depth_topic, description='Depth Camera topic')
    cloud_topic_cmd = DeclareLaunchArgument('cloud_topic', default_value=cloud_topic, description='Lidar Cloud topic')

    use_dynamic = LaunchConfiguration('use_dynamic', default=True)  
    use_dynamic_cmd = DeclareLaunchArgument('use_dynamic', default_value=use_dynamic, description='Use Drone Simulation Considering Dynamics or Not')

    world2map_static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="world_to_map_broadcaster",
        output="screen",
        arguments=[
            "0", "0", "0",
            "0", "0", "0",
            "world", "map"
        ]
    )

    odom2baselink_static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="odom_to_base_broadcaster",
        output="screen",
        arguments=[
            "0", "0", "0",
            "0", "0", "0",
            "odom", "base_link"
        ]
    )

    # Jazzy fix: 补充 world→odom 的 TF，否则 grid_map 查询坐标系失败导致段错误
    world2odom_static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="world_to_odom_broadcaster",
        output="screen",
        arguments=[
            "0", "0", "0",
            "0", "0", "0",
            "world", "odom"
        ]
    )

    # Jazzy fix: 补充 base_link→camera_link 的 TF
    # 相机安装位置：x=0.12, y=0.03, z=0.242（来自无人机 SDF 配置）
    baselink2camera_static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="base_to_camera_broadcaster",
        output="screen",
        arguments=[
            "0.12", "0.03", "0.242",
            "-1.5708", "0", "0",
            "base_link", "camera_link"
        ]
    )

    # Include advanced parameters
    advanced_param_include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('ego_planner'), 'launch', 'advanced_param.launch.py')),
        launch_arguments={
            'drone_id': drone_id,
            'map_size_x_': map_size_x,
            'map_size_y_': map_size_y,
            'map_size_z_': map_size_z,
            'odometry_topic': odom_topic,
            'depth_topic': depth_topic,
            'cloud_topic': cloud_topic,
            
            'max_vel': str(0.8),
            'max_acc': str(1.0),
            'planning_horizon': str(7.5),
            'use_distinctive_trajs': 'True',
            'flight_type': str(1),
            'point_num': str(4),
            'point0_x': str(5.0),
            'point0_y': str(0.0),
            'point0_z': str(1.0),
            
            'point1_x': str(-5.0),
            'point1_y': str(0.0),
            'point1_z': str(1.0),
            
            'point2_x': str(5.0),
            'point2_y': str(0.0),
            'point2_z': str(1.0),
            
            'point3_x': str(-5.0),
            'point3_y': str(0.0),
            'point3_z': str(1.0),
            
            'point4_x': str(5.0),
            'point4_y': str(0.0),
            'point4_z': str(1.0),
        }.items()
    )

    # Trajectory server node
    traj_server_node = Node(
        package='ego_planner',
        executable='traj_server',
        name=['drone_', drone_id, '_traj_server'],
        output='screen',
        remappings=[
            ('position_cmd', ['drone_', drone_id, '_planning/pos_cmd']),
            ('planning/bspline', ['drone_', drone_id, '_planning/bspline'])
        ],
        parameters=[
            {'traj_server/time_forward': 1.0}
        ]
    )

    ld = LaunchDescription()

    # Add Node
    ld.add_action(advanced_param_include)
    ld.add_action(world2map_static_tf)
    ld.add_action(world2odom_static_tf)
    ld.add_action(baselink2camera_static_tf)
    ld.add_action(odom2baselink_static_tf)
    ld.add_action(traj_server_node)

    return ld