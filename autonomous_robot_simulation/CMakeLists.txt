cmake_minimum_required(VERSION 3.5)
project(autonomous_robot_simulation)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ------------------------------------------------------------------------------
# Dependencies
# ------------------------------------------------------------------------------

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)   # para ament_python_install_package

find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)

find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)

find_package(pcl_ros REQUIRED)
find_package(pcl_conversions REQUIRED)
find_package(PCL REQUIRED COMPONENTS common io filters registration)
find_package(Eigen3 3.3 REQUIRED NO_MODULE)

# ------------------------------------------------------------------------------
# Include dirs
# ------------------------------------------------------------------------------

# Headers propios
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

# PCL
include_directories(${PCL_INCLUDE_DIRS})
link_directories(${PCL_LIBRARY_DIRS})
add_definitions(${PCL_DEFINITIONS})

set(common_dependencies
  rclcpp
  geometry_msgs
  nav_msgs
  sensor_msgs
  tf2
  tf2_ros
  tf2_geometry_msgs
  pcl_ros
  pcl_conversions
)

# ------------------------------------------------------------------------------
# Ejecutables
# ------------------------------------------------------------------------------

add_executable(tf_broadcaster src/tf_broadcaster.cpp)
ament_target_dependencies(tf_broadcaster ${common_dependencies})

add_executable(pc2_to_xyzi src/pc2_to_xyzi.cpp)
ament_target_dependencies(pc2_to_xyzi ${common_dependencies})
target_link_libraries(pc2_to_xyzi
  Eigen3::Eigen
  ${PCL_LIBRARIES}
)

add_executable(lidar_imu_sync src/lidar_imu_sync.cpp)
ament_target_dependencies(lidar_imu_sync ${common_dependencies})
target_link_libraries(lidar_imu_sync
  Eigen3::Eigen
  ${PCL_LIBRARIES}
)

add_executable(pcd_visualizer src/pcd_visualizer.cpp)
ament_target_dependencies(pcd_visualizer ${common_dependencies})
target_link_libraries(pcd_visualizer
  Eigen3::Eigen
  ${PCL_LIBRARIES}
)

# ------------------------------------------------------------------------------
# Instalación
# ------------------------------------------------------------------------------

install(TARGETS
  tf_broadcaster
  pc2_to_xyzi
  lidar_imu_sync
  pcd_visualizer
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  urdf
  meshes
  materials
  rviz
  worlds
  config
  scripts
  include
  utils
  DESTINATION share/${PROJECT_NAME}
)

install(DIRECTORY
  materials
  meshes
  thumbnails
  DESTINATION share/${PROJECT_NAME}/models/Depot
)

install(FILES
  model.config
  model.sdf
  DESTINATION share/${PROJECT_NAME}/models/Depot
)

# Python package (directorio autonomous_robot_simulation/)
ament_python_install_package(${PROJECT_NAME})

# Ejecutables Python
install(PROGRAMS
  scripts/omni_teleop_keyboard.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
