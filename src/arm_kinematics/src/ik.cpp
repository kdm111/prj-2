#include "arm_kinematics/ik.hpp" // cpp가 hpp의 선언을 읽어 컴파일러가 대조하게 만든다ㅏ. 리턴 타입이나 인자를 틀리면 에러가 나온다.
#include <cmath> // 시스템 표준헤더 불러오기

namespace arm_kinematics
{ // hpp에서 상자에 담아 선언했으니 cpp에서도 같은 상자 안에서 정의해야 짝이 맞는다.
double reach_distance(double r, double z)
{
  return std::sqrt(r * r + z * z);   // std::pow(r,2)도 되지만 정수 제곱에는 곱셈이 빠르다. 하지만 카메라 좌표가 들어오면 어떻게 될지 스스로 분석할 것
}
} // namespace arm_kinematics
