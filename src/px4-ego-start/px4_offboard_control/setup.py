from setuptools import find_packages, setup

package_name = 'px4_offboard_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name, ['px4_offboard_control/mode_key.py']),
        ('share/' + package_name, ['px4_offboard_control/offboard_control_test.py']),
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
            'mode_key=px4_offboard_control.mode_key:main',
            'offboard_control_test=px4_offboard_control.offboard_control_test:main',
        ],
    },
)
