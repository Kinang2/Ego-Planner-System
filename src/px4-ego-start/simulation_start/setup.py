from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'simulation_start'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch',glob("launch/*.launch.py")),
        ('share/' + package_name, ['simulation_start/simulation_gazebo.py']),
        ('share/' + package_name, ['simulation_start/depth_gz_bridge.py']),

    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='guo',
    maintainer_email='13137076637@163.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'depth_gz_bridge=simulation_start.depth_gz_bridge:main',
            'simulation_gazebo=simulation_start.simulation_gazebo:main',
        ],
    },
)
