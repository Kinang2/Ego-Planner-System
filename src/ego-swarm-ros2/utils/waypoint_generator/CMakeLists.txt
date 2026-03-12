cmake_minimum_required(VERSION 3.8)
project(waypoint_generator)

if (CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    add_compile_options(-Wall -Wextra -Wpedantic)
endif ()

set(CMAKE_BUILD_TYPE Release)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# find dependencies
find_package(ament_cmake REQUIRED)
set(dependencies
        rclcpp
        tf2
        tf2_geometry_msgs
        nav_msgs
)
foreach (Dependency IN ITEMS ${dependencies})
    find_package(${Dependency} REQUIRED)
endforeach ()

add_executable(waypoint_generator src/waypoint_generator.cpp)
target_include_directories(waypoint_generator
        PUBLIC
        "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
        "$<INSTALL_INTERFACE:include/${PROJECT_NAME}>")
ament_target_dependencies(
        ${PROJECT_NAME} PUBLIC
        ${dependencies}
)

install(TARGETS waypoint_generator
        DESTINATION lib/${PROJECT_NAME}
)

ament_package()
