# prj-2

## 1일차
agent.Dockerfile 생성
* 사용자 명령 해석
* 어떤 팔을 움직일 지 계산


로봇이 동작할 액션 인터페이스 생성
* Pick : 물건을 집는 동작

**TIL**

*패키지와 노드의 정확한 구분*

패키지
 * 정체성 : 빌드, 배포의 단위.
 * 정적 : 디스크에 존재한다.
 * 하는 일 : 코드를 담고, 빌드되고, 설치, 공유
 * 명령 : `colcon build`, `ros2 pkg list`

노드
 * 정체성 : 실제로 돌아가는 프로세스 하나
 * 성격 : 동적(실행 중), 메모리에 있음.
 * 하는 일 : 토픽 주고 받고, 액션 서버/클라이언트로 일한다.
 * 명령 : `ros2 run`, `ros2 node list`


*설계 시 기준*

노드 : 한 문장으로 설명 되는 역할. 이 노드는 어떤걸 구독해 어떤걸 발행한다.
1. 책임이 다른가? : 카메라(30hz 루프), 명령당 LLM 계획은 1번
2. 따로 죽거나 재시작 해도 괜찮나? : 추론이 멈춰도 LLM 에이전트는 살아야 한다.
3. 다른 머신이나 컨테이너로 갈 수 있나? : 제어(MCU), agent(PC or Jetson)

패키지 : 의존성, 공유, 언어, 환경에 따라 판단한다.
1. 여러 노드가 공유하고 있나? : 독립 패키지(인터페이스)
2. 의존성이 무겁거나 다른가? : MoveIt <> LLM 
3. 언어가 다른가? : C++(ament_cmake) <> Python(ament_python)
4. 따로 빌드하거나 재사용, 배포해야하는가?  

따라서 인터페이스를 따로 빼야 하는 이유는 agent가 타입을 사용하기 위해 motion에 의존해야 한다. 순환 의존을 방지하기 위해서라도 따로 빼야 한다. 

인터페이스 패키지 : node 0개, bringup 패키지 : node 0개


*CMAkeLists와 packages.xml이 하는 일*

이 두 파일이 존재해야, 패키지가 선언될 수 있다.

package.xml : 나는 누구이고 무엇이 필요한가? : 패키지의 선언
패키지의 이름(name)(colcon의 기준), 패키지의 의존성(depend), 빌드 타입(build-type)이 정의 된다.

CMakeLists : 나를 이렇게 만들어라. 작업 지시 파일
이름(project), 의존성(find_package), 진짜 일(rosidl_generate_interfaces). 

빌드 했는데도 이전 패키지가 남아 있을 경우
`rm -rf build/ log/ install/` 깨끗이 처음부터 다시 빌드한다.
 

*도커의 바인드 마운트*
compose.yaml의 한 줄
volumes: ./:/ws 프로젝트 폴더를 도커의 /ws로 연결한다. 


*노드 생성 시 필요한 파일 정리*
arm_agent패키지 안에 arm_agent파이썬 모듈 정의

package.xml : ros 신분증. 이 폴더를 ROS 패키지로 인식시키는 파일
읽는 파일 : colcon(빌드 순서, 이름), rosdep(의존성)

setup.py : 빌드 방법, 진입점 정의
파이썬 패키지를 어떻게 설치, 빌드하는지 정의
entry_points : 함수를 실행 파일로 만듦

setup.cfg : 실행 파일을 어디에 설치할지 정의
실행파일을 lib/arm_agent에 설치
ros2 run은 실행파일을 install/package/lib/package 안에서 찾는다.

resource/arm_agent(빈 파일) :
ament는 설치된 패키지 목록을 색인으로 관리한다. 자기 이름의 빈 파일을 색인 폴더에 만들면서 "arm_agent 패키지 있음"의 표시로 ros2 pkg list / ros2 run이 빠르게 찾는다. "존재 자체가 의미"

arm_agent/__init_-.py : 
파이썬 패키지다 표시. 파이썬 규칙으로 import가 가능하고 비어 있어도 이 파일이 모듈로 인식될수 있도록 표시



## 2일차

1. 액션 계약 확정
LLM 에이전트가 tool 스키마가 스킬 서버 인터페이스에 묶여있게 설계 되어 확정했다.
Pick/Place/MoveTo 액션의 결과를 success와 FailureReport로 통일했다. 이걸로 실패의 정보 출처를 하나로 통일하였다.
MoveTo는 SRDF에 이름 붙인 관절값으로 이동한다. 목표가 이미 관절 공간에 있으므로 IK를 풀지 않는다. 다만 현재 자세는 매번 다르므로 경로는 매 호출마다 플래너가 새로 생성한다. 
애초에 못잡는 GRASP_FAILED와 놓치는 GRIPPER_EMPTY를 분리하였다. 서로의 복구 동작을 다르게 할 계획이다.
goal에 시도횟수 attempt를 추가하였다. AI Agent가 가지고 있고, 서버는 오직 실행만 한다.

