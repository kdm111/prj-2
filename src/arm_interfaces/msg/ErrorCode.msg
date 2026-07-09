int32 SUCCESS=0 # 성공
int32 OBJECT_NOT_FOUND=1 # 물체를 찾을 수 없음
# 역기구학. 포즈를 만드려면 각도를 몇 도로 둬야 하는가? 
# 팔이 만들수 없는 자세라면 각도 제한에 걸리거나
int32 UNREACHABLE=2 # 닿을 수 없는 거리에 있음
# 모션 플래닝
# IK가 목표 관절값을 내놨으니 아무데도 부딪히지 않고 가는 궤적을 찾는다.
# 목표 자체는 도달 가능 가는 길이 막혀있으면 failed 처리 된다.
# 이는 확률형 이라서 시드를 바꾸거나 플래닝 시간을 늘리면 종종 해결된다.
int32 PLANNING_FAILED=3 # 경로 생성을 할 수 없음
 # 그리퍼 닫힘 위치로 판정한 파지 실패 
int32 GRASP_FAILED=4 # 짚을 수 없음.
 # 실행 시간 초과
int32 EXECUTION_TIMEOUT=5
int32 INTERNAL_ERROR=99 # 알 수 없는 에러

