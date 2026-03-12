# EGO Planner Swarm 原理梳理

对于每一个仿真的飞机，需要有5个节点

* ego_planner_node
* traj_server
* odom_visualization
* pcl_render_node
* poscmd_2_odom

## Ego planner node

订阅信息：

* 全局坐标系下（frame=world）的里程计信息
* 地图坐标系下（frame=map）的点云信息
* 如果是集群仿真，需要接收其他飞机的预测轨迹（Bspline）