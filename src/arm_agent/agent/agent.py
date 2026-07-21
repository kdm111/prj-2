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
    def on_command(self, msg): 
        parts = msg.data.split()
        if not parts:
            return
        skill = parts[0]
        if skill == 'move_to' and len(parts) == 2:
            client =self._move_to_client
            goal = MoveTo.Goal()
            goal.target_name = parts[1]
        elif skill == 'pick' and len(parts) == 2:
            client = self._pick_client
            goal = Pick.Goal()
            goal.object_id = parts[1]
        elif skill == 'place' and len(parts) == 3:
            client = self._place_client
            goal = Place.Goal()
            goal.object_id = parts[1]
            goal.target_id = parts[2]
        else:
            self.get_logger().warn(f'등록 되지 않은 명령: {" ".join(parts)}')
            return
        goal.attempt = 1 # 어떤 행동이건 처음 시작하는 동작은 항상 1부터 시작
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
