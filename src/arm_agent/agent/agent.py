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
from arm_interfaces.action import MoveTo

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
    # 명령어가 들어오면 처리하고 핵션 서버로 보냄
    def on_command(self, msg): # 콜백 함수에는 메시지 객체가 전부 들어온다. 
        target = msg.data # 명령 전체를 자세 이름으로 취급
        self._move_to_client.wait_for_server() # 서버 뜰 때까지 대기
        goal = MoveTo.Goal()
        goal.target_name = target
        goal.attempt = 1 # 시도 횟수는 agent가 센다.
        goal_future = self._move_to_client.send_goal_async(goal) # goal을 쏜 후에 날라올 값
        goal_future.add_done_callback(self.on_goal_response) # 수락 여부 콜백

    # 수락 되면 결과값 처리
    def on_goal_response(self, goal_future):
        goal_handle = goal_future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('goal 거부됨')
            return
        self.get_logger().info('goal 수락됨')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.on_result) # 결과 콜백

    # 결과값 콜백
    def on_result(self, result_future):
        result = result_future.result().result
        self.get_logger().info(
            f'결과 : success={result.success}, code={result.failure.code}'
        )

def main(args=None):
    rclpy.init(args=args)
    agent = Agent()
    rclpy.spin(agent)

    rclpy.shutdown()
