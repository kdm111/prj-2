"""
mock_skills : 가짜 스킬 서버.

진짜 팔도 MoveIt도 없이 Pick/Place/MoveTo 액션 서버를 흉내낸다.
파라미터로 실패를 주입해서 에이전트의 복구 루프를 미리 검증한다.

"""

import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import ParameterDescriptor, ParameterType
from arm_interfaces.msg import ErrorCode, FailureReport, Stage

import time
from rclpy.action import ActionServer
from arm_interfaces.action import MoveTo

MOVE_TO_STAGES = [Stage.PLAN, Stage.EXECUTE]


class MockSkills(Node):
    def __init__(self):
        super().__init__('mock_skills')
        # 파라미터 선언. ROS2는 선언 안한 파라미터를 못 읽고 못 쓴다.
        # 기본적으로 파라미터의 타입은 선언 시점에 고정되고 바뀌지 않는다.
        # 명시된 기본값에서 추론되거나 디스크립터로 명시된 값. 
        # ROS2 파람 리스트에 기대한게 안 보이면 내가 지금 보고 있는 노드가 과거 노드인지 확인해야 한다.
        # symlink-install 덕에 빌드는 필요없지만 파이썬 파일은 읽힐때 재시작 하므로 다시 읽어야 한다.
        self.declare_parameter('move_to.duration_sec', 0.5)
        self.declare_parameter('move_to.fail_until_attempt', 0)
        self.declare_parameter(
            'move_to.fail_code',
            ErrorCode.PLANNING_FAILED
        )
        self.declare_parameter(
            'move_to.fail_stage',
            Stage.PLAN            
        )
        d = self.get_parameter('move_to.duration_sec').value
        self.get_logger().info(f'mock_skills 시작 move_to.duration_sec={d}')

        self._move_to_server = ActionServer( # _로 내부로 숨겨야 파이썬 GC이 수거하지 않는다.
            self, # 액션 서버가 붙을 노드
            MoveTo, # 액션 타입
            'move_to', # 액션 이름(상대 이름)
            self.execute_move_to, # 목표를 받으면 실행할 콜백
        )
    
    def execute_move_to(self, goal_handle):
        """
        action을 받으면 실행되는 callback 함수
        """
        goal = goal_handle.request # action goal은 request안에 있다.
        self.get_logger().info(
            f'move_to 시작 : target_name={goal.target_name} attempt={goal.attempt}'
        )
        duration = self.get_parameter('move_to.duration_sec').value
        fail_code = self.get_parameter('move_to.fail_code').value
        fail_stage = self.get_parameter('move_to.fail_stage').value
        fail_until = self.get_parameter('move_to.fail_until_attempt').value
        
        will_fail = goal.attempt <= fail_until
        for i, stage in enumerate(MOVE_TO_STAGES):
            feedback = MoveTo.Feedback()
            feedback.stage = stage
            feedback.progress = i / len(MOVE_TO_STAGES)
            goal_handle.publish_feedback(feedback)
            
            self.get_logger().info(f"[{stage}]")
            time.sleep(duration) # 행동마다 슬립 # param set 하면 그 값으로 바뀐 뒤 바로 먹혀야 한다.
            # 슬립 다음에 실패하는 이유
            # 앞에두면 시도 조차 하지 않기 때문. 
            if will_fail and stage == fail_stage: # 실패 사례
                self.get_logger().warn(f"[{stage}] 실패 주입 (code={fail_code})")
                goal_handle.abort()
                result = MoveTo.Result()
                result.success = False
                result.failure = self.make_failure(
                    code=fail_code,
                    stage=stage,
                    object_id='', # MoveTo는 물체가 없다.
                    detail=f"주입된 실패: target_name={goal.target_name}",
                    attempt=goal.attempt, # 서버는 세지 않고 에이전트가 셀 예정
                )
                return result
        goal_handle.succeed()
        result = MoveTo.Result()
        result.success = True
        result.failure = self.make_failure(ErrorCode.SUCCESS, '', '', '', goal.attempt)
        return result
    
    def make_failure(self, code, stage, object_id, detail, attempt):
        """
        FailureReport를 만드는 유일한 통로
        어디서도 FailureReport를 직접 생성하지 않고 code에 ErrorCode 상수가 아닌 값이 들어갈 경로를 여기 하나로 좁힌다.
        """
        report = FailureReport()
        report.code = code
        report.stage = stage
        report.object_id = object_id
        report.detail = detail
        report.stamp = self.get_clock().now().to_msg()
        report.attempt = attempt
        return report
    

def main(args=None):
    rclpy.init(args=args)
    mock_skills = MockSkills()
    rclpy.spin(mock_skills)

    rclpy.shutdown()

if __name__ == '__main__':
    main()