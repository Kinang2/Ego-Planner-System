#include <rclcpp/rclcpp.hpp>
#include "drone_detect/drone_detector.h"


int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<detect::DroneDetector>("drone_detect");
    node->test();
    spin(node);
    rclcpp::shutdown();
    return 0;
}
