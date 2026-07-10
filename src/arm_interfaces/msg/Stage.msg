# C++와 Python 서로 양쪽이 같은 문자열을 쓴다는 보장이 없다. 오타가 컴파일/import Error를 나타내도록 간다.
# ROS2는 문자열 상수를 지원한다. FailureReport.stage와 Feedback.stage가 공유하는 어휘

# MoveTo : PLAN > EXECUTE
# Pick : PLAN > APPROACH > GRASP > LIFT
# Place : PLAN > TRANSFER > RELEASE > RETREAT

string PLAN=PLAN # 계획 수립 중 IK, PLANNING
string EXECUTE=EXECUTE # 궤적 실행 중 MoveTO 액션
string APPROACH=APPROACH # 물체 위 접근 자세로 이동 중
string GRASP=GRASP # 그리퍼 닫는 중
string LIFT=LIFT # 물체를 들어 올리는 중
string TRANSFER=TRANSFER # 물체를 들고 목적지로 이동 중
string RELEASE=RELEASE # 그리퍼 여는 중
string RETREAT=RETREAT # 물체에서 물러나는 중

