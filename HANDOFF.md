# 핸드오프 v3 — 자가 복구 피킹 셀

> AI 어시스턴트 간 컨텍스트 동기화용 문서. 대화가 바뀌거나 다른 도구로 넘어갈 때 이 파일을 먼저 읽힌다.
> 최종 갱신: 2026-07-10 (W1 목요일 밤)
> v2 대비 변경: 벤더 스택 실측 검증(§2), 개발 환경 규칙 신설(§3), mock 서버 진행(§6), 갭 조치 갱신(§8)

---

## 0. 협업 방식 (AI는 이 규칙을 따를 것)

- **가이드 모드.** 코드는 사용자가 직접 타이핑한다. AI는 설명하고 스펙을 넘긴다. 대신 써주지 않는다.
- **단계를 잘게 쪼갠다.** 한 번에 새 개념 하나. 한꺼번에 던지면 사용자가 조립하지 못한다. (실제로 액션서버+파라미터+실행기+디스크립터를 동시에 던졌다가 실패했다.)
- **경계가 있다 (§8-G1):** 인프라(launch, 컨트롤러 YAML, moveit config)는 벤더 것을 **재사용**한다. 직접 타이핑 대상은 **핵심 로직**(IK, 스킬 서버, 에이전트, 계약)뿐이다.
- 용어와 개념의 정확성을 중시한다. **틀린 표현은 지적받길 원한다.** AI가 틀렸으면 AI도 정정할 것.
- **추측하지 말고 확인할 것.** 이 프로젝트에서 AI가 세 번 틀렸다: (1) `ParameterDescriptor(type=...)`가 타입을 정한다고 함 → rclpy는 무시함, (2) 빈 리스트가 예외를 낸다고 함 → 조용히 `BYTE_ARRAY`가 됨, (3) `docker compose restart`로 노드가 재시작된다고 함 → PID 1만 재시작됨. **소스/실물을 열어보고 말할 것.**
- 매주 일요일 영상 1개. W6가 끝나면 미완성이어도 지원 시작. **협상 불가.**

---

## 1. 프로젝트 정체

**자가 복구 피킹 셀** — 단일 ROBOTIS OMX(OMX-F), sim → real.
포트폴리오 3계층 중 **"로봇 제어 계층"** 담당.

| 계층 | 산출물 | 상태 |
| --- | --- | --- |
| 관제 | BigPinky/VicPinky FMS (NestJS, React, domain_bridge) | 완료 (기존 자산) |
| **로봇 제어** | **이 프로젝트** | **W1 진행 중** |
| 임베디드 | STM32 UART 안전 워치독 | W7 예정 |

정체성 문장: *"관제부터 펌웨어까지, 로봇 시스템 전 계층을 실기로 관통한 엔지니어."*

### 설계 원칙

> LLM은 **무엇을** 할지 정하고, MoveIt2/OMPL은 **어떻게 갈지** 풀고, ros2_control은 **그대로 움직인다.**

| 계층 | 담당 | 하는 일 |
| --- | --- | --- |
| LLM 에이전트 | `arm_agent` | 자연어 → 스킬 시퀀스, 실패 → 복구 전략 판단 |
| 모션 플래닝 | MoveIt2 / OMPL | 충돌 없는 관절 궤적 생성 |
| 실시간 제어 | ros2_control | 궤적 추종, 하드웨어 read/write |

**LLM은 궤적을 만들지 않는다.** 경로 생성은 OMPL의 샘플링 기반 플래너(RRT 계열)이며 결정론적 알고리즘 + 난수 샘플링이다. 확률적 완전성만 보장 — 해가 있으면 언젠간 찾지만, 못 찾았다고 해가 없는 건 아니다.

**인지는 플래너에게 지도를 주고 빠진다.** 플래닝 중 카메라는 관여하지 않는다. Planning Scene = URDF(로봇) + 하드코딩(테이블) + `/scene_state` 스냅샷(동적 물체). 실행 중 물체가 움직이면 로봇은 모른다 — 그 실패가 `OBJECT_MOVED`이고 W5 자가 복구의 존재 이유.

---

## 2. 하드웨어 / 벤더 스택 — 실측 검증 완료 (2026-07-10)

### 2.1 제품 정체 — 혼동 금지

- 사용 장비는 **ROBOTIS OMX** (신형, Physical AI 라인). **구형 OpenMANIPULATOR-X(4축)와 다른 제품.**
- 레포 구조가 이를 증명: `open_manipulator_bringup/config/` 안에 `omx_f`와 `open_manipulator_x`가 **별도 디렉토리로 공존**.
- 검색·문서 작성 시 반드시 "OMX". "OpenMANIPULATOR-X" 자료(4-DOF IK 유도 등)를 가져오면 틀린다.

### 2.2 검증된 사실 (파일을 직접 열어 확인)

