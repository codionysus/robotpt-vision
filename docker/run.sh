#!/bin/bash

# Go to the directory of this file -- needed for docker-compose
FILE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $FILE_DIR

if [ -z ${1+x} ];
then
	MODE="popup";
else
	MODE=$1;
fi

SERVICE_NAME="vision_project_dev"
ROS_MASTER_URI=$ROS_MASTER_URI docker compose up --build
case "$MODE" in
	run | start | up )
		ROS_MASTER_URI=$ROS_MASTER_URI docker compose run -d $SERVICE_NAME bash -c "source ~/catkin_ws/devel/setup.bash && roslaunch ros_vision_interaction vision_project.launch"
		;;
	terminal | terminal_debug | t )
		# ROS_MASTER_URI=$ROS_MASTER_URI docker-compose run $SERVICE_NAME bash -c "source ~/catkin_ws/devel/setup.bash && bash"
		ROS_MASTER_URI=$ROS_MASTER_URI docker compose run $SERVICE_NAME bash
		;;
	stop | kill | down )
		docker compose down
		;;
	terminator | popup )
		xhost +local: # share display on ubuntu platforms
		ROS_MASTER_URI=$ROS_MASTER_URI docker compose run $SERVICE_NAME bash -c "terminator -e \"echo 'Entering Docker Container...' && bash\""
		;;
	* )
		echo "Not a valid command"
		;;
esac
