
#include <rclcpp/rclcpp.hpp>
#include <ego_planner/ego_replan_fsm.h>

using namespace ego_planner;

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<rclcpp::Node>("ego_planner_node");

    EGOReplanFSM rebo_replan;
    rebo_replan.init(node);

    // Jazzy fix: 用 MultiThreadedExecutor 显式管理节点
    // 不能再调用 spin(node)，因为 init() 内部已经使用了 spin_some(node_)
    rclcpp::executors::MultiThreadedExecutor executor;
    executor.add_node(node);
    executor.spin();

    rclcpp::shutdown();
    return 0;
}