| 항목 | 확정 내용 | 출처 |
| --- | --- | --- |
| 자유도 | **5-DOF 팔 + 그리퍼** | ROBOTIS 공식 문서 |
| 라인업 | OMX-L(리더, 텔레옵) / OMX-F(팔로워) — **사용자는 둘 다 물리적으로 보유** | 공식 문서 |
| 제어 루프 | `update_rate: 100` Hz | `config/omx_f/hardware_controller_manager.yaml` |
| `arm_controller` | `joint_trajectory_controller/JointTrajectoryController`, joints `joint1~5`, command `position`, state `position+velocity`, `allow_partial_joints_goal: true` | 같음 |
| **그리퍼** | **`position_controllers/GripperActionController`**, joint `gripper_joint_1` | 같음 |
| SRDF 그룹 | `arm`(joint1~5 + end_effector_joint), `gripper`(gripper_joint_1, _2) | `config/omx_f/omx_f.srdf` |
| SRDF named pose | `init`, `home` (arm) / `open`, `close` (gripper). **`observe` 없음 → W4에 추가** | 같음 |
| 수동 관절 | `gripper_joint_2`는 `<passive_joint>` (손가락 하나만 구동) | 같음 |
| **IK 솔버** | `kdl_kinematics_plugin/KDLKinematicsPlugin`, timeout 5ms, **`position_only_ik: True`** | `config/omx_f/kinematics.yaml` |
| MoveIt 컨트롤러 | `arm_controller`=`FollowJointTrajectory`, `gripper_controller`=**`GripperCommand`** | `config/omx_f/moveit_controllers.yaml` |
| 플래너 | `ompl_interface/OMPLPlanner` + 어댑터 파이프라인 (`AddTimeOptimalParameterization` 등) | `config/ompl_planning.yaml` |
| 속도 | `default_velocity_scaling_factor: 0.1` (초보자용 축소) | `config/omx_f/joint_limits.yaml` |
| URDF | `${prefix}` xacro 파라미터가 **이미 적용돼 있음** → 양팔 확장 무료 | `urdf/omx_f/omx_f_arm.urdf.xacro` |
| 링크 오프셋 | j1 `(-0.01125,0,0.034)` / j2 `(0,0,0.0635)` / j3 `(0.0415,0,0.11315)` / j4 `(0.162,0,0)` / j5 `(0.0287,0,0)` | 같음 |

### 2.3 사용할 launch 두 개 (서로 독립)

| launch | 패키지 | 띄우는 것 | 인자 |
| --- | --- | --- | --- |
| `omx_f_gazebo.launch.py` | `open_manipulator_bringup` | Gazebo, robot_state_publisher, 컨트롤러 3종, clock 브리지 | `world` (기본 `empty_world`) |
| `omx_f_moveit.launch.py` | `open_manipulator_moveit_config` | move_group, RViz | **`use_sim` (기본 false → 반드시 `true`)**, `start_rviz` |

Gazebo launch는 move_group을 띄우지 않는다. **`sim`/`moveit` 컨테이너 분리가 벤더 설계와 일치.**

⚠️ `use_sim:=true`를 빼면 **Plan은 되는데 Execute가 조용히 무시된다.** 원인 찾기 고약함.

### 2.4 이 프로젝트에 대한 시사점

1. **`GRASP_FAILED` 판정이 공짜.** `GripperActionController`가 노출하는 `control_msgs/action/GripperCommand`의 Result에 `stalled`(물체에 막혀 멈춤 → 파지 성공)와 `reached_goal`(완전 닫힘 도달 → 파지 실패)가 들어 있다. `/joint_states`를 폴링하며 임계값을 튜닝할 필요 없음. `GRIPPER_EMPTY`는 lift 후 재확인으로 별도 판정.
2. **`position_only_ik: True`가 W2의 핵심 서사.** 벤더는 5축으로 6D 포즈를 못 맞추니 **방향 제약을 통째로 포기**했다. 피킹에 부적합(그리퍼가 아래를 안 봐도 "도달"). → W2에서 태스크 대칭성을 이용한 해석적 IK로 대체. *"5DOF의 자유도 부족을 태스크 대칭성으로 해소하고 남은 방정식을 해석적으로 풀었다."* KDL은 수치해석적(반복법)이므로 **성공률·시간 양쪽에서 이길 수 있다** — 그게 W2 벤치마크.
   - **W2 첫 작업: URDF의 `<axis>`를 확인할 것.** j1=z(베이스 요), j2~4=y(수직면 피치), j5=x(손목 롤)이면 위 서사가 성립. 확인 전엔 단정 금지.
3. **W2 "ros2_control 해부 문서"의 뼈대는 §2.2 표 + 아래 체인.**
4. **`omx_follower` 스택은 이 프로젝트가 아니다.** 리더-팔로워는 텔레옵/모방학습용이고 플래닝도 IK도 없다(사람 손이 그 역할). **같은 하드웨어, 다른 소프트웨어 스택.** 리더 팔은 W8 확장 카드(ACT 학습).

### 2.5 `Execute` 를 누르면 일어나는 일 (W2 문서의 뼈대)

