//
// Created by biao on 3/5/25.
//

#include "px4_ego_agent/PX4EgoAgent.h"
#include <boost/algorithm/string.hpp>

int main(int argc, char* argv[])
{
    setvbuf(stdout, NULL, _IONBF, BUFSIZ);
    rclcpp::init(argc, argv);
    auto node = std::make_shared<PX4EgoAgent>();
    node->init();
    spin(node);

    rclcpp::shutdown();
    return 0;
}

PX4EgoAgent::PX4EgoAgent() : Node("px4_ego_agent")
{
    declare_parameter("drone_name", drone_name_);
    declare_parameter("system_id", 1);

    drone_name_ = get_parameter("drone_name").as_string();

    RCLCPP_INFO(get_logger(), "Starting PX4 Ego Planner Agent Node ...");
}

void PX4EgoAgent::init()
{
    offboard_control_ = std::make_shared<OffBoardControl>(shared_from_this());
    gcs_cmd_sub_ = create_subscription<std_msgs::msg::String>
    ("/gcs/command", 10,
     [this](const std_msgs::msg::String::SharedPtr msg)
     {
         std::vector<std::string> commands;
         split(commands, msg->data, boost::is_any_of(","));
         if (commands.size() < 0) return;
         if (commands[0] == "Take Off")
         {
             offboard_control_->takeOff(std::stof(commands[1]));
         } else if (commands[0] == "Land")
         {
             offboard_control_->land();
         } else if (commands[0] == "Disarm")
         {
             offboard_control_->disarm();
         }
     });
}
