cmake_minimum_required(VERSION 3.8)
project(ego_planner)

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
        quadrotor_msgs
        bspline_opt
)
foreach (Dependency IN ITEMS ${dependencies})
    find_package(${Dependency} REQUIRED)
endforeach ()

include_directories(
        include
        SYSTEM
        ${EIGEN3_INCLUDE_DIR}
        ${PCL_INCLUDE_DIRS}
)

add_executable(ego_planner_node
        src/ego_planner_node.cpp
        src/ego_replan_fsm.cpp
        src/planner_manager.cpp
)
target_include_directories(ego_planner_node PUBLIC
        "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
        "$<INSTALL_INTERFACE:include/${PROJECT_NAME}>")
ament_target_dependencies(
        ego_planner_node
        ${dependencies}
)

add_executable(traj_server src/traj_server.cpp)
target_include_directories(traj_server PUBLIC
        "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
        "$<INSTALL_INTERFACE:include/${PROJECT_NAME}>")
ament_target_dependencies(traj_server
        ${dependencies})

install(
        TARGETS ego_planner_node traj_server
        DESTINATION lib/${PROJECT_NAME}
)

install(
        DIRECTORY launch
        DESTINATION share/${PROJECT_NAME}/
)

ament_package()