```
[RViz]  마커 드래그 → 목표 6D 포즈
   ↓ /plan_kinematic_path
[move_group]
   ├ IK (kinematics.yaml 의 KDL)  : 목표 포즈 → 목표 관절값
   ├ OMPL                         : 현재 → 목표, 충돌 없는 경로 샘플링
   └ 시간 파라미터화              : 경로(점들) → 궤적(점+시각+속도)
   ↓ /arm_controller/follow_joint_trajectory  (moveit_controllers.yaml 이 알려준 주소)
[joint_trajectory_controller]  100Hz 보간
   ↓ command_interfaces: position
[gz_ros2_control]              ← 실기에선 여기가 DynamixelHardwareInterface
   ↓ write()
[Gazebo]  팔이 움직인다
   ↑ read() → joint_state_broadcaster → /joint_states → RViz, move_group
```

**sim과 real의 경계는 딱 한 칸(`gz_ros2_control` ↔ `DynamixelHardwareInterface`).** 그 위는 한 줄도 안 바뀐다. 이것이 이력서의 "sim-to-real 무수정 이식"의 실체이며, W6이 W1~W5를 다시 짜지 않아도 되는 이유.

---

## 3. 개발 환경 — 규칙 (하루를 태우고 얻은 것)

호스트: **Ubuntu 24.04.4 Noble**, `/opt/ros/jazzy` 네이티브 설치되어 있음(563 패키지), RTX 4070 SUPER, X11 세션.
그럼에도 **도커 컴포즈 3컨테이너 구조를 유지하기로 결정**(사용자 선택). 네이티브 개발도 가능했으나 포트폴리오·재현성을 택함.

### 3.1 절대 규칙

1. **빌드는 항상 `sim` 컨테이너에서.** `agent` 이미지엔 `ros2_control`/MoveIt이 없다. `install/`은 bind mount로 공유되므로 **어디서 지었는지가 중요**하다. (`agent`에서 `colcon build` → `controller_interface` 못 찾음 → 전체 abort.)
2. **`src/` 밑에 파일을 만드는 명령(`ros2 pkg create` 등)은 호스트에서.** 컨테이너 안에서 만들면 root 소유가 되어 VSCode가 sudo를 요구한다. (호스트에도 ROS가 있으므로 문제없음.) `build/`/`install/`/`log/`는 root 소유여도 무방 — 편집하지 않으므로.
3. **인자 없는 `colcon build` 금지.** `src/` 전부를 짓는다. `--packages-select`(그것만) 또는 `--packages-up-to`(의존성 포함).
4. **`--symlink-install`은 파이썬 패키지에만.** 같은 패키지를 symlink/복사 모드로 번갈아 지으면 `CMakeCache.txt`에 모드가 박혀서 `rm -rf build/<pkg> install/<pkg>` 해야 풀린다.
5. **컨테이너는 root로 실행.** `user: "1000:1000"`을 시도했다가 `HOME=/root`(700) 접근 불가 + `.bashrc` 경로 문제로 되돌림.
6. **`docker compose restart <svc>`는 PID 1(`sleep infinity`)만 재시작한다.** `exec`으로 띄운 노드는 죽고 안 돌아온다. 노드를 다시 띄우려면 셸에서 `Ctrl+C` 후 재실행.

### 3.2 벤더 패키지 제외

`src/third_party/open_manipulator/` 아래 6곳에 `COLCON_IGNORE` 파일을 둠:
`open_manipulator/`, `open_manipulator_collision/`, `open_manipulator_gui/`, `open_manipulator_playground/`, `open_manipulator_teleop/`, `ros2_controller/`(om_* 3개 통째로).
**`vcs import`를 다시 하면 사라지므로 재생성 필요.** W8에 텔레옵이 필요하면 해당 파일만 삭제.

### 3.3 브링업

```bash
xhost +local:docker            # 최초 1회 (재부팅하면 다시)
docker compose up -d

# 최초 1회 빌드
vcs import src < singlearm.repos          # 호스트. src 기준(!). src/third_party 아님
docker compose exec sim bash
colcon build --packages-up-to open_manipulator_bringup open_manipulator_moveit_config
colcon build --packages-select arm_interfaces
colcon build --packages-select arm_agent arm_skills_mock --symlink-install

# [터미널 A]
docker compose exec sim bash
ros2 launch open_manipulator_bringup omx_f_gazebo.launch.py

# [터미널 B]
docker compose exec moveit bash
ros2 launch open_manipulator_moveit_config omx_f_moveit.launch.py use_sim:=true
```

`.bashrc`가 ROS와 `/ws/install/setup.bash`를 자동 소싱한다 (대화형 셸 한정. `bash -c "..."`는 안 됨).

### 3.4 컨테이너 구조

| 서비스 | 이미지 | 하는 일 | GUI |
| --- | --- | --- | --- |
| `sim` | `singlearm/sim:dev` | Gazebo Harmonic + ros2_control + rsp. **빌드도 여기서** | X11 |
| `moveit` | `singlearm/sim:dev` (공유) | move_group + RViz | X11 |
| `agent` | `singlearm/agent:dev` | LLM 계획·복구 (ros-base만) | — |
| (W3) `skills` | 미정 | C++ 액션 서버 3종 | — |
| (W4) `perception` | 미정 | ArUco → `/scene_state` | `/dev/video0` |

