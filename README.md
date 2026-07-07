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


