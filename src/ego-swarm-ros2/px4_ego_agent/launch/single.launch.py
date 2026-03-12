from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='px4_ego_agent',
            executable='px4_ego_agent_node',
            namespace= 'px4_1',
            parameters=[
                {'system_id': 2}
            ]
        )
    ])
