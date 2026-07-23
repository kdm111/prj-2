#include "arm_kinematics/ik.hpp" // cpp가 hpp의 선언을 읽어 컴파일러가 대조하게 만든다ㅏ. 리턴 타입이나 인자를 틀리면 에러가 나온다.
#include <cmath> // 시스템 표준헤더 불러오기

namespace arm_kinematics
{ // hpp에서 상자에 담아 선언했으니 cpp에서도 같은 상자 안에서 정의해야 짝이 맞는다.
double get_reach_distance(double r, double z)
{
  return std::sqrt(r * r + z * z);   // std::pow(r,2)도 되지만 정수 제곱에는 곱셈이 빠르다. 하지만 카메라 좌표가 들어오면 어떻게 될지 스스로 분석할 것
}
double get_base_angle(double px, double py)
{
  return std::atan2(py, px);   // 각도 변환 생성
}
std::optional<double> get_elbow_angle(double d, double l1, double l2)
{
  double cos_theta = (l1 * l1 + l2 * l2 - d * d) / (2.0 * l1 * l2);
  if (std::fabs(cos_theta) > 1.0) {
    return std::nullopt;
  }
  return std::acos(cos_theta);
}
std::optional<double> get_shoulder_angle(double r, double z, double l1, double l2)
{
  double d = get_reach_distance(r, z);   // 어깨에서 목표까지의 직선 거리 D
  // 보정각 beta의 코사인, 삼각형(l1, d, l2)에서 어깨 꼬깆점의 각도이다.
  double cos_beta = (l1 * l1 + d * d - l2 * l2) / (2.0 * l1 * d);
  // 도달 가능성 검사. |cos|이 1을 넘으면 그런 삼각형은 존재하지 않는다.
  if (std::fabs(cos_beta) > 1.0) {
    return std::nullopt;
  }
  // 어깨에서 목표를 똑바로 겨누는 각. 수평 x축 기준 목표 방향
  double aim = std::atan2(z, r);
  // cos_beta로부터 실제 보정각. 팔꿈치가 접혀서 위팔이 더 들려야 하는 양
  double beta = std::acos(cos_beta);
  return aim + beta;
}
Point2D get_wrist_point(double r, double z, double l3, double phi)
{
  // 그리퍼는 손목에서 목표 방향으로 L3 만큼 뻗는다. target = wrist + L3 * (cos(phi), sin(phi))
  // 뒤집으면 손목 = 목표 - L3 * (cos(phi), sin(phi))
  double wrist_r = r - l3 * std::cos(phi);
  double wrist_z = z - l3 * std::sin(phi);
  return {wrist_r, wrist_z}; // Point2D 반환
}
} // namespace arm_kinematics
