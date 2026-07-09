# 작업 지시서
# 실제로 만들어 내느 경로
# 패키지가 설치된 경로를 찾아 헤더, 라이브러리 위치를 변수에 담아라.

cmake_minimum_required(VERSION 3.8)
project(arm_interfaces)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(builtin_interfaces REQUIRED)

# Generate C++/Python types for these interfaces. Both the agent (client) and
# motion (server) depend on this package, so the contract lives here once.
rosidl_generate_interfaces(${PROJECT_NAME}
  # 메시지
  "msg/ErrorCode.msg"
  "msg/FailureReport.msg"
  # 액션
  "action/Pick.action"
  "action/Place.action"
  DEPENDENCIES geometry_msgs std_msgs
)

ament_export_dependencies(rosidl_default_runtime)

ament_package()