- **이미지는 "필요한 소프트웨어"로 나누고, 컨테이너는 "생명주기"로 나눈다.** `sim`/`moveit`이 이미지를 공유하는 이유(같은 의존성)와 컨테이너를 나누는 이유(move_group만 자주 재시작; Gazebo 씬 보존)가 다르다.
- `moveit`에도 `build:` 블록이 **필요하다.** `image:`만 있으면 compose가 Docker Hub에서 pull하려다 실패한다. 같은 Dockerfile이라 두 번째는 캐시로 0초.
- **`${DISPLAY}` 오타 주의.** compose는 없는 변수를 에러 없이 빈 문자열로 치환한다. `docker compose config`로 렌더링 결과를 확인하는 습관.
- **DDS 검증 완료 (2026-07-10):** 도커 브리지 네트워크에서 멀티캐스트 디스커버리가 동작한다. `moveit` 컨테이너에서 `sim`의 `/joint_states`가 보이고 `Plan & Execute`가 Gazebo의 팔을 움직였다. **v2에 적힌 Zenoh 폴백은 불필요.** (rmw_zenoh는 ROBOTIS Dockerfile에도 있으니 최후의 수단으로만 기억.)

### 3.5 의존성 해결 경로가 두 갈래

| 무엇 | 도구 |
| --- | --- |
| apt에 바이너리가 있는 것 (`moveit`, `ros_gz`, `dynamixel_sdk`) | `apt` / `rosdep` |
| 소스로만 배포되는 것 (`open_manipulator`, `dynamixel_interfaces`) | `vcs import` + `.repos` |

`rosdep`은 소스 레포를 클론하지 않는다. `colcon`은 이미 있는 걸 순서대로 짓기만 한다.
**`.repos`는 중첩된다.** `dynamixel_hardware_interface`가 자기 `.repos`로 `dynamixel_interfaces`를 요구했다. 새 서드파티를 붙일 땐 그 레포 안의 `*_ci.repos`를 먼저 볼 것.

`singlearm.repos`: `open_manipulator`(jazzy), `dynamixel_hardware_interface`(main), `dynamixel_interfaces`(main), `robotis_interfaces`(main). 클론 위치 `src/third_party/`는 gitignore.

---

## 4. 계약 (`arm_interfaces`) — 닫힘

### 4.1 액션 3종

Result는 셋 다 동일. **실패 정보의 출처는 하나뿐**이라는 규칙:

```
bool success
FailureReport failure     # success=true면 failure.code == SUCCESS
```

`bool success`는 중복이지만 클라이언트 가독성(`if result.success:`)을 위해 유지.

| 액션 | Goal | 목표가 사는 공간 | IK |
| --- | --- | --- | --- |
| `Pick` | `string object_id`, `uint8 attempt` | 작업 공간 (`/scene_state` 조회) | 푼다 |
| `Place` | `string target_id`, `uint8 attempt` | 작업 공간 | 푼다 |
| `MoveTo` | `string target_name`, `uint8 attempt` | 관절 공간 (SRDF `group_state`) | 안 푼다 |

Feedback 공통: `string stage` + `float32 progress`.

**`attempt`는 에이전트가 센다. 서버는 무상태.** 실패 시 `report.attempt = goal.attempt`를 그대로 되돌린다. 1부터 시작. 서버가 세면 RESCAN 후 리셋 여부를 서버가 알 수 없다.

**`MoveTo`가 별도 액션인 이유:** 목표 표현 방식이 다르다 — 관절값 직접 / 이름 붙인 관절값(SRDF) / 손끝 6D 포즈(IK 필요). `MoveTo`는 2번, `Pick`/`Place`는 3번. 셋 다 목표 확정 후엔 플래너가 경로를 **매 호출마다 새로** 계산한다. **"사전 정의된"이 수식하는 건 궤적이 아니라 목표다.** 용처: 관측 자세로 팔 치우기(팔이 블록을 가리면 ArUco를 못 봄), 사이클 후 home 복귀, RESCAN 복구.

**명명 규칙:** `_id` = 세상에 실재하는 물체/장소(`red_block`, `tray`) / `_name` = SRDF 자세 이름표(`home`, `observe`). LLM tool 스키마 혼동 방지.
**`MoveToPose`는 의도적으로 회피** — 로봇 도메인에서 "pose"는 Cartesian 6D. 미래의 진짜 Cartesian 액션에 이름을 남겨둔다.

**액션 서버 이름:** `pick`, `place`, `move_to` (상대 이름. `/` 없음 → 네임스페이스로 `/left_arm/pick` 확장 가능).

### 4.2 `FailureReport.msg` — 복구 판단의 유일한 입력

```
int32 code                      # ErrorCode 상수값
string stage                    # Stage 상수값
string object_id                # 대상 없으면 빈 문자열
string detail                   # 사람이 읽는 메시지
builtin_interfaces/Time stamp   # 노드 시계(get_clock). time.time() 금지 — use_sim_time 때문
uint8 attempt
```

