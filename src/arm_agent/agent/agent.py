'''
arm_agent : agent의 귀로 사용자의 명령을 받는 agent 노드

입력(구독) : /command (std_msgs/String)
출력 : 로그 출력
노드 이름 : arm_agent

'''

import rclpy
from rclpy.node import Node

from std_msgs.msg import String


class Agent(Node): # Node 상속
    def __init__(self):
        super().__init__('agent') # 부모 생성자 호출 및 노드 이름 
        self.create_subscription( # command 를 구독하고 있어 명령을 수신할 수 있음.
            String,
            '/command',
            self.on_command,
            10
        )

    def on_command(self, msg): # 콜백 함수에는 메시지 객체가 전부 들어온다. 
        self.get_logger().info(msg.data)

def main(args=None):
    rclpy.init(args=args)
    agent = Agent()
    rclpy.spin(agent)

    rclpy.shutdown()
