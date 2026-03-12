cd ~/PX4-Autopilot/ || exit
gnome-terminal \
 --tab --title="XRCE Agent" -e 'bash -c "MicroXRCEAgent udp4 -p 8888; exec bash"' \
 --tab --title="Drone 1" -e 'bash -c "PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=gz_x500_depth ./build/px4_sitl_default/bin/px4 -i 0; exec bash"'

