#!/usr/bin/env bash

# Set variables
PYTHON3_VERSION="python3.8"

# Install core dependencies
sudo apt-get update
sudo apt-get install -y curl git vim

# Setup new ROS key + install ros packages
#sudo apt-key del 421C365BD9FF1F717815A3895523BAEEB01FA116
#sudo apt-key adv --keyserver 'hkp://keyserver.ubuntu.com:80' --recv-key C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654
sudo apt-get update && apt-get upgrade -y
sudo apt-get install -y \
     ros-$ROS_DISTRO-ros-control \
     ros-$ROS_DISTRO-ros-controllers \
     ros-$ROS_DISTRO-gazebo-ros-pkgs \
     ros-$ROS_DISTRO-gazebo-ros-control \
     ros-$ROS_DISTRO-rosbridge-server \
     ros-$ROS_DISTRO-audio-common \
     ros-$ROS_DISTRO-mongodb-store \
     ros-$ROS_DISTRO-mongodb-log

# Setup Cordial dependencies
sudo apt-get install -y \
	alsa \
	gstreamer1.0-alsa \
	vorbis-tools \
	awscli \
	ffmpeg

# Setup Python2 - for Cordial
sudo apt-get update && sudo apt-get install -y \
	python3-scipy \
	python3-pyaudio
# python3 -m pip install --upgrade pip==20.3.3

# Setup Python3 - for the vision project
sudo apt-get install -y \
	software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y 
sudo apt-get update
sudo apt-get install -y \
	${PYTHON3_VERSION} \
	${PYTHON3_VERSION}-dev \
	${PYTHON3_VERSION}-venv

# Setup pip3
curl https://bootstrap.pypa.io/get-pip.py | sudo ${PYTHON3_VERSION}
${PYTHON3_VERSION} -m pip install --user \
	rospkg \
	catkin_pkg \
	awscli \
	freezegun==1.0.0 \
	robotpt_common_utils==0.0.8 \
	schedule==0.6.0 \
	pydub==0.25.1 \
	pymongo==3.11.4 \
	discord.py==1.7.1 \
	speechrecognition \
	webrtcvad \
	rospkg \
	catkin_pkg \
	boto3==1.12.11 \
	soundfile==0.10.3.post1 \
	speedtest-cli==2.1.2
