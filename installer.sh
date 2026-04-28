#!/usr/bin/env bash

set -Eeuo pipefail

ROS_DISTRO="${ROS_DISTRO:-jazzy}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="${COLCON_WS:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
SRC_DIR="${WORKSPACE_DIR}/src"
BUNDLE_DIR="${SCRIPT_DIR}"
SIM_PACKAGE_DIR="${BUNDLE_DIR}/autonomous_robot_simulation"
FAST_LIO_DIR="${BUNDLE_DIR}/fast_lio_ros2"
NDT_OMP_DIR="${BUNDLE_DIR}/ndt_omp_ros2"
LIDAR_LOCALIZATION_DIR="${BUNDLE_DIR}/lidar_localization"
PATH_PLANNING_DIR="${BUNDLE_DIR}/path_planning_dynamic"
NMPC_CONTROLLER_DIR="${BUNDLE_DIR}/nmpc_controller"

log() {
  printf '\n\033[1;34m[installer]\033[0m %s\n' "$*"
}

warn() {
  printf '\n\033[1;33m[installer warning]\033[0m %s\n' "$*" >&2
}

die() {
  printf '\n\033[1;31m[installer error]\033[0m %s\n' "$*" >&2
  exit 1
}

run() {
  log "$*"
  "$@"
}

source_setup() {
  local setup_file="$1"
  [[ -f "${setup_file}" ]] || die "No existe ${setup_file}"
  set +u
  # shellcheck disable=SC1090
  source "${setup_file}"
  set -u
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "Falta el comando requerido: $1"
}

clean_ros_environment() {
  unset AMENT_PREFIX_PATH || true
  unset CMAKE_PREFIX_PATH || true
  unset COLCON_PREFIX_PATH || true
  unset LD_LIBRARY_PATH || true
  unset PYTHONPATH || true
}

verify_bundle_layout() {
  [[ -d "${BUNDLE_DIR}" ]] || die "No existe el bundle ${BUNDLE_DIR}"
  [[ -d "${SIM_PACKAGE_DIR}" ]] || die "Falta ${SIM_PACKAGE_DIR}"
  [[ -d "${FAST_LIO_DIR}" ]] || die "Falta ${FAST_LIO_DIR}"
  [[ -d "${NDT_OMP_DIR}" ]] || die "Falta ${NDT_OMP_DIR}"
  [[ -d "${LIDAR_LOCALIZATION_DIR}" ]] || die "Falta ${LIDAR_LOCALIZATION_DIR}"
  [[ -d "${PATH_PLANNING_DIR}" ]] || die "Falta ${PATH_PLANNING_DIR}"
  [[ -d "${NMPC_CONTROLLER_DIR}" ]] || die "Falta ${NMPC_CONTROLLER_DIR}"
}

casadi_installed() {
  [[ -f "/usr/local/include/casadi/casadi.hpp" ]] || return 1
  [[ -f "/usr/local/lib/libcasadi.so" || -f "/usr/local/lib64/libcasadi.so" || -f "/usr/lib/x86_64-linux-gnu/libcasadi.so" ]]
}

update_bundled_sources() {
  log "Verificando fuentes incluidas en el bundle"

  log "FAST_LIO_DIR: ${FAST_LIO_DIR}"

  if [[ ! -d "${FAST_LIO_DIR}/.git" ]]; then
    run git -C "${FAST_LIO_DIR}" submodule update --init --recursive
  fi

  [[ -f "${FAST_LIO_DIR}/include/ikd-Tree/ikd_Tree.h" ]] || die "Falta include/ikd-Tree/ikd_Tree.h. Inicializa los submodules de fast_lio_ros2."
}

install_casadi_if_needed() {
  log "Verificando CasADi para nmpc_controller"

  if casadi_installed; then
    log "CasADi ya está instalado"
    return
  fi

  local casadi_src_dir="/tmp/casadi"

  if [[ -d "${casadi_src_dir}/.git" ]]; then
    run git -C "${casadi_src_dir}" pull --ff-only
  else
    run git clone https://github.com/casadi/casadi.git "${casadi_src_dir}"
  fi

  run rm -rf "${casadi_src_dir}/build"
  run cmake -S "${casadi_src_dir}" -B "${casadi_src_dir}/build" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DWITH_IPOPT=ON \
    -DWITH_BUILD_IPOPT=ON \
    -DWITH_BUILD_MUMPS=ON \
    -DWITH_BUILD_REQUIRED=ON
  run cmake --build "${casadi_src_dir}/build" -j"$(nproc)"
  run sudo cmake --install "${casadi_src_dir}/build"

  log "Registrando /usr/local/lib para el runtime de CasADi"
  printf '/usr/local/lib\n' | sudo tee /etc/ld.so.conf.d/casadi.conf >/dev/null
  run sudo ldconfig

  casadi_installed || die "CasADi no quedó instalado correctamente en /usr/local"
}

install_apt_dependencies() {
  log "Instalando dependencias APT para ROS 2 ${ROS_DISTRO}, Gazebo, PCL, Eigen, OpenCV y utilidades"

  local ros_packages=(
    "ros-${ROS_DISTRO}-ament-cmake-auto"
    "ros-${ROS_DISTRO}-ament-cmake-python"
    "ros-${ROS_DISTRO}-ament-index-python"
    "ros-${ROS_DISTRO}-rclcpp"
    "ros-${ROS_DISTRO}-rclcpp-lifecycle"
    "ros-${ROS_DISTRO}-std-msgs"
    "ros-${ROS_DISTRO}-sensor-msgs"
    "ros-${ROS_DISTRO}-geometry-msgs"
    "ros-${ROS_DISTRO}-visualization-msgs"
    "ros-${ROS_DISTRO}-nav-msgs"
    "ros-${ROS_DISTRO}-lifecycle-msgs"
    "ros-${ROS_DISTRO}-vision-msgs"
    "ros-${ROS_DISTRO}-image-geometry"
    "ros-${ROS_DISTRO}-message-filters"
    "ros-${ROS_DISTRO}-polygon-msgs"
    "ros-${ROS_DISTRO}-launch"
    "ros-${ROS_DISTRO}-launch-ros"
    "ros-${ROS_DISTRO}-ros2launch"
    "ros-${ROS_DISTRO}-joint-state-publisher"
    "ros-${ROS_DISTRO}-joint-state-publisher-gui"
    "ros-${ROS_DISTRO}-robot-state-publisher"
    "ros-${ROS_DISTRO}-xacro"
    "ros-${ROS_DISTRO}-tf2"
    "ros-${ROS_DISTRO}-tf2-ros"
    "ros-${ROS_DISTRO}-tf2-geometry-msgs"
    "ros-${ROS_DISTRO}-tf2-sensor-msgs"
    "ros-${ROS_DISTRO}-tf2-eigen"
    "ros-${ROS_DISTRO}-tf2-tools"
    "ros-${ROS_DISTRO}-ros-gz"
    "ros-${ROS_DISTRO}-rviz2"
    "ros-${ROS_DISTRO}-rviz-default-plugins"
    "ros-${ROS_DISTRO}-pcl-ros"
    "ros-${ROS_DISTRO}-pcl-conversions"
    "ros-${ROS_DISTRO}-pcl-msgs"
    "ros-${ROS_DISTRO}-grid-map-ros"
    "ros-${ROS_DISTRO}-grid-map-rviz-plugin"
    "ros-${ROS_DISTRO}-lanelet2-core"
    "ros-${ROS_DISTRO}-lanelet2-io"
    "ros-${ROS_DISTRO}-lanelet2-maps"
    "ros-${ROS_DISTRO}-lanelet2-projection"
    "ros-${ROS_DISTRO}-lanelet2-routing"
    "ros-${ROS_DISTRO}-lanelet2-traffic-rules"
    "ros-${ROS_DISTRO}-lanelet2-validation"
    "ros-${ROS_DISTRO}-fastcdr"
    "ros-${ROS_DISTRO}-fastrtps"
    "ros-${ROS_DISTRO}-rmw-fastrtps-cpp"
    "ros-${ROS_DISTRO}-rmw-fastrtps-shared-cpp"
    "ros-${ROS_DISTRO}-rosidl-typesupport-fastrtps-c"
    "ros-${ROS_DISTRO}-rosidl-typesupport-fastrtps-cpp"
  )

  local system_packages=(
    build-essential
    cmake
    gfortran
    git
    libeigen3-dev
    liblapack-dev
    libopencv-dev
    libpcl-dev
    pkg-config
    python3-colcon-common-extensions
    python3-rosdep
    python3-yaml
    unzip
  )

  run sudo apt-get update
  run sudo apt-get install -y "${system_packages[@]}" "${ros_packages[@]}"
}

init_rosdep_if_needed() {
  if [[ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]]; then
    run sudo rosdep init
  fi
  run rosdep update
}

install_rosdeps_for_bundle() {
  log "Instalando rosdeps para los paquetes incluidos en el bundle"
  clean_ros_environment
  source_setup "/opt/ros/${ROS_DISTRO}/setup.bash"

  run rosdep install \
    --rosdistro "${ROS_DISTRO}" \
    --from-paths "${SIM_PACKAGE_DIR}" "${NDT_OMP_DIR}" "${LIDAR_LOCALIZATION_DIR}" "${PATH_PLANNING_DIR}" "${NMPC_CONTROLLER_DIR}" \
    --ignore-src \
    -y
}

build_workspace_packages() {
  log "Compilando ndt_omp_ros2, autonomous_robot_simulation, lidar_localization, fast_lio, path_planning_dynamic y nmpc_controller"
  clean_ros_environment
  source_setup "/opt/ros/${ROS_DISTRO}/setup.bash"

  (
    warn "To build ndt_omp_ros2, it is necessary to use rmw_fastrtps_cpp middleware implementation."
    cd "${WORKSPACE_DIR}"
    run colcon build --packages-select ndt_omp_ros2 --cmake-clean-cache --cmake-args -DCMAKE_BUILD_TYPE=Release
  )
  # Could not find ROS middleware implementation 'rmw_cyclonedds_cpp'.  Choose one of the following: rmw_fastrtps_cpp

  source_setup "${WORKSPACE_DIR}/install/setup.bash"

  (
    cd "${WORKSPACE_DIR}"
    run colcon build --packages-select autonomous_robot_simulation --symlink-install --cmake-clean-cache --cmake-args -DCMAKE_BUILD_TYPE=Release
  )

  source_setup "${WORKSPACE_DIR}/install/setup.bash"

  (
    cd "${WORKSPACE_DIR}"
    run colcon build --packages-select lidar_localization --symlink-install --cmake-clean-cache --cmake-args -DCMAKE_BUILD_TYPE=Release
  ) # Depende de compilacion de ndt_omp_ros2

  source_setup "${WORKSPACE_DIR}/install/setup.bash"

  # (
  #   cd "${WORKSPACE_DIR}"
  #   run colcon build --packages-select fast_lio --symlink-install --cmake-clean-cache --cmake-args -DCMAKE_BUILD_TYPE=Release
  # )

  source_setup "${WORKSPACE_DIR}/install/setup.bash"

  (
    cd "${WORKSPACE_DIR}"
    run colcon build --packages-select path_planning_dynamic --symlink-install --cmake-clean-cache --cmake-args -DCMAKE_BUILD_TYPE=Release
  )

  source_setup "${WORKSPACE_DIR}/install/setup.bash"

  (
    cd "${WORKSPACE_DIR}"
    run colcon build --packages-select nmpc_controller --symlink-install --cmake-clean-cache --cmake-args -DCMAKE_BUILD_TYPE=Release
  )
}

validate_installation() {
  log "Validando instalación"
  clean_ros_environment
  source_setup "/opt/ros/${ROS_DISTRO}/setup.bash"
  source_setup "${WORKSPACE_DIR}/install/setup.bash"

  run pkg-config --modversion pcl_common eigen3 opencv4
  run ros2 pkg prefix ndt_omp_ros2
  run ros2 pkg prefix autonomous_robot_simulation
  run ros2 pkg prefix lidar_localization
  # run ros2 pkg prefix fast_lio
  run ros2 pkg prefix path_planning_dynamic
  run ros2 pkg prefix nmpc_controller
  casadi_installed || die "CasADi no está disponible para nmpc_controller"

  local depot_dir="${WORKSPACE_DIR}/install/autonomous_robot_simulation/share/autonomous_robot_simulation/models/Depot"
  [[ -f "${depot_dir}/model.config" ]] || die "Falta ${depot_dir}/model.config"
  [[ -f "${depot_dir}/model.sdf" ]] || die "Falta ${depot_dir}/model.sdf"
  [[ -f "${depot_dir}/meshes/Depot.dae" ]] || die "Falta ${depot_dir}/meshes/Depot.dae"
  [[ -f "${WORKSPACE_DIR}/install/lidar_localization/share/lidar_localization/launch/lidar_localization_launch.py" ]] || die "Falta lidar_localization_launch.py instalado"
  # [[ -f "${WORKSPACE_DIR}/install/fast_lio/share/fast_lio/config/simulated.yaml" ]] || die "Falta fast_lio/config/simulated.yaml instalado"
  [[ -f "${WORKSPACE_DIR}/install/path_planning_dynamic/share/path_planning_dynamic/config/params.yaml" ]] || die "Falta path_planning_dynamic/config/params.yaml instalado"
  [[ -f "${WORKSPACE_DIR}/install/nmpc_controller/share/nmpc_controller/launch/sim_nmpc.launch.py" ]] || die "Falta nmpc_controller/launch/sim_nmpc.launch.py instalado"
  [[ -f "${WORKSPACE_DIR}/install/nmpc_controller/share/nmpc_controller/config/sim_nmpc.yaml" ]] || die "Falta nmpc_controller/config/sim_nmpc.yaml instalado"

  # if ! nm -D "/opt/ros/${ROS_DISTRO}/lib/libfastcdr.so.2" | c++filt | grep -q 'eprosima::fastcdr::Cdr::serialize(unsigned int)'; then
  #   warn "libfastcdr.so.2 no exporta Cdr::serialize(unsigned int). Si display_map_launch.py falla con undefined symbol, actualiza ros-${ROS_DISTRO}-fastcdr/fastrtps."
  # fi
}

print_next_steps() {
  cat <<EOF

Instalación terminada.

Abre una terminal nueva y ejecuta:

  cd ${WORKSPACE_DIR}
  source /opt/ros/${ROS_DISTRO}/setup.bash
  source install/setup.bash

Para probar Gazebo:

  ros2 launch autonomous_robot_simulation one_robot_ign_launch.py

Para lanzar localización:

  ros2 launch lidar_localization lidar_localization_launch.py

Para lanzar FAST-LIO:

  ros2 launch fast_lio mapping.launch.py config_file:=simulated.yaml

Para lanzar path planning:

  ros2 launch path_planning_dynamic planning.launch.py

Para lanzar NMPC:

  ros2 launch nmpc_controller sim_nmpc.launch.py

Nota: no sources ~/ros2_jazzy/install/setup.bash en la misma terminal. Este instalador usa /opt/ros/${ROS_DISTRO}.
EOF
}

main() {
  [[ -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]] || die "No existe /opt/ros/${ROS_DISTRO}/setup.bash. Instala ROS 2 ${ROS_DISTRO} primero."
  [[ -d "${WORKSPACE_DIR}" ]] || die "No existe el workspace ${WORKSPACE_DIR}"
  [[ -d "${SRC_DIR}" ]] || die "No existe ${SRC_DIR}"

  # verify_bundle_layout

  # require_command sudo
  # require_command apt-get
  # require_command git
  # require_command cmake
  # require_command make
  # require_command colcon
  # require_command ldconfig
  # require_command rosdep
  # require_command pkg-config
  # require_command nm
  # require_command c++filt

  # install_apt_dependencies
  # init_rosdep_if_needed
  # update_bundled_sources #Fast_lio submoodule (clonar el sub.modulo esta mal y se necesita el repo)
  # install_casadi_if_needed
  # install_rosdeps_for_bundle
  build_workspace_packages
  validate_installation
  print_next_steps
}

main "$@"
