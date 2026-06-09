cmake_minimum_required(VERSION 3.8)
project(dofbot_kinematics)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(kdl_parser REQUIRED)
# find_package(orocos_kdl REQUIRED)
find_package(dofbot_interfaces REQUIRED)

add_executable(dofbot_kinematics_node src/dofbot_kinematics_node.cpp)

target_include_directories(dofbot_kinematics_node PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
  # ${orocos_kdl_INCLUDE_DIRS}
)

# target_include_directories(dofbot_kinematics_node PRIVATE
#   ${orocos_kdl_INCLUDE_DIRS}
# )

# target_link_libraries(dofbot_kinematics_node
#   PRIVATE
#   ${orocos_kdl_LIBRARIES}
# )

ament_target_dependencies(dofbot_kinematics_node
  rclcpp
  geometry_msgs
  kdl_parser
  dofbot_interfaces
)

install(TARGETS
  dofbot_kinematics_node
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)


if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
