# syntax=docker/dockerfile:1

# sim과 moveit 두 서비스가 이미지 하나를 공유한다.
# ROBOTIS의 docker/Dockerfile은 실기 전용
FROM ros:jazzy-ros-base

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-colcon-common-extensions \
        python3-vcstool \
        python3-rosdep \
        git \
        # --- 시뮬레이션 ---
        ros-jazzy-ros-gz \
        ros-jazzy-gz-ros2-control \
        # --- 제어 ---
        ros-jazzy-ros2-control \
        ros-jazzy-dynamixel-sdk \
        ros-jazzy-ros2-controllers \
        # --- 플래닝 / 시각화 ---
        ros-jazzy-moveit \
        ros-jazzy-rviz2 \
        # --- 기술 ---
        ros-jazzy-xacro \
        ros-jazzy-robot-state-publisher \
        ros-jazzy-joint-state-publisher \
        ros-jazzy-joint-state-publisher-gui \
        ros-jazzy-realsense2-description \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ws

RUN echo 'source /opt/ros/jazzy/setup.bash' >> /root/.bashrc \
 && echo '[ -f /ws/install/setup.bash ] && source /ws/install/setup.bash' >> /root/.bashrc

CMD ["sleep", "infinity"]
