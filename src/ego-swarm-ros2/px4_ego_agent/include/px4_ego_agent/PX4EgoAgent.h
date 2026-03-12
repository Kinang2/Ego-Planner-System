//
// Created by biao on 3/5/25.
//

#ifndef PX4EGOAGENT_H
#define PX4EGOAGENT_H


#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>

#include "OffBoardControl.h"

class PX4EgoAgent final : public rclcpp::Node
{
public:
    PX4EgoAgent();
    void init();
private:
    std::string drone_name_;

    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr gcs_cmd_sub_;

    std::shared_ptr<OffBoardControl> offboard_control_;
};


#endif //PX4EGOAGENT_H
