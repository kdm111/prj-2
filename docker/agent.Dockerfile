# syntax=docker/dockerfile:1

# Base image: ROS 2 Jazzy (ros-base variant) on Ubuntu 24.04.
# ros-base already ships rclpy, the `ros2` CLI, and the DDS middleware,
# so the agent can act as a ROS 2 action client out of the box.
FROM ros:jazzy-ros-base

# Don't let apt stop for interactive prompts (tzdata, etc.) during build.
ARG DEBIAN_FRONTEND=noninteractive

# Dev tooling:
#   - colcon: builds our workspace (src/*)
#   - pip / venv: for pure-Python deps later (e.g. the LLM client)
#   - git: convenience inside the container
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-pip \
        python3-venv \
        python3-colcon-common-extensions \
        git \
    && rm -rf /var/lib/apt/lists/*

# The repo gets bind-mounted here by compose, so host edits are live inside.
WORKDIR /ws

# Make interactive shells (`docker compose exec agent bash`) auto-source ROS,
# plus our workspace overlay once it has been built.
RUN echo 'source /opt/ros/jazzy/setup.bash' >> /root/.bashrc \
 && echo '[ -f /ws/install/setup.bash ] && source /ws/install/setup.bash' >> /root/.bashrc

# Keep the container alive so we can exec into it during development.
# (Actual ROS nodes are launched by hand in later steps, not baked in yet.)
CMD ["sleep", "infinity"]