RETRY/REGRASP/RESCAN을 가르는 건 `code`가 아니라 `stage`+`attempt`.

**알려진 구멍:** `code`(int32)와 `ErrorCode`의 연결은 주석뿐 — 타입 시스템이 강제 못 함. 방어책: **`make_failure()` 헬퍼가 `FailureReport`를 만드는 유일한 통로.** mock 서버에 이미 구현됨. W3 C++ 서버도 같은 이름의 함수를 가질 것.

### 4.3 `ErrorCode.msg` / `Stage.msg` — 발행되지 않는 상수 이름공간

필드 0개 + 상수만. ROS 2 IDL에 enum이 없어서 쓰는 표준 관례(`action_msgs/GoalStatus`, `moveit_msgs/MoveItErrorCodes`, **`rcl_interfaces/ParameterType`** 도 같은 패턴). C++/Python 양쪽 상수가 빌드 시 한 파일에서 생성 → 같은 값을 다른 이름으로 부르는 사고를 구조적으로 차단.

| ErrorCode | 값 | 의미 | 복구 전략(초안) |
| --- | --- | --- | --- |
| `SUCCESS` | 0 | 성공 | — |
| `OBJECT_NOT_FOUND` | 1 | 물체를 찾을 수 없음 | RESCAN |
| `UNREACHABLE` | 2 | IK 해 없음 | **ABORT** |
| `PLANNING_FAILED` | 3 | 경로 생성 실패 | REPLAN (OMPL은 확률형) |
| `GRASP_FAILED` | 4 | 애초에 못 잡음 (그리퍼 완전 닫힘) | REGRASP |
| `OBJECT_MOVED` | 5 | 인지 시점 포즈에 물건 없음 | RESCAN |
| `GRIPPER_EMPTY` | 6 | 잡았다가 운반 중 낙하 | REGRASP |
| `EXECUTION_TIMEOUT` | 7 | 실행 시간 초과 | RETRY |
| `INTERNAL_ERROR` | 99 | 알 수 없는 에러 | **ABORT** |

⚠️ **복구 전략 열은 아직 초안이다.** 사용자가 확정한 건 `OBJECT_MOVED→RESCAN`, `GRIPPER_EMPTY→REGRASP` 둘뿐. W5에서 설계할 때 진실로 취급하지 말 것.

`SUCCESS=0`은 의도된 설계 — `FailureReport`의 `int32` 기본값이 0이므로 성공 경로에서 아무것도 안 채워도 `failure.code == SUCCESS`가 성립한다.

**Stage:** `PLAN`, `EXECUTE`, `APPROACH`, `GRASP`, `LIFT`, `TRANSFER`, `RELEASE`, `RETREAT`

```
MoveTo : PLAN → EXECUTE
Pick   : PLAN → APPROACH → GRASP → LIFT
Place  : PLAN → TRANSFER → RELEASE → RETREAT
```

**재번호 금지.** 상수값이 곧 계약. 실기 로그가 쌓이면 과거 로그의 숫자 의미가 바뀐다. 새 코드는 뒤에 추가만.

---

## 5. 현재 레포 상태

```
personal_project/
├── compose.yaml               # 프로젝트명 singlearm. 서비스 agent/sim/moveit
├── singlearm.repos            # 벤더 4개 버전 고정
├── docker/{agent,sim}.Dockerfile
├── HANDOFF.md                 # 이 파일
├── w1_sim_bringup_{1,2}.webm  # W1 데모 영상 (docs/media/ 로 옮길 것)
└── src/
    ├── arm_interfaces/        # ament_cmake — 계약 (닫힘)
    │   ├── action/{Pick,Place,MoveTo}.action
    │   └── msg/{FailureReport,ErrorCode,Stage}.msg
    ├── arm_agent/             # ament_python — /command 구독 스텁 (아직 미개발)
    ├── arm_skills_mock/       # ament_python — mock 스킬 서버 (진행 중)
    └── third_party/           # gitignore. vcs import 로 재현
```

커밋 히스토리 (최신순): `mock 서버: move_to 액션 서버 + 실패 주입` / `Stage 메시지 추가` / `컨테이너별 moveit, sim 생성 후 동작 확인` / `action 시도 횟수 추가` / `single arm으로 docker container 변경` / `FailureReport 추가` / `agent 노드 생성` / `로봇 작업 인터페이스 선언`

---

## 6. mock 스킬 서버 — 진행 중 (여기서 이어갈 것)

**전략:** 계약을 먼저 못 박고, mock으로 에이전트를 미리 완성한다.
Python 노드 하나가 `Pick`/`Place`/`MoveTo` 액션 서버 3개를 띄우되, 진짜 팔도 MoveIt도 없이 `sleep` 후 결과만 뱉는다. 파라미터로 실패를 주입한다.

