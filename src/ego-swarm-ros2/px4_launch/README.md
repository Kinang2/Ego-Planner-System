# Launch PX4 ROS2 Gazebo simulation

## Install PX4

### Get PX4 source code and build
I prefer to place PX4 repository at home directory, you can choose any location you like.
```bash
cd ~
git clone https://github.com/PX4/PX4-Autopilot.git --recursive
bash ./PX4-Autopilot/Tools/setup/ubuntu.sh
```
### Validate PX4 Gazebo simulation
```bash
cd ~/PX4-Autopilot
make px4_sitl gz_x500
```
### Prepare PX4 Multi-Vehicle Simulation
```bash
cd ~/PX4-Autopilot
make px4_sitl
```

### Setup Micro XRCE-DDS Agent & Client
```bash
# choose a location to place the Micro XRCE-DDS Agent source code.
git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git
cd Micro-XRCE-DDS-Agent
mkdir build
cd build
cmake ..
make
sudo make install
sudo ldconfig /usr/local/lib/
```

### use instruction 
run single.sh first, only run multiple.sh after the single initialize finished.