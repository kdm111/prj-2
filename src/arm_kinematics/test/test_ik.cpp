// ik값의 검수
#include <gtest/gtest.h> // google의 테스트 프레임워크 불러오기
#include "arm_kinematics/ik.hpp"

TEST(ReachDistance, CASE_One) { // 매크로 첫째 묶음 이름, 둘째 케이스 이름
  // 부동소수점 연산은 EXPECT_EQ를 쓰면 안된다. 부동소수점은 틀릴 수도 있으니까
  EXPECT_NEAR(arm_kinematics::reach_distance(3.0, 4.0), 5.0, 1e-9);
}

TEST(ReachDistance, CASE_Zero) {
  EXPECT_NEAR(arm_kinematics::reach_distance(0.0, 0.0), 0.0, 1e-9);
}