**이유:** ① 에이전트의 복구 루프를 W1에 검증 가능 ② W3에서 진짜 C++ 서버로 갈아끼울 때 **에이전트 코드 무수정** ③ 복구 전략을 **결정론적으로** 검증(실제 파지 실패는 비결정적이라 디버깅이 지옥).

### 6.1 현재 상태

- ✅ `_execute(goal_handle, name, action_type, object_id, target)` — 액션 3종 공통 로직. 내부에 `MoveTo` 등 특정 액션 이름이 없다.
- ✅ `make_failure(code, stage, object_id, detail, attempt)` — `FailureReport`의 유일한 생성 통로. `stamp`는 `self.get_clock().now().to_msg()`.
- ✅ 파라미터 12개 선언 (`{pick,place,move_to}.{duration_sec,fail_until_attempt,fail_code,fail_stage}`)
- ✅ `move_to` 액션 서버 동작. 실패 주입 검증 완료:
  ```
  attempt=1                         → SUCCEEDED
  param set move_to.fail_until_attempt 1
  attempt=1  [PLAN] 실패 주입 code=3 → ABORTED, failure.attempt=1
  attempt=2  [PLAN][EXECUTE]        → SUCCEEDED
  ```
- ⬜ `pick` / `place` 액션 서버 (껍데기 + `ActionServer` 한 줄씩)

### 6.2 남은 작업

```python
# 1) pick 추가
self._pick_server = ActionServer(self, Pick, 'pick', self.execute_pick)

def execute_pick(self, goal_handle):
    goal = goal_handle.request
    return self._execute(goal_handle, 'pick', Pick, goal.object_id, goal.object_id)

# 2) place 추가 (object_id는 빈 문자열, target은 goal.target_id)
```

`object_id`와 `target`을 나눈 이유: `object_id`는 `FailureReport`의 필드로 **의미가 정해져 있다**(실패의 대상이 된 물체). `move_to`의 `home`, `place`의 `tray`는 물체가 아니라 자세·장소이므로 넣으면 안 된다. `target`은 순전히 로그/`detail`용.

### 6.3 mock 설계 결정

- **실패 시 `goal_handle.abort()`** (액션 상태 `ABORTED`) + Result에 `FailureReport`. `succeed()` + `success=false`가 아니다. ROS 관례이고 `ros2 action send_goal`로 상태가 바로 보인다. rclpy는 `abort()` 후에도 Result를 정상 전달한다.
- **`fail_until_attempt: int` (0 = 실패 없음)**, 배열이 아니다. rclpy는 빈 리스트의 타입을 추론하지 못하고(`all()`의 공허참 때문에 `BYTE_ARRAY`가 됨) `ParameterDescriptor(type=...)`는 **무시된다**(docstring 명시). 정수 하나면 "처음 N번 실패 후 성공"이라는 실제 시나리오를 다 표현한다.
- **파라미터는 콜백 안에서 매번 읽는다.** `__init__`에서 읽어 저장하면 `ros2 param set`이 안 먹는다. W5에서 실행 중인 시스템에 실패를 주입하려면 필수.
- **실행기는 아직 기본 `rclpy.spin(node)`.** `time.sleep`이 막지만 목표를 하나씩 보내면 문제없다. **액션 3개 + 취소 처리를 넣을 때 `MultiThreadedExecutor` + `ReentrantCallbackGroup`으로 전환.** W3의 C++ 서버도 MoveIt 호출이 블로킹이라 같은 구조가 필요.
- **콜백에서 예외가 나면 rclpy가 자동으로 `ABORTED` 처리**하되 Result는 기본값(`success=false`, `code=0`)이라 계약상 모순(`success=false`인데 `code==SUCCESS`). W3 서버는 `try/except`로 감싸 `INTERNAL_ERROR(99)`를 채울 것.

### 6.4 미결 결정 — 다음 세션 첫 안건

**`Place.action` goal에 `string object_id`를 추가할 것인가?**

운반 중 낙하(`GRIPPER_EMPTY`)가 나면 `FailureReport.object_id`가 빈 문자열이라 **무엇을 떨어뜨렸는지 로그에 안 남는다.** `FailureReport`가 "에이전트의 행동 역추적을 위한 메시지"라는 커밋 메시지를 생각하면 손실이다.

```
# Place goal (제안)
string object_id     # 지금 들고 있는 물체
string target_id     # 놓을 곳
uint8  attempt
```

에이전트는 어차피 아는 값이고, W3 서버는 놓은 뒤 `/scene_state`를 갱신할 때 결국 필요해진다. **지금이 싸다** (계약 + mock만 수정). W3엔 에이전트와 C++ 서버까지 세 군데.

---

## 7. 시장 평가 — 공고 코퍼스(약 25건) 대비

> 코퍼스: 로보에·고레·두산·HD현대·현대차(제어/연구), 클로봇·로보티즈·와트·XYZ·코라스(응용/시스템), 셀틱스·알티올·에이로봇·니어스랩(펌웨어), AIVEX·씨메스·라이온(비전), 위로보틱스·Riibotics 등.

### 7.1 잘하고 있는 것

