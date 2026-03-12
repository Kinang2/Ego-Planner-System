cmake_minimum_required(VERSION 3.8)
project(drone_detect)

if (CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    add_compile_options(-Wall -Wextra -Wpedantic)
endif ()

set(CMAKE_BUILD_TYPE Release)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)


# find dependencies
find_package(ament_cmake REQUIRED)
find_package(cv_bridge REQUIRED)
set(dependencies
        rclcpp
        std_msgs
        sensor_msgs
        nav_msgs
        geometry_msgs
        std_srvs
        cv_bridge
        Eigen3
        OpenCV
        Boost
        message_filters
)

foreach (Dependency IN ITEMS ${dependencies})
    find_package(${Dependency} REQUIRED)
endforeach ()

add_executable(drone_detect
  src/${PROJECT_NAME}_node.cpp
  src/drone_detector.cpp
)
target_include_directories(${PROJECT_NAME}
        PUBLIC
        ${EIGEN3_INCLUDE_DIR}
        ${Boost_INCLUDE_DIRS}
        ${OpenCV_INCLUDE_DIRS}
        "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
        "$<INSTALL_INTERFACE:include/${PROJECT_NAME}>")
ament_target_dependencies(
        ${PROJECT_NAME} PUBLIC
        ${dependencies}
)

# Install targets
install(
  TARGETS drone_detect
  DESTINATION lib/${PROJECT_NAME}
)

# Install headers
install(
  DIRECTORY include/${PROJECT_NAME}/
  DESTINATION include/${PROJECT_NAME}
  FILES_MATCHING PATTERN "*.h"
)

# Install additional resources
install(
  DIRECTORY doc
  DESTINATION share/${PROJECT_NAME}
)

# 安装 launch 文件
install(
  DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

# 安装config
install(DIRECTORY config DESTINATION share/${PROJECT_NAME})

# Enable testing
# if(BUILD_TESTING)
#   find_package(ament_cmake_gtest REQUIRED)
#   ament_add_gtest(${PROJECT_NAME}-test
#     test/test_drone_detector.cpp
#   )
#   ament_target_dependencies(${PROJECT_NAME}-test rclcpp sensor_msgs nav_msgs geometry_msgs std_srvs cv_bridge Eigen3 OpenCV Boost message_filters)
# endif()

ament_package()
