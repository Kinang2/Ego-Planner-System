cmake_minimum_required(VERSION 3.8)
project(px4_ego_agent)

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
        px4_msgs
        quadrotor_msgs
        Boost
)
foreach (Dependency IN ITEMS ${dependencies})
    find_package(${Dependency} REQUIRED)
endforeach ()

add_library(${PROJECT_NAME}
        src/OffBoardControl.cpp
)

target_include_directories(${PROJECT_NAME}
        PUBLIC
        ${Boost_INCLUDE_DIRS}
        "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
        "$<INSTALL_INTERFACE:include/${PROJECT_NAME}>")

ament_target_dependencies(${PROJECT_NAME} ${dependencies} Boost)

add_executable(${PROJECT_NAME}_node src/PX4EgoAgent.cpp)
target_link_libraries(${PROJECT_NAME}_node ${PROJECT_NAME})

install(
        TARGETS ${PROJECT_NAME}
        EXPORT export_${PROJECT_NAME}
        DESTINATION lib
)

install(
        TARGETS
        ${PROJECT_NAME}_node
        DESTINATION lib/${PROJECT_NAME}
)

install(
        DIRECTORY launch
        DESTINATION share/${PROJECT_NAME}/
)

if (BUILD_TESTING)
    find_package(ament_lint_auto REQUIRED)
    # the following line skips the linter which checks for copyrights
    # comment the line when a copyright and license is added to all source files
    set(ament_cmake_copyright_FOUND TRUE)
    # the following line skips cpplint (only works in a git repo)
    # comment the line when this package is in a git repo and when
    # a copyright and license is added to all source files
    set(ament_cmake_cpplint_FOUND TRUE)
    ament_lint_auto_find_test_dependencies()
endif ()

ament_export_targets(export_${PROJECT_NAME} HAS_LIBRARY_TARGET)
ament_export_dependencies(${dependencies})

ament_package()