1. **계약-우선 + mock 전략.** 액션 계약을 먼저 닫고 mock으로 에이전트를 검증하는 순서는 와트류의 "SW 구조 설계 + unit test·시나리오 기반 통합 테스트" 문화 그 자체.
2. **실패 분류의 정교함.** `GRASP_FAILED`≠`GRIPPER_EMPTY`, stage+attempt 기반 판단은 클로봇의 "Failover 구조 설계 및 개발"을 정면 커버. **자소서·면접에서 "failover"라는 단어로 서술할 것.**
3. **계층 분리의 언어화.** "LLM은 궤적을 만들지 않는다", OMPL 확률적 완전성 같은 정확한 표현은 로보에의 "샘플링 기반 모션플래닝"을 '도구 사용'이 아니라 '원리 이해'로 증명. 부트캠프 출신 변별 포인트.
4. **`position_only_ik` 발견 → W2 서사 확보.** "MoveIt 써봤습니다"와 "MoveIt 설정을 읽고 한계를 파악했습니다"를 가르는 문장.
5. **하드웨어-스택 구분 인식.** 리더-팔로워(텔레옵/IL)와 자율 플래닝을 분리 — 목표가 흐려지지 않음.
6. **과분석 방지 장치 내장.** 주간 영상, W6 지원 시작, "실체 없는 컨테이너 금지", DDS "미리 손대지 말 것".

### 7.2 공고 커버리지 매핑

| 공고 요구 (빈도순) | 이 프로젝트에서의 증거 |
| --- | --- |
| 실기 매니퓰레이터 경험 | W6 OMX-F 브링업 + 실기 자가 복구 데모 |
| 기구학 | W2 해석적 5-DOF IK (태스크 대칭성) |
| 모션플래닝 (샘플링 기반) | MoveIt2/OMPL + 원리 언어화 |
| ROS2 액션/토픽/서비스 설계 | `arm_interfaces` 계약 |
| C++ | W2 IK, W3 스킬 서버 |
| failover/복구 구조 | ErrorCode 체계 + W5 복구 루프 |
| Docker/Linux/Git | compose 멀티컨테이너 + CI |
| LLM→행동 (두산·HD현대) | `arm_agent` tool-use |
| 임베디드 이해 (우대) | W7 STM32 워치독 |

---

## 8. 갭 조치 목록

- **G1 — 인프라 재사용 원칙 ✅ 성공.** 벤더 launch/config를 **한 줄도 고치지 않고** Gazebo+MoveIt을 컴포즈 안에서 구동. 직접 작성한 것은 Dockerfile, compose 정의, `.repos`뿐.
- **G2 — `SceneState.msg` 초안 (W2 초까지).** 최소형: `DetectedObject[] objects`, `DetectedObject = {string object_id, geometry_msgs/PoseStamped pose, builtin_interfaces/Time last_seen}`. perception(생산자, W4)과 skills(소비자, W3)가 공유하므로 **W3 전에 닫는다.** 스냅샷 의미론을 주석으로 명기.
- **G3 — ABORT 전략 추가 (W2).** 복구 전략 집합을 {RETRY, REGRASP, RESCAN, REPLAN, **ABORT**}로 확정. ABORT = 사이클 중단 + 사용자 보고. `UNREACHABLE`·`INTERNAL_ERROR`·attempt 상한 초과의 종착지. W5 상태 표시에 `ABORTED` 추가.
- **G4 — Place 검증 결정 (W4).** A: release 후 그리퍼 위치로만 판정(약함) / B: `MoveTo(observe)` → perception 재확인(강함, RESCAN 인프라 재사용). **B 권장.** §6.4의 `Place.object_id` 결정과 연동.
- **G5 — CI (아직 안 함, 30분).** GitHub Actions: `ros:jazzy` 컨테이너에서 `colcon build` + `colcon test`. **도커가 개발의 주 무대가 아니게 되더라도 CI가 Dockerfile을 검증한다.**
- **G6 — C++ 파이프라인 선행 (W2에 내장).** W2 IK를 C++ 라이브러리 + gtest로 만들며 C++ 빌드/테스트 경로를 먼저 뚫는다. W3는 "C++ 처음"이 아니라 "액션 서버 패턴만 새로".
- **G7 — 그리퍼 제어 경로 ✅ 종료.** `omx_f` 프로파일은 `GripperActionController`. (`gpio_command_controller`는 어느 프로파일에도 없음. `omx_f_follower_ai`는 `arm_controller`가 `gripper_joint_1`까지 6조인트로 먹는 별개 구성.)
- **G8 — SRDF 오버레이 (W3~W4, 신규).** W4에 `observe` 자세를 추가해야 하는데 벤더 SRDF는 `src/third_party/`(gitignore)에 있다. 고쳐도 커밋에 안 남고 `vcs import`로 날아간다. → **`src/singlearm_moveit_config` 패키지를 만들어 벤더 config를 오버레이한다.** 지금 손대지 말 것.
- **G9 — `install/` 공유 위험 (W3, 신규).** 세 컨테이너가 bind mount로 `install/`을 공유하는데 이미지가 서로 다르다. `skills` 컨테이너(C++/MoveIt)가 생기면 "빌드는 한 컨테이너에서만" 규칙을 강제하거나 컨테이너별 install을 분리할 것.
- **G10 — 시연용 compose 오버레이 (W5~W6, 신규).** 현재 PID 1은 `sleep infinity`. `docker compose up` 한 방으로 전체가 뜨게 하려면 각 서비스에 `command:`를 주는 `compose.demo.yaml`을 만들어 `-f`로 겹친다. 개발 편의를 위해 지금은 하지 않는다.

