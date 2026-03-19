from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'object_decetion'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='guo',
    maintainer_email='guo@todo.todo',
    description='YOLOv8目标检测ROS2节点（使用YOLOv8源码）',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'detector_node = object_decetion.detector_node:main',
        ],
    },
)
