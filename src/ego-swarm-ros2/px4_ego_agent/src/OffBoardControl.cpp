//
// Created by tlab-uav on 25-3-5.
//

#include "px4_ego_agent/OffBoardControl.h"


#include <px4_msgs/msg/offboard_control_mode.hpp>
#include <px4_msgs/msg/trajectory_setpoint.hpp>
#include <px4_msgs/msg/vehicle_command.hpp>
#include <rclcpp/rclcpp.hpp>
#include <cstdint>
#include <utility>

using namespace std::chrono;
using namespace std::chrono_literals;
using namespace px4_msgs::msg;


OffBoardControl::OffBoardControl(rclcpp::Node::SharedPtr node): node_(std::move(node))
{
    offboard_control_mode_publisher_ = node_->create_publisher<OffboardControlMode>(
        "fmu/in/offboard_control_mode", 10);
    trajectory_setpoint_publisher_ = node_->create_publisher<TrajectorySetpoint>("fmu/in/trajectory_setpoint", 10);
    vehicle_command_publisher_ = node_->create_publisher<VehicleCommand>("fmu/in/vehicle_command", 10);

    system_id_ = node_->get_parameter("system_id").as_int();

    auto timer_callback = [this]() -> void {
        // offboard_control_mode needs to be paired with trajectory_setpoint
        publishOffBoardControlMode();
        target_.timestamp = node_->now().nanoseconds() / 1000;
        trajectory_setpoint_publisher_->publish(target_);
    };
    timer_ = node_->create_wall_timer(100ms, timer_callback);
}

void OffBoardControl::takeOff(float height)
{
    RCLCPP_INFO(node_->get_logger(), "Taking Off to %f meters", height);

    target_.position = {0.0, 0.0, -height};
    target_.yaw = -3.14; // [-PI:PI]

    // Change to Offboard mode after 10 setpoints
    publishVehicleCommand(VehicleCommand::VEHICLE_CMD_DO_SET_MODE, 1, 6);

    // Arm the vehicle
    arm();
}

void OffBoardControl::land() const
{
    publishVehicleCommand(VehicleCommand::VEHICLE_CMD_DO_LAND_START, 0, 0);
    RCLCPP_INFO(node_->get_logger(), "Landing Mode");
}

/**
 * @brief Send a command to Arm the vehicle
 */
void OffBoardControl::arm() const
{
    publishVehicleCommand(VehicleCommand::VEHICLE_CMD_COMPONENT_ARM_DISARM, 1.0);
    RCLCPP_INFO(node_->get_logger(), "Arm command send");
}

/**
 * @brief Send a command to Disarm the vehicle
 */
void OffBoardControl::disarm() const
{
    publishVehicleCommand(VehicleCommand::VEHICLE_CMD_COMPONENT_ARM_DISARM, 0.0);
    RCLCPP_INFO(node_->get_logger(), "Disarm command send");
}

/**
 * @brief Publish the offboard control mode.
 *        For this example, only position and altitude controls are active.
 */
void OffBoardControl::publishOffBoardControlMode()
{
    OffboardControlMode msg{};
    msg.position = true;
    msg.velocity = false;
    msg.acceleration = false;
    msg.attitude = false;
    msg.body_rate = false;
    msg.timestamp = node_->now().nanoseconds() / 1000;
    offboard_control_mode_publisher_->publish(msg);
}

/**
 * @brief Publish a trajectory setpoint
 *        For this example, it sends a trajectory setpoint to make the
 *        vehicle hover at 5 meters with a yaw angle of 180 degrees.
 */
void OffBoardControl::publishTrajectorySetpoint()
{
    TrajectorySetpoint msg{};
    msg.position = {0.0, 0.0, -5.0};
    msg.yaw = -3.14; // [-PI:PI]
    msg.timestamp = node_->now().nanoseconds() / 1000;
    trajectory_setpoint_publisher_->publish(msg);
}

/**
 * @brief Publish vehicle commands
 * @param command   Command code (matches VehicleCommand and MAVLink MAV_CMD codes)
 * @param param1    Command parameter 1
 * @param param2    Command parameter 2
 */
void OffBoardControl::publishVehicleCommand(uint16_t command, float param1, float param2) const
{
    auto msg = VehicleCommand();
    msg.param1 = param1;
    msg.param2 = param2;
    msg.command = command;
    msg.target_system = system_id_;
    msg.target_component = 1;
    msg.source_system = 1;
    msg.source_component = 1;
    msg.from_external = true;
    msg.timestamp = node_->now().nanoseconds() / 1000;
    vehicle_command_publisher_->publish(msg);
}