---

## 9. 로드맵

| 주차 | 기간 | 목표 | 산출물 |
| --- | --- | --- | --- |
| **W1** | 7/7–7/13 | 계약 ✅ / sim+moveit 구동 ✅ / mock 스킬 서버(진행 중) / G5 CI | 인터페이스 커밋 ✅ + sim 구동 영상(재촬영 필요) |
| W2 | 7/14–7/20 | ros2_control 해부 문서(§2.5 기반). **해석적 5-DOF IK** 유도 + C++ 구현 + gtest FK 왕복 검증(KDL 대비 성공률·시간). G2 SceneState, G3 ABORT. 루프 주기/지터 측정 | IK 유도 문서 + 벤치마크 표 |
| W3 | 7/21–7/27 | C++ 스킬 서버 3종(MoveGroupInterface). `make_failure` 헬퍼. 텍스트 명령 → sim pick E2E ★수직 슬라이스 | E2E 영상 |
| W4 | 7/28–8/3 | 웹캠 + ArUco → 6D 포즈 → `/scene_state`. agent 실스킬 연결. G4, G8 | "빨간 블록 트레이에" 데모 |
| W5 | 8/4–8/10 | 실패 주입 3종 + 복구 전략 5종(ABORT 포함). 사이클 루프 + RUNNING/RECOVERING/ABORTED | 자가 복구 데모 영상 |
| W6 | 8/11–8/17 | **실기.** OMX-F 브링업, 카메라 삼각대 + 베이스 캘리브레이션 | **지원 가능한 완결 포트폴리오 → 지원 시작** |
| W7 | 8/18–8/24 | STM32 워치독: UART 하트비트 500ms 단절 시 릴레이 전원 차단 | 독립 repo + 1페이지 |
| W8+ | 8/25~ | 선택 카드: 양팔(`${prefix}` 이미 있음) / 포인트클라우드 / ACT(리더 팔) | — |

### W6 전 확인 목록 (미확인)

- [ ] 모터 정확한 모델명 (X-series까지만 확인)
- [ ] OMX-F 전원 스펙 (전압/전류) — **W7 워치독 릴레이 설계에 직결**
- [ ] PC↔팔 인터페이스 보드 (U2D2 여부, `/dev` 경로)
- [ ] URDF의 `<axis>` 확인 (W2 IK 서사의 전제)

---

## 10. 이력서용 기술 스택

- **로봇 제어** — ROS2 Jazzy, ros2_control(`hardware_interface`·`controller_manager`·JTC, 100Hz), MoveIt2(OMPL 샘플링 기반 플래닝), **해석적 역기구학(5-DOF, 태스크 대칭성 활용) 유도·구현**, Gazebo Harmonic, DYNAMIXEL Protocol 2.0/TTL, sim-to-real 무수정 이식
- **시스템 설계** — Docker Compose 멀티컨테이너, ROS2 액션 기반 인터페이스 계약, 에러코드 체계·failover(자가 복구) 아키텍처, C++17/Python, GitHub Actions CI
- **AI 통합** — LLM tool-use 에이전트(작업 계획·복구 판단), OpenCV/ArUco 6D 포즈 인지
- **임베디드** — STM32 레지스터 레벨(GPIO·TIM·UART·NVIC·BSRR), UART 안전 워치독, RTOS 개념
- **기보유(관제)** — NestJS, React, Socket.IO/WebRTC, `domain_bridge` 기반 멀티로봇 FMS

---

## 11. 다른 AI를 위한 첫 행동 지침

1. **§0 협업 방식을 지킨다.** 코드를 대신 쓰지 말 것. 단계를 잘게 쪼갤 것. **확인하지 않은 API 동작을 단정하지 말 것.**
2. 지금이 W1 금~일이면: **§6.4 `Place.object_id` 결정 → `pick`/`place` 액션 서버 추가 → G5 CI → 영상 재촬영** 순.
3. **"OMX"와 "OpenMANIPULATOR-X"를 절대 혼용하지 말 것 (§2.1).**
4. **계약(§4)의 상수값·필드는 사용자 확인 없이 변경 제안하지 말 것.** 추가는 뒤 번호로만.
5. **개발 환경 규칙(§3.1)을 어기지 말 것.** 특히 "빌드는 `sim` 컨테이너", "`src/` 파일 생성은 호스트".
6. 일정 압박 시 우선순위: 수직 슬라이스(W3 E2E) > 우대 카드. **W6 지원 시작 규칙은 협상 불가.**
