#pragma once // 이 헤더는 한번만 포함되고 여러 파일이 같은 헤더를 include 할 때 중복 삽입을 방지한다.
#include <optional>

// 함수를 arm_kinematics::reach_distance라는 이름표 상자에 넣는다. 즉 다른 라이브러리에 비슷한 이름의 함수가 있어도 부딪히지 않는다.
namespace arm_kinematics
{
// 실제 omx-f의 링크 길이(m)
constexpr double L1 = 0.12052;   // 어깨 -> 팔꿈치 sqrt(0.0415^2 + 0.11315^2)
constexpr double L2 = 0.162;   // 팔꿈치 -> 손목
constexpr double L3 = 0.12063;   // 손목 -> TCP 0.0287 + 0.09193
struct Point2D
{
  double r;
  double z;
};
// IK의 해를 나타내는 구조체. 각 관절각과 해당 위치에 도달 가능한 지 확인한다.
struct IkSolution
{
  double theta1;
  double theta2;
  double theta3;
  double theta4;
  double theta5;
  bool reachable;
};
// IK의 해를 다 알고있음.
IkSolution solve_ik(double x, double y, double z, double phi);
// 손목점이 실제도 도달 해야 하는 점. 접근 방향에서 그리퍼 크기만큼 물러난 곳
Point2D get_wrist_point(double r, double z, double l3, double phi);
// 순기구학 : 관절각 + 링크 길이 > 손끝 위치(평면 r,z) IK 왕복 검증용
Point2D get_forward_kinematics(
  double theta2, double theta3, double theta4, double l1, double l2,
  double l3);
double get_reach_distance(double r, double z);   // 함수 선언
double get_base_angle(double px, double py);   // 물체를 팔에 중심에 위치하도록 베이스 이동
// 팔꿈치 각도 계산 bool 대수 포함으로 해당 팔꿈치가 위로 향하게 할지 아래로 향하게 할지 결정한다.
std::optional<double> get_elbow_angle(double d, double l1, double l2, bool elbow_up = true);
// 어깨 각도 계산
std::optional<double> get_shoulder_angle(
  double r, double z, double l1, double l2,
  bool elbow_up = true);
double get_wrist_angle(double phi, double theta2, double theta3);
}