2. 로보티즈의 스택을 그대로 사용하기 위해 조사하여 의존성을 설치했다.

3. 컨테이너 구조
gazebo와 moveit을 띄우려면 ros:jazzy-ros-base에 없는 게 많다. move_group은 자주 재시작하는데 gazebo까지 죽으면 씬이 초기화된다.
sim/moveit 두 서비스가 동일한 sim 이미지를 공유한다. 

Dockerfile : 레시피 : 우분투 깔고 읽고 등등
이미지 : 다 만들어진 파일시스템 스냅샷 이를 통해 docker build가 보고 만든다.
컨테이너 : 이미지를 실행한 프로세스
서비스 : compose의 선언. 이 이미지로 이런 이름의 컨테이너를 이 볼륨과 이 환경 변수로 띄워라. 

세 컨테이너가 같은 브릿지 네트워크에 있고 ROS_DOMAIN_ID가 같다. 

4. 벤더 스택 실행
벤더 : 자기 회사 로봇을 ROS에서 쓸 수 있도록 같이 배포하는 소프트웨어 묶음. 그것이 벤더 스택
/ws에서 실행하는 소프트웨어는 출처가 세 갈래이다.

나의 코드
 * arm_interfaces # 내가 정의한 인터페이스
 * arm_agent : LLM 에이전트
벤더 스택 src/third_party
 * open_manipulator_description : URDF/xacro, 메시, 링크 치수
 * open_manipulator_bringup : launch, hardware_controller
 * open_manipulator_moveit_config : SRDF, kinematics.yaml, ompl_planning
 * dynamixel_hardware_interface : ros2_control의 hardware_interface 구현체. read()/write()를 DYNAMIXEL Protocol 2.0 패킷으로 번역. 
 * dynamixel_interfaces : 위에서 사용되는 메시지와 서비스의 정의
오픈소스 생태계 apt
 * ros2_control, joint_trajectory_controller, GripperActionController
 * MovIt2, OMPL
 * Gazebo Harmonic, gz_ros2_control, ros_gz_bridge
 * DDS(rmw)
커널 : 호스트 우분투

벤더 스택이 오픈소스 생태계에 관절은 5개이고 조인트 리밋은 이거고, 컨트로러는 이렇게 붙여라. 를 알려준다.
데이터에 가까우며, URDF, SRDF, YAML, launch

Gazebo는 sim에 설치, move_group과 Rviz는 moveit에 두 컨테이너는 파일시스템과 프로세스 공간이 격리되어 있다.

DDS가 컨테이너의 경계를 넘어 moveit의 move_group이 sim의 /joint_states를 보고, /arm_controller/follow_joint_trajectory 액션 서버를 찾아 궤적을 보낸다.

MoveIt 썼습니다에서
**MoveIt의 OMPL 플래너가 만든 궤적을 우리 스킬 서버가 액션으로 받아 실행하고, 실패 시 FailureReport로 구조화해서 에이전트에 올립니다.**

로봇 회사의 OMX 스택을 무수정으로 재사용하되, 실행환경을 도커 컴포즈의 두 컨테이너로 분리한다. 컨테이너 경계를 넘어 DDS 디스커버리가 동작함을 확인하고, RViz에서 plan & Execute한 궤적이 Gazebo의 팔을 움직이는 것으로 스택 전체가 연결됨을 검증했다. 직접 작성한 것은 Dockerfile, compose 정의, 의존성 고정(.repos)이며 로봇 설정 파일은 고치지 않았다.

5. MoveIt2를 이루는 파일들
MoveIt2는 여러 설정 파일을 조립해서 move_group이라는 노드를 만들어내는 프레임워크. omx_f_moveit.launch.py, MoveItConfigsBuilder 가하는 일이 그 조립이다.

1. URDF - 로봇의 몸
URDF는 링크(뼈)와 조인트(관절)의 트리로 이루어여 있다.
링크 이름, 관절 이름/타입/축/한계, 오프셋, 관성(mass, inertia), 충돌 형상, 시각 메시. **로봇이 물리적으로 어떻게 생겼는가?**
```
<joint name="" type=""> 
  <origin xyz="0 0 0.01">
  <limit>
</joint>
```
name이라는 회전관절이고 부모로부터 10mm 올라간 곳에 붙어 있다.
origind은 링크의 치수이다. 관절에서 나오는 **origin 링크의 치수들을 통해 해석적 IK를 유도**할 수 있다.
순기구학(FK)는 오프셋 값들을 관절각으로 회전시켜 차례로 곱해 나가는 것이고, 역기구학(IK)는 그 반대를 푸는 것이다.

2. SRDF(Semantic Robot Description Format) - URDF만으로 설명이 안되는 것들
이 로봇을 어떻게 다룰지에 대한 의미론(semantics)

