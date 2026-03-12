cmake_minimum_required(VERSION 3.8)
project(quadrotor_msgs)

# find dependencies
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
        "msg/AuxCommand.msg"
        "msg/Corrections.msg"
        "msg/Gains.msg"
        "msg/LQRTrajectory.msg"
        "msg/OutputData.msg"
        "msg/PositionCommand.msg"
        "msg/PPROutputData.msg"
        "msg/Serial.msg"
        "msg/SO3Command.msg"
        "msg/StatusData.msg"
        "msg/TRPYCommand.msg"
        "msg/Odometry.msg"
        "msg/PolynomialTrajectory.msg"
        DEPENDENCIES geometry_msgs nav_msgs std_msgs
)

# 将该包对应的依赖导出，其他包在调用是会自动依赖
ament_export_dependencies(geometry_msgs nav_msgs std_msgs)
ament_package()
