// ik값의 검수
#include <gtest/gtest.h> // google의 테스트 프레임워크 불러오기
#include <cmath>
#include "arm_kinematics/ik.hpp"

TEST(ReachDistance, CASE_One) { // 매크로 첫째 묶음 이름, 둘째 케이스 이름
  // 부동소수점 연산은 EXPECT_EQ를 쓰면 안된다. 부동소수점은 틀릴 수도 있으니까
  EXPECT_NEAR(arm_kinematics::get_reach_distance(3.0, 4.0), 5.0, 1e-9);
}

TEST(ReachDistance, CASE_Zero) {
  EXPECT_NEAR(arm_kinematics::get_reach_distance(0.0, 0.0), 0.0, 1e-9);
}

TEST(BaseAngle, PositiveX)
{
  EXPECT_NEAR(arm_kinematics::get_base_angle(1.0, 0.0), 0.0, 1e-9);
}

TEST(BaseAngle, PositiveY)
{
  EXPECT_NEAR(arm_kinematics::get_base_angle(0.0, 1.0), M_PI / 2, 1e-9);
}

TEST(BaseAngle, SecondQuadrant)
{
  // (-1.0, 1.0) > 135(deg) atan(py/px) 였으면 -45도로 틀렸을 자리
  EXPECT_NEAR(arm_kinematics::get_base_angle(-1.0, 1.0), 3 * M_PI / 4, 1e-9);
}
TEST(ElbowAngle, RightAngle)
{
  auto result = arm_kinematics::get_elbow_angle(std::sqrt(2.0), 1.0, 1.0);
  ASSERT_TRUE(result.has_value());
  EXPECT_NEAR(result.value(), M_PI / 2, 1e-9);
}
TEST(ElbowAngle, StraitArm)
{
  auto result = arm_kinematics::get_elbow_angle(2.0, 1.0, 1.0);
  ASSERT_TRUE(result.has_value());
  EXPECT_NEAR(result.value(), M_PI, 1e-9);
}
TEST(ElbowAngle, Unreachable)
{
  auto result = arm_kinematics::get_elbow_angle(3.0, 1.0, 1.0);
  EXPECT_FALSE(result.has_value());
}
TEST(ShoulderAngle, Diagonal)
{
  auto result = arm_kinematics::get_shoulder_angle(1.0, 1.0, 1.0, 1.0);
  ASSERT_TRUE(result.has_value());
  EXPECT_NEAR(result.value(), M_PI / 2, 1e-9);
}
TEST(ShoulderAngle, Horizontal)
{
  auto result = arm_kinematics::get_shoulder_angle(std::sqrt(2.0), 0.0, 1.0, 1.0);
  ASSERT_TRUE(result.has_value());
  EXPECT_NEAR(result.value(), M_PI / 4, 1e-9);
}
TEST(ShoulderAngle, Unreachable)
{
  auto result = arm_kinematics::get_shoulder_angle(3.0, 0.0, 1.0, 1.0);
  EXPECT_FALSE(result.has_value());
}
