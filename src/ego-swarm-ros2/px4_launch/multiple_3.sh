cd ~/PX4-Autopilot/ || exit
gnome-terminal \
 --tab --title="Drone 2" -e 'bash -c "PX4_SYS_AUTOSTART=4001 PX4_GZ_MODEL_POSE="0,1" PX4_SIM_MODEL=gz_x500_depth ./build/px4_sitl_default/bin/px4 -i 2"'\
 --tab --title="Drone 3" -e 'bash -c "PX4_SYS_AUTOSTART=4001 PX4_GZ_MODEL_POSE="0,2" PX4_SIM_MODEL=gz_x500_depth ./build/px4_sitl_default/bin/px4 -i 3"'\
 --tab --title="Drone 4" -e 'bash -c "PX4_SYS_AUTOSTART=4001 PX4_GZ_MODEL_POSE="0,3" PX4_SIM_MODEL=gz_x500_depth ./build/px4_sitl_default/bin/px4 -i 4"'
