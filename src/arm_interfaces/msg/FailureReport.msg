# 실패 1건에 대한 구조화된 보고서
# 에이전트의 복구 전략을 고르는 유일한 입력
# 에러 코드 하나만으로는 에이전트가 복구 할 수 없다. 어떤 환경에서 

int32 code # arm_interfaces/msg/ErrorCode의 상수값
string stage # 실패 시점 PLAN | APPROACH | GRASP | LIFT | TRANSFER | RELEASE | RETREAT
string object_id # 대상 없으면 빈 문자열
string detail # 읽는 메시지
builtin_interfaces/Time stamp # 실패 시각
uint8 attempt # 목표에 대한 몇 번째 시도인가?

