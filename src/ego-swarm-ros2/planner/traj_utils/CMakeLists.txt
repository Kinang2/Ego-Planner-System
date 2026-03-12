cmake_minimum_required(VERSION 3.8)
project(traj_utils)

if (CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    add_compile_options(-Wall -Wextra -Wpedantic)
endif ()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_BUILD_TYPE Release)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# find dependencies
find_package(ament_cmake REQUIRED)
set(dependencies
        rclcpp
        std_msgs
        visualization_msgs
        geometry_msgs
        builtin_interfaces
)
foreach (Dependency IN ITEMS ${dependencies})
    find_package(${Dependency} REQUIRED)
endforeach ()
find_package(rosidl_default_generators REQUIRED)

find_package(Eigen3 REQUIRED)
find_package(PCL REQUIRED)

rosidl_generate_interfaces(traj_utils
        "msg/Bspline.msg"
        "msg/DataDisp.msg"
        "msg/MultiBsplines.msg"
        DEPENDENCIES ${dependencies}
)

add_library(${PROJECT_NAME}_lib SHARED
        src/planning_visualization.cpp
        src/polynomial_traj.cpp
)
target_include_directories(${PROJECT_NAME}_lib PUBLIC
        ${Eigen3_INCLUDE_DIRS}
        ${PCL_INCLUDE_DIRS}
        "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
        "$<INSTALL_INTERFACE:include/${PROJECT_NAME}>")
ament_target_dependencies(
        ${PROJECT_NAME}_lib PUBLIC
        ${dependencies} Eigen3 PCL
)

install(TARGETS ${PROJECT_NAME}_lib
        EXPORT export_${PROJECT_NAME}_lib
        DESTINATION lib
)
install(DIRECTORY include/
        DESTINATION include/${PROJECT_NAME}
)

ament_export_targets(export_${PROJECT_NAME}_lib HAS_LIBRARY_TARGET)
ament_export_dependencies(${dependencies} Eigen3 PCL)

ament_package()
