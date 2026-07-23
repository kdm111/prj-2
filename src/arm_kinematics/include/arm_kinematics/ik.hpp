#pragma once // 이 헤더는 한번만 포함되고 여러 파일이 같은 헤더를 include 할 때 중복 삽입을 방지한다.
#include <optional>

// 함수를 arm_kinematics::reach_distance라는 이름표 상자에 넣는다. 즉 다른 라이브러리에 비슷한 이름의 함수가 있어도 부딪히지 않는다.
namespace arm_kinematics
{
double get_reach_distance(double r, double z);   // 함수 선언
double get_base_angle(double px, double py);   // 물체를 팔에 중심에 위치하도록 베이스 이동
std::optional<double> get_elbow_angle(double d, double l1, double l2);   // 팔꿈치 각도 계산
std::optional<double> get_shoulder_angle(double r, double z, double l1, double l2);   // 어깨 각도 계산
}
