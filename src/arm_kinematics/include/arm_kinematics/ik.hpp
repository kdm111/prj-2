#pragma once // 이 헤더는 한번만 포함되고 여러 파일이 같은 헤더를 include 할 때 중복 삽입을 방지한다.

// 함수를 arm_kinematics::reach_distance라는 이름표 상자에 넣는다. 즉 다른 라이브러리에 비슷한 이름의 함수가 있어도 부딪히지 않는다.
namespace arm_kinematics
{
double reach_distance(double r, double z);   // 함수 선언
}
