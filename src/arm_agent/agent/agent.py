'''
arm_agent : agent의 귀로 사용자의 명령을 받는 agent 노드

입력(구독) : /command (std_msgs/String)
출력 : 로그 출력
노드 이름 : arm_agent

'''

import rclpy
from rclpy.node import Node

from std_msgs.msg import String

from rclpy.action import ActionClient
from arm_interfaces.action import MoveTo, Pick, Place

from arm_interfaces.msg import ErrorCode

MAX_ATTEMPTS = 3
ABORT_CODES ={ErrorCode.UNREACHABLE, ErrorCode.INTERNAL_ERROR}

class Agent(Node): # Node 상속
    def __init__(self):
        super().__init__('agent') # 부모 생성자 호출 및 노드 이름 
        self.create_subscription( # command 를 구독하고 있어 명령을 수신할 수 있음.
            String,
            '/command',
            self.on_command,
            10
        )
        self._move_to_client = ActionClient(
            self,
            MoveTo, # 액션 타입
            'move_to' # 액션 명칭
        )
        self._pick_client = ActionClient(
            self,
            Pick,
            'pick'
        )
        self._place_client = ActionClient(
            self,
            Place,
            'place'
        )

    # 해당 액션 서버로 보내는 라우터
    # 계획을 세우고 실행 시작하는 함수
    def on_command(self, msg): 
        parts = msg.data.split()
        if not parts:
            self.get_logger().warn(f'잘못된 명령 : {" ".join(parts)}')
            return
        plan = self._build_plan(parts)
        if plan is None:
            self.get_logger().warn(f'잘못된 명령 : {" ".join(parts)}')
            return 
        self._plan = plan # 실행할 스텝들
        self._step = 0 # 지금 몇 번째
        self._attempt = 1 # 현재 시도 횟수
        self._run_step()

    # 계획을 만드는 함수
    def _build_plan(self, parts):
        skill = parts[0]
        if skill == 'move_to' and len(parts) == 2:
            client =self._move_to_client
            goal = MoveTo.Goal()
            goal.target_name = parts[1]
            return [(client, goal)]
        elif skill == 'pick' and len(parts) == 2:
            client = self._pick_client
            goal = Pick.Goal()
            goal.object_id = parts[1]
            return [(client, goal)]
        elif skill == 'place' and len(parts) == 3:
            client = self._place_client
            goal = Place.Goal()
            goal.object_id = parts[1]
            goal.target_id = parts[2]
            return [(client, goal)]
        elif skill == 'deliver' and len(parts) == 3:
            pick_goal = Pick.Goal()
            pick_goal.object_id = parts[1]
            place_goal = Place.Goal()
            place_goal.object_id = parts[1]
            place_goal.target_id = parts[2]
            return [(self._pick_client, pick_goal), (self._place_client, place_goal)]
        return None

    # 스텝 하나 실행
    def _run_step(self):
        if self._step >= len(self._plan):
            self.get_logger().info('시퀀스 완료')
            return
        client, goal = self._plan[self._step]
        goal.attempt = self._attempt
        client.wait_for_server()
        goal_future = client.send_goal_async(goal)
        goal_future.add_done_callback(self.on_goal_response)

    # 수락 되면 결과값 처리
    def on_goal_response(self, goal_future):
        goal_handle = goal_future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('goal 거부됨')
            return
        self.get_logger().info('goal 수락됨')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.on_result) # 결과 콜백

    # 결과값 콜백과 시퀀스 다음 스텝 실행
    # 에러 코드에 따른 복구 전략 변경
    def on_result(self, result_future):
        result = result_future.result().result
        code = result.failure.code
        if result.success:
            self._step += 1
            self._attempt = 1
            self.get_logger().info(
                f'결과 : success={result.success}, code={result.failure.code}'
            )
            self._run_step()
        if code in ABORT_CODES:
            self.get_logger().error(f'복구 불가 코드(code={code}) > 즉시 중단')
            return
        if self._attempt < MAX_ATTEMPTS:
            self._attempt += 1
            self.get_logger().warn(f'실패(code={result.failure.code}) > 재시도 attempt={self._attempt}')
            self._run_step()
        else:
            self.get_logger().error(f'복구 실패 > 시퀀스 중단(ABORT), code={result.failure.code}')
            return





def main(args=None):
    rclpy.init(args=args)
    agent = Agent()
    rclpy.spin(agent)

    rclpy.shutdown()
