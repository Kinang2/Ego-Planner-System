#!/usr/bin/env python3
############################################################################
#
#   Copyright (C) 2022 PX4 Development Team. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 3. Neither the name PX4 nor the names of its contributors may be
#    used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
############################################################################

import rclpy
import numpy as np
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy, QoSDurabilityPolicy
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleStatus, VehicleLocalPosition, VehicleCommand, VehicleOdometry
from quadrotor_msgs.msg import PositionCommand
from std_msgs.msg import String
import math


class OffboardControl(Node):

    def __init__(self):
        super().__init__('ego_pos_command_publisher')

                # QoS profiles
        qos_profile_pub = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=0
        )

        qos_profile_sub = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=0
        )

        self.status_sub = self.create_subscription(
            VehicleStatus,
            'fmu/out/vehicle_status',
            self.vehicle_status_callback,
            qos_profile_sub)
        self.status_sub = self.create_subscription(
            VehicleStatus,
            'fmu/out/vehicle_status_v1',
            self.vehicle_status_callback,
            qos_profile_sub)
        self.vehicle_local_position_sub = self.create_subscription(
            VehicleLocalPosition, '/fmu/out/vehicle_local_position_v1', self.vehicle_local_position_callback, qos_profile_sub)
        self.vehicle_visual_odom_sub = self.create_subscription(
            VehicleOdometry, '/fmu/in/vehicle_visual_odometry', self.vehicle_visual_odom_callback, qos_profile_sub)
        self.planning_pos_cmd_sub = self.create_subscription(
            PositionCommand,'/drone_0_planning/pos_cmd', self.planning_pos_cmd_callback, qos_profile_sub)
        self.mode_cmd_sub = self.create_subscription(
            String, '/mode_key', self.mode_cmd_callback, qos_profile_sub)

        self.publisher_offboard_mode = self.create_publisher(OffboardControlMode, 'fmu/in/offboard_control_mode', qos_profile_pub)
        self.publisher_trajectory = self.create_publisher(TrajectorySetpoint, 'fmu/in/trajectory_setpoint', qos_profile_pub)
        self.publisher_vehicle_command = self.create_publisher(VehicleCommand, '/fmu/in/vehicle_command', qos_profile_pub)

        self.control_mode = 'm'
        self.offboard_setpoint_counter = 0
        self.land_trigger_counter = 0
        self.vehicle_local_position = VehicleLocalPosition()
        self.vehicle_visual_odom = VehicleOdometry()
        self.vehicle_status = VehicleStatus()

        timer_period = 0.02  # seconds
        self.timer = self.create_timer(timer_period, self.cmdloop_callback)
        self.dt = timer_period
        self.nav_state = VehicleStatus.NAVIGATION_STATE_MAX
        self.arming_state = VehicleStatus.ARMING_STATE_DISARMED
        self.vehicle_local_position_received = False
        self.vehicle_visual_odom_received = False
        self.planning_pos_command_received = False
        self.takeoff_hover_des_set = False
        self.offboard_hover_des_set = False
        self.hover_setpoint = TrajectorySetpoint()
        # Note: no parameter callbacks are used to prevent sudden inflight changes of radii and omega
        # which would result in large discontinuities in setpoints
        self.theta = 0.0
        self.latest_planning_msg = None
        self.ros_to_fmu = np.array([
            [0, 1, 0],
            [1, 0, 0],
            [0, 0, -1]
        ])
    def quaternion_to_yaw(self, w, x, y, z):
        # yaw (Z axis rotation)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        return math.atan2(siny_cosp, cosy_cosp)

    def vehicle_status_callback(self, msg):
        # TODO: handle NED->ENU transformation
        # print("NAV_STATUS: ", msg.nav_state)
        # print("  - offboard status: ", VehicleStatus.NAVIGATION_STATE_OFFBOARD)
        self.nav_state = msg.nav_state
        self.arming_state = msg.arming_state
        self.vehicle_status = msg
    
    def vehicle_visual_odom_callback(self, msg):
        self.vehicle_visual_odom = msg
        self.vehicle_visual_odom_received = True

    def planning_pos_cmd_callback(self, msg):
        self.latest_planning_msg = msg
        self.planning_pos_command_received = True

    def vehicle_local_position_callback(self, vehicle_local_position):
        """Callback function for vehicle_local_position topic subscriber."""
        self.vehicle_local_position = vehicle_local_position
        self.vehicle_local_position_received = True
    
    def mode_cmd_callback(self, msg):
        self.control_mode = msg.data
    
    def publish_offboard_control_heartbeat_signal(self):
        """Publish the offboard control mode."""
        msg = OffboardControlMode()
        msg.position = True
        msg.velocity = False
        msg.acceleration = False
        msg.attitude = False
        msg.body_rate = False
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.publisher_offboard_mode.publish(msg)

    def engage_offboard_mode(self):
        """Switch to offboard mode."""
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_DO_SET_MODE, param1=1.0, param2=6.0)
        self.get_logger().info("Switching to offboard mode")
    
    def enter_position_mode(self):
        """Exit offboard mode and switch to position mode."""
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_DO_SET_MODE,
            param1=1.0,   # 1 = custom mode
            param2=4.0    # 4 = POSITION mode
        )
        self.get_logger().info("Exiting OFFBOARD mode → Switching to POSITION mode")
    
    def arm(self):
        """Send an arm command to the vehicle."""
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, param1=1.0)
        self.get_logger().info('Arm command sent')

    def takeoff(self):
        """Takeoff to a specified altitude (default 1m)."""
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_NAV_TAKEOFF, param7=-1.0)
        self.get_logger().info(f"Taking off to 1.0 meters")
    
    def land(self):
        """Switch to land mode."""
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_NAV_LAND)
        self.get_logger().info("Switching to land mode")

    def disarm(self):
        """Send a disarm command to the vehicle."""
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, param1=0.0)
        self.get_logger().info('Disarm command sent')
    
    def publish_vehicle_command(self, command, **params) -> None:
        """Publish a vehicle command."""
        msg = VehicleCommand()
        msg.command = command
        msg.param1 = params.get("param1", 0.0)
        msg.param2 = params.get("param2", 0.0)
        msg.param3 = params.get("param3", 0.0)
        msg.param4 = params.get("param4", 0.0)
        msg.param5 = params.get("param5", 0.0)
        msg.param6 = params.get("param6", 0.0)
        msg.param7 = params.get("param7", 0.0)
        msg.target_system = 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.publisher_vehicle_command.publish(msg)

    def position_msg_pub(self):
        msg = TrajectorySetpoint()
        if (self.vehicle_local_position_received and not self.vehicle_visual_odom_received):
            if not self.takeoff_hover_des_set:
                self.hover_setpoint.position[0] = self.vehicle_local_position.x 
                self.hover_setpoint.position[1] = self.vehicle_local_position.y 
                self.hover_setpoint.position[2] = -0.9
                self.hover_setpoint.yaw = self.vehicle_local_position.heading
                self.takeoff_hover_des_set = True
            if self.takeoff_hover_des_set:
                msg.position = self.hover_setpoint.position
                msg.yaw = self.hover_setpoint.yaw
        elif (self.vehicle_visual_odom_received):
            if not self.takeoff_hover_des_set:
                self.hover_setpoint.position[0] = self.vehicle_visual_odom.position[0]
                self.hover_setpoint.position[1] = self.vehicle_visual_odom.position[1]
                self.hover_setpoint.position[2] = -0.9
                q_att = self.vehicle_visual_odom.q
                self.hover_setpoint.yaw = self.quaternion_to_yaw(q_att[0],q_att[1],q_att[2],q_att[3])
                self.takeoff_hover_des_set = True
            if self.takeoff_hover_des_set:
                msg.position = self.hover_setpoint.position
                msg.yaw = self.hover_setpoint.yaw
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.publisher_trajectory.publish(msg)
    
    # VehicleLocalPosition /fmu/out/vehicle_local_position_v1 for simulation
    # VehicleOdometry /fmu/in/vehicle_visual_odometry for real experiment
    def hover_cmd_pub(self):
        msg = TrajectorySetpoint()
        if (self.vehicle_local_position_received and not self.vehicle_visual_odom_received):
            if not self.offboard_hover_des_set:
                self.hover_setpoint.position[0] = self.vehicle_local_position.x
                self.hover_setpoint.position[1] = self.vehicle_local_position.y
                self.hover_setpoint.position[2] = self.vehicle_local_position.z
                self.hover_setpoint.yaw = self.vehicle_local_position.heading
                self.offboard_hover_des_set = True
            if self.offboard_hover_des_set:
                msg.position = self.hover_setpoint.position
                msg.yaw = self.hover_setpoint.yaw
        elif (self.vehicle_visual_odom_received):
            if not self.offboard_hover_des_set:
                self.hover_setpoint.position[0] = self.vehicle_visual_odom.position[0]
                self.hover_setpoint.position[1] = self.vehicle_visual_odom.position[1]
                self.hover_setpoint.position[2] = self.vehicle_visual_odom.position[2]
                q_att = self.vehicle_visual_odom.q
                self.hover_setpoint.yaw = self.quaternion_to_yaw(q_att[0],q_att[1],q_att[2],q_att[3])
                self.offboard_hover_des_set = True
            if self.offboard_hover_des_set:
                msg.position = self.hover_setpoint.position
                msg.yaw = self.hover_setpoint.yaw
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.publisher_trajectory.publish(msg)
    
    def ego_cmd_pub(self):
        msg = TrajectorySetpoint()
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        planning_position = np.array([self.latest_planning_msg.position.x, 
                                    self.latest_planning_msg.position.y, 
                                    self.latest_planning_msg.position.z])
        planning_velocity = np.array([self.latest_planning_msg.velocity.x,
                                    self.latest_planning_msg.velocity.y,
                                    self.latest_planning_msg.velocity.z])
        inv_ros_to_fmu = np.linalg.inv(self.ros_to_fmu)
        planning_position = inv_ros_to_fmu @ planning_position
        planning_velocity = inv_ros_to_fmu @ planning_velocity
        msg.position[0] = planning_position[0]
        msg.position[1] = planning_position[1]
        msg.position[2] = planning_position[2]
        msg.velocity[0] = planning_velocity[0]
        msg.velocity[1] = planning_velocity[1]
        msg.velocity[2] = planning_velocity[2]
        yaw_enu = self.latest_planning_msg.yaw
        msg.yaw = np.arctan2(np.cos(yaw_enu),np.sin(yaw_enu))
        # msg.yaw = np.arccos(np.sin(self.latest_planning_msg.yaw))
        self.publisher_trajectory.publish(msg)
    
    def ego_vel_cmd_pub(self):
        msg = TrajectorySetpoint()
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        planning_position = np.array([self.latest_planning_msg.position.x, 
                                    self.latest_planning_msg.position.y, 
                                    self.latest_planning_msg.position.z])
        planning_velocity = np.array([self.latest_planning_msg.velocity.x,
                                    self.latest_planning_msg.velocity.y,
                                    self.latest_planning_msg.velocity.z])
        inv_ros_to_fmu = np.linalg.inv(self.ros_to_fmu)
        planning_position = inv_ros_to_fmu @ planning_position
        planning_velocity = inv_ros_to_fmu @ planning_velocity
        # msg.position[0] = planning_position[0]
        # msg.position[1] = planning_position[1]
        # msg.position[2] = planning_position[2]
        # msg.velocity[0] = planning_velocity[0]
        # msg.velocity[1] = planning_velocity[1]
        # msg.velocity[2] = planning_velocity[2]
        current_position = np.array([0.0, 0.0, 0.0])
        if (self.vehicle_local_position_received and not self.vehicle_visual_odom_received):
            current_position[0] = self.vehicle_local_position.x
            current_position[1] = self.vehicle_local_position.y
            current_position[2] = self.vehicle_local_position.z
        elif (self.vehicle_visual_odom_received):
            current_position[0] = self.vehicle_visual_odom.position[0]
            current_position[1] = self.vehicle_visual_odom.position[1]
            current_position[2] = self.vehicle_visual_odom.position[2]
        msg.position[0] = float('nan')
        msg.position[1] = float('nan')
        msg.position[2] = float('nan')
        msg.velocity[0] = 0.98* (planning_position[0] - current_position[0]) + planning_velocity[0]
        msg.velocity[1] = 0.98* (planning_position[1] - current_position[1]) + planning_velocity[1]
        msg.velocity[2] = 1.00* (planning_position[2] - current_position[2]) + planning_velocity[2]
        yaw_enu = self.latest_planning_msg.yaw
        msg.yaw = np.arctan2(np.cos(yaw_enu),np.sin(yaw_enu))
        # msg.yaw = np.arccos(np.sin(self.latest_planning_msg.yaw))
        self.publisher_trajectory.publish(msg)

    def cmdloop_callback(self):
        self.publish_offboard_control_heartbeat_signal()
        if self.control_mode == 'm':
            self.get_logger().info("manual control")
            return

        if self.control_mode == 't':
            if self.nav_state != VehicleStatus.NAVIGATION_STATE_OFFBOARD:
                # self.publish_offboard_control_heartbeat_signal()
                self.engage_offboard_mode()
            if self.arming_state != VehicleStatus.ARMING_STATE_ARMED:
                self.arm()
            self.offboard_hover_des_set = False
            self.position_msg_pub()
            self.get_logger().info("takeoff")
            return

        if self.control_mode == 'p':
            self.takeoff_hover_des_set = False
            self.hover_cmd_pub()
            self.get_logger().info("position mode")
            return

        if (self.control_mode == 'o' and not self.planning_pos_command_received):
            self.in_position_hold = True
            # self.enter_position_mode()
            self.takeoff_hover_des_set = False
            self.hover_cmd_pub()
            self.get_logger().info("No command in offboard, return to position mode")
            return

        if (self.control_mode == 'o' and self.planning_pos_command_received):
            if self.nav_state != VehicleStatus.NAVIGATION_STATE_OFFBOARD:
                # self.publish_offboard_control_heartbeat_signal()
                self.engage_offboard_mode()
            if (self.nav_state == VehicleStatus.NAVIGATION_STATE_OFFBOARD):
                    # self.rate_setpoint_msg_pub()
                    # self.position_msg_pub()
                    if self.latest_planning_msg is not None:
                        self.offboard_hover_des_set = False
                        self.takeoff_hover_des_set = False
                        self.ego_cmd_pub()
                        self.get_logger().info("offboard velocity")
                        return
                    else:
                        self.in_position_hold = True
                        # self.enter_position_mode()
                        self.hover_cmd_pub()
                        self.get_logger().info("hhhhh")
                        return
        
        if self.control_mode == 'l':
            self.land()
            return
        
        if self.control_mode == 'd':
            self.disarm()
            return


def main(args=None):
    rclpy.init(args=args)

    offboard_control = OffboardControl()

    rclpy.spin(offboard_control)

    offboard_control.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()