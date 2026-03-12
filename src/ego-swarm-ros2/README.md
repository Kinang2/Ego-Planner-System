# ego-swarm-ros2
The repository comes from https://github.com/legubiao/ego-swarm-ros2, I revised the "qos" in grid_map.cpp and add my own ego planner launch files.
```
mkdir -p ego_ws/src
cd ego_ws/src
git clone https://github.com/DongnanHu6556/ego-swarm-ros2.git
cd ..
colcon build
```
Then you can launch the planner:
```
source install/setup.bash
ros2 launch ego_planner single_uav_gazebo.launch.py
```
Before the autonomous navigation, the drone need to takeoff and switch to offboard mode in gazebo. For specific steps, please follow the repository https://github.com/DongnanHu6556/ego-planner-ros2-sim/tree/main.

Launch rviz:
```
source install/setup.bash
ros2 launch ego_planner rviz.launch.py 
```
Use "2D Goal Pose" to publish the target.
<img width="1831" height="958" alt="Screenshot 2026-01-01 21:21:05" src="https://github.com/user-attachments/assets/6903858b-2572-4f49-891b-d7d6409104e6" />