그룹 : 어느 관절들을 한 덩어리로 계획할 것인가?
```
<group name="arm"> joint1~5 + end_effector_joint
<group name="gripper"> gripper_joint_1, gripper_joint_2
```
URDF는 관절 8개가 트리로 연결되어 있다는 것만 알고 있다. 팔 5개는 같이 계획하고 그리퍼는 따로다 라는 걸 쓸 자리가 없다.


명명 자세(group state) : MoveTo의 target_name
```
<group_state name="home" group="arm">
  <joint name="joint2" value="-1.57">
```
MoveTo 액션이 조회할 표.

수동 관절 
```
<passive_joint name="gripper_joint_2">
```
이 관절은 모터가 없다. 따라 움직인다. 그래서 gripper_controller가 gripoper_joint_1 하나만 잡는다.

가상 관절
```
<virtual_joint name="world_fixed" type="fixed" parent_frame="world" child_link="link0"/>
```
로봇 밑동은 세상에 고정되어 있다. 모바일 로봇이라면 floating이 된다.

충돌 무시 쌍
link2, link3은 항상 붙어 있으니 충돌 검사에서 빼라. 이게 없으면 플래너가 자기 자신과 충돌한다고 판단해서 경로를 찾을 수 없다.

3. kinematics.yaml : IK를 누가 푸는가
```
arm:
  kinematics_solver : kdl_kinematics_plugin/KDLKinematicsPlugin
  kenematics_solver_timeout: 0.005
  position_only_ik: True
```
KDLKinematicsPlugin은 수치해석적 IK이다. 해를 유도하는 것이 아니라 목표에 가까워질 때까지 조금씩 고쳐나간다. 초기 값에 따라 성공 실패가 나뉘고, 같은 목표를 두 번 풀면 다른 답이 나올 수 있다. 나의 해석적 IK가 비교당할 상대.

벤더의 `kinematics.yaml`은 `position_only_ik: True` 5축으로는 6D 포즈를 만족할 수 없어 방향 제약을 통째로 포기한 설정이다. 피킹에는 부적합하므로 해석적 IK로 대체한다.
하지만 피킹의 경우 그리퍼가 아래를 향해야 한다. 팔이 옆으로 누워서 블록 위치에 손목을 갖다대고 도착했다 라고 생각할 수 있다.

**우리는 임의의 방향 문제를 푸는것이 아니다. 그리퍼가 아래로 향하는 것과 손이 블록으로 정렬되는 것이다. 임의의 방향이 아니다**

4. ompl_planning.yaml
Open Motion Planning Library, RRT, RRT-Connect, PRM 같은 샘플링 기반 플래너들의 모음집이다.
관절 공간에 무작위 점을 뿌리고 충돌 없는 것들을 이어붙이는 것

CheckStartStateCollision : 시작 자세부터 충돌이면 계획하지 말아라
OMPL : 경로(공간상의 점)를 찾는다. 시간 개념이 없다.
AddTimeOptimalParameterization : 그 점들에 시각과 속도를 붙여 궤적으로 만든다. 이때 joint_limits.의 속도/가속도의 한계를 지킨다.

경로는 어디를 지나는가 궤적은 언제 거기 있는가 

5. joint_limits.yaml
default_velocity_scaling_factor: 0.1
default_acceleration_scaling_factor: 0.1

URDF에도 limit velocity가 있지만 그건 하드웨어 최대치이고 이 파일로 덮어쓰거나 축소한다. 
데모 영상에서 팔이 느리게 움직인다면 이 숫자 때문이다.

결론
move_group은 이 전부를 파라미터로 받아서 뜨는 하나의 노드이다. 스킬 서버가 말을 걸 상대가 된다.


6. MOCK 스킬 서버

1. ROS의 파라미터 = 노드가 소유한 설정 손잡이
토픽/서비스/액션은 노드들 사이의 통신이다. 데이터가 A에서 B로 흐르지
파라미터는 노드 자신의 설정이다. 흐르는 게 아니라 거기 그냥 있는 값이다. 노드의 메모리 안에 있고 노드가 필요할 때 읽는다.
노드는 별도의 프로세스 이다. 프로세스 안의 변수를 바깥에서 바꾸려면 문을 하나 뚫어야 한다.
ROS에서 프로세스 간 주고 받는 수단은 세가지이다. 토픽, 서비스, 액션, 파라미터 읽기/쓰기는 "요청/응답" 모양으로 서비스이다.
rclpy가 노드를 기본으로 상속한다. 노드를 만들때 파라미터 서비스를 자동으로 붙인다. 

## 3일차

오랜만에 작업. 다시 전체적인 흐름 정리.
계약 + 가짜 팔 
1. 액션 계약을 먼저 못 박고 가짜 스킬 서버로 에이전트를 검증하고 있음.
arm_interfaces에 팔의 행동이 정의 되어 있음.
현재 arm_agent는 /command 를 듣고 로그만 찍는다.
목 서버 내부에는 각기 다른 액션이 하나의 함수 _execute를 공유한다.
