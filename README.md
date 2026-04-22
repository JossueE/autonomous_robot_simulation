
# Autonomous-Car-Simulation (ROS 2 + Gazebo) 🏎️
**Author:** Jossue Espinoza <br>

[![ROS 2](https://img.shields.io/badge/ROS%202-Jazzy-blue.svg)](https://docs.ros.org/en/jazzy/)
[![Gazebo](https://img.shields.io/badge/Gazebo-Harmonic-orange.svg)](https://gazebosim.org/docs/harmonic/)
[![SLAM](https://img.shields.io/badge/SLAM-Integration-brightgreen.svg)](https://github.com/SteveMacenski/slam_toolbox)
[![Python](https://img.shields.io/badge/Python-3.12+-yellow.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

This ROS 2 package provides a complete simulation framework for mobile robots in **Gazebo**.  
It acts as a bridge between simulated environments, enabling seamless integration of **LiDAR**, **IMU**, and **vehicle models**.

Within this repository, you’ll find everything needed to:

- 🛰️ Simulate different **LiDARs**, **vehicles**, and **sensors**.  
- 🔄 **Synchronize IMU and LiDAR** data for accurate mapping.  
- 🗺️ Generate and **save maps** using FAST LIO.  
- 🤖 Add custom **mobile robots** to your simulations.  
- 🧠 Test and evaluate **SLAM algorithms** in virtual environments.

**NOTE:** this repo was tested on Ubuntu 24.04 LTS, with ROS 2 Jazzy and Gazebo Harmonic.

--- 
<p align="center">
  <img src="docs/slam.png" alt="Robot Localization in Real Time with Simulated Lidar" width="800">
  <br>
  <em>Robot Localization in Real Time with Simulated Lidar</em>
</p>  

## 📚 Table of Contents
- [Installation](#installation)

- [Configuration](#configuration)
    - [Configure The Simulation](#configure-the-simulation)
    - [Adding New Robots and Worlds](#adding-new-robots-and-worlds)
    - [Configure your LiDAR (URDF/Xacro + Ignition)](#configure-your-lidar-urdfxacro--ignition)
    - [Configure your IMU (URDF/Xacro + Ignition)](#configure-your-imu-urdfxacro--ignition)
    - [Configure FAST_LIO](#configure-fast_lio)
    - [Configure Localization](#configure-localization)
    - [Configure Path Planning](#configure-path-planning)

- [Usage](#usage)
    - [Mapping](#mapping)
        - [Launching the Robot in Gazebo](#launching-the-robot-in-gazebo)
        - [Launching the SLAM (FAST_LIO Mapping)](#launching-the-slam-fast_lio-mapping)
        - [Teleoperating the Robot](#teleoperating-the-robot) 
        - [Saving the Map (.pcd)](#saving-the-map-pcd)
        - [Displaying the Map](#displaying-the-map)
    - [Localization](#localization)
        - [Localization in a Previous Map Saved](#localization-in-a-previous-map-saved)
    - [Path Planning](#path-planning)


---

## Installation

> [!IMPORTANT]
> Use the automatic installer. This README no longer documents a separate manual installation flow.

### Automatic installer for Jazzy

This repository was validated on Ubuntu 24.04 with ROS 2 Jazzy and Gazebo Harmonic.

Clone the repository inside the `src` directory of your workspace and run the installer:

```bash
cd ~/colcon_ws/src
git clone https://github.com/JossueE/autonomous_robot_simulation.git
cd autonomous_robot_simulation
./installer.sh
```

The installer assumes this repository is located inside `~/colcon_ws/src`. If your workspace path is different, set `COLCON_WS`:

```bash
COLCON_WS=/path/to/colcon_ws ./installer.sh
```

Use a clean terminal sourced only with `/opt/ros/jazzy/setup.bash` or with no ROS2 setup sourced. Do not mix this flow with `~/ros2_jazzy/install/setup.bash`.

The installer does the following:

- Installs the required ROS 2 Jazzy, Gazebo Harmonic, RViz, bridge, and build dependencies.
- Installs `PCL` and `Eigen` using the system packages expected by this workspace: `libpcl-dev`, `libeigen3-dev`, `ros-jazzy-pcl-ros`, `ros-jazzy-pcl-conversions`, `ros-jazzy-pcl-msgs`, and `ros-jazzy-tf2-eigen`.
- Installs CasADi for `nmpc_controller`.
- Runs `rosdep` for the bundled packages.
- Initializes the bundled `fast_lio` submodule `ikd-Tree` when needed.
- Builds `ndt_omp_ros2`, `autonomous_robot_simulation`, `lidar_localization`, `fast_lio`, `path_planning_dynamic`, and `nmpc_controller`.
- Validates the resulting installation and prints the next launch commands.

---

## ⚙️ Configuration

### 🎮 Configure The Simulation

The `one_robot_ign_launch.py` file launches **Gazebo (Ignition)** using a predefined world and spawns the selected robot model automatically.

Inside the repository, the simulation package keeps its launch configuration in `autonomous_robot_simulation/config/config.yaml`.  
This file contains adjustable parameters for the simulation, as well as configuration options for the LiDAR and IMU functionalities.

> [!IMPORTANT]
> The world file **depot.sdf** includes the warehouse as `model://Depot`.  
> During `colcon build`, this repository installs the bundled Depot model into `share/autonomous_robot_simulation/models/Depot`, and `one_robot_ign_launch.py` adds `share/autonomous_robot_simulation/models` to `GZ_SIM_RESOURCE_PATH`.
> You do not need to copy `Depot.zip` into `~/.ignition/models` or `~/.gz/models`.

```bash
cd ~/colcon_ws
colcon build --symlink-install --packages-select autonomous_robot_simulation --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash

find install/autonomous_robot_simulation/share/autonomous_robot_simulation/models/Depot \
  -maxdepth 2 \
  \( -name model.config -o -name model.sdf -o -name Depot.dae \)
```

Expected files:

```text
install/autonomous_robot_simulation/share/autonomous_robot_simulation/models/Depot/model.config
install/autonomous_robot_simulation/share/autonomous_robot_simulation/models/Depot/model.sdf
install/autonomous_robot_simulation/share/autonomous_robot_simulation/models/Depot/meshes/Depot.dae
```

If Gazebo prints `Unable to find uri[model://Depot]`, rebuild `autonomous_robot_simulation` and source `install/setup.bash` again before launching.

### 🤖 Adding New Robots and Worlds

You can easily **add a new robot model** by creating a **URDF** description in  
`urdf/`, preferably in **`.xacro`** format for easier parameterization and reuse.

To include a new environment, simply **add your world file** in  
`worlds/` using the **`.sdf`** format.

Once added, you can select them in the launch file by updating:
```python
robot_model = '<your_robot_name>'
world_file = '<your_world_name>.sdf'
```
> [!IMPORTANT]
> To obtain a correct behavior of the sensors, the world.sdf file MUST be correctly set by adding the corresponding 'plugin' tag inside the 'world' tag. For more information. please refer to https://gazebosim.org/docs/latest/sensors/.

### 📡 Configure your LiDAR (URDF/Xacro + Ignition)

This repo mounts a LiDAR on `base_link` and spawns an Ignition (Gazebo) ray sensor.  
You can tune **pose**, **FOV**, **resolution**, **rate**, **range** and the **topic** directly in `autonomous_robot_simulation/config/config.yaml`.

> [!TIP]
> Use **`gpu_lidar`** if you have GPU available (faster). Use **`lidar`** for CPU-only.
> Also, can add or modify the noise directly in your .xacro file.

```yaml
    lidar:
    lidar_frequency: 10.0              # Lidar frequency in Hz (typical value: 10 Hz)
    lidar_out_topic: '/lidar/points'   # Output topic for published point clouds

    horizontal_samples: 360            # Number of horizontal scan samples per rotation
    horizontal_resolution: 1           # Horizontal angular resolution in degrees
    horizontal_min_angle: -3.14159     # Minimum horizontal angle (radians)
    horizontal_max_angle:  3.14159     # Maximum horizontal angle (radians)

    vertical_samples: 32               # Number of vertical scan lines
    vertical_resolution: 1             # Vertical angular resolution in degrees
    vertical_min_angle: -0.78539       # Minimum vertical angle (-45°)
    vertical_max_angle:  0.78539       # Maximum vertical angle (+45°)

    min_distance: 0.2                  # Minimum measurable distance (meters)
    max_distance: 100.0                # Maximum measurable distance (meters)
    resolution: 0.017453               # Angular resolution in radians (~1°)
```

In this repository, a general LiDAR configuration example is provided.  
If you want to adapt it to a specific sensor, here are some key parameters to tune:

- **`lidar_frequency`** — Default is `10 Hz`, since most LiDARs operate around this range. Adjust it according to your sensor specifications.  
- **`horizontal_*` and `vertical_*` parameters** — Define the LiDAR’s scanning structure:
  - `samples` → number of beams or steps per axis  
  - `resolution` → angular precision (° or radians)  
  - `min_angle` / `max_angle` → scanning limits for each axis  
- **`min_distance`, `max_distance`, and `resolution`** — Define the LiDAR’s detection range and precision.  
  Ensure these match your hardware’s datasheet for accurate simulation results.


### 📊 Configure your IMU (URDF/Xacro + Ignition)

In this repository you’ll find a simulated IMU with a configurable update rate.  
By default, a small amount of noise is enabled to approximate real-world behavior.  
If you want to customize noise, edit your robot’s `.xacro` to pass the values below to the IMU plugin.

```yaml
imu:
    imu_frequency : 50.0 # The frequency of the lidar in Hz
    imu_out_topic: '/imu' #The output topic of the IMU
```

### ⚡ Configure FAST_LIO
FAST_LIO in this bundle consumes standard `sensor_msgs/msg/PointCloud2` plus IMU topics.
The repository already includes a ready-to-edit config file at `fast_lio_ros2/config/simulated.yaml`, so you do not need to copy or paste a FAST_LIO config from somewhere else. Edit that bundled file, or create another config in the same folder only if you need a different sensor profile.

> [!IMPORTANT]
> In `fast_lio_ros2/config/simulated.yaml`, make sure these values stay aligned with your simulation config:
> - `common.lid_topic` ← your `lidar_out_topic`
> - `common.imu_topic` ← your `imu_out_topic`
> - `preprocess.scan_line` ← your `vertical_samples`
> - `preprocess.scan_rate` ← your `lidar_frequency` LiDAR rotation rate in Hz (e.g., 10)
> - `mapping.fov_degree` ← `horizontal_max_angle` and `horizontal_min_angle` (in degrees)
> - `mapping.det_range` ← your `max_distance`

```yaml
/**:
    ros__parameters:
        feature_extract_enable: false
        point_filter_num: 4
        max_iteration: 3
        filter_size_surf: 0.2
        filter_size_map: 0.2
        cube_side_length: 1000.0
        runtime_pos_log_enable: true
        map_file_path: PCD/name_of_your_map.pcd # <----------------- HERE YOU DEFINE YOUR OUTPUT FILE ----------------->

        common:
            lid_topic:  "/lidar/points"  # <----------------- HERE YOU PUT EXACTLY THE lidar_out_topic DEFINED BEFORE ----------------->
            imu_topic:  "/imu"      # <----------------- HERE YOU PUT EXACTLY THE imu_out_topic DEFINED BEFORE ----------------->
            time_offset_lidar_to_imu: 0.0 # Static time offset between lidar and IMU, in seconds.

        preprocess:
            lidar_type: 5                # 2 Velodyne, 3 Ouster, 4 generic PointCloud2, 5 simulated <----- DO NOT MODIFY
            scan_line: 32                # <----------------- HERE YOU PUT EXACTLY THE vertical_samples DEFINED BEFORE ----------------->
            scan_rate: 10                # <----------------- HERE YOU PUT EXACTLY THE lidar_frequency DEFINED BEFORE ----------------->
            timestamp_unit: 0            # the unit of time/t field in the PointCloud2: 0-second, 1-milisecond, 2-microsecond, 3-nanosecond. <----- DO NOT MODIFY
            blind: 0.05

        mapping:
            acc_cov: 0.1
            gyr_cov: 0.1
            b_acc_cov: 0.0001
            b_gyr_cov: 0.0001
            fov_degree:    360.0          # <----------------- HERE YOU PUT EXACTLY THE horizontal_samples DEFINED BEFORE ----------------->       
            det_range:     100.0          # <----------------- HERE YOU PUT EXACTLY THE max_distance DEFINED BEFORE ----------------->
            extrinsic_est_en:  false      # true: enable the online estimation of IMU-LiDAR extrinsic,

            extrinsic_T: [-0.04, 0., 0.07] # <----------------- CHECK the note IMPORTANT BELOW 
            extrinsic_R: [ 1., 0., 0., 
                           0., 1., 0., 
                           0., 0., 1.]

        publish:
            map_pub_en: true 
            path_en:  false
            scan_publish_en:  true       # false: close all the point cloud output
            dense_publish_en: true       # false: low down the points number in a global-frame point clouds scan.
            scan_bodyframe_pub_en: true  # true: output the point cloud scans in IMU-body-frame

        pcd_save:
            pcd_save_en: true
            interval: -1                 # how many LiDAR frames saved in each pcd file; 
                                        # -1 : all frames will be saved in ONE pcd file, may lead to memory crash when having too much frames.
```

> [!WARNING]
> Make sure that:
> - In your URDF/Xacro, the LiDAR pose relative to the IMU/base_link matches
> - In FAST_LIO, `mapping.extrinsic_T` and `mapping.extrinsic_R` are set to that same transform
> 
> Once the extrinsics are correct, you should see stable logs like:
> `In num: 11520 downsamp ≈ 2400 ... effect num ≈ 1200`
> and no more `No point, skip this scan!`.

The `extrinsic_T` and `extrinsic_R` parameters describe the **pose of the LiDAR with respect to the IMU frame** (i.e., how the LiDAR is positioned and oriented relative to the IMU).

- `extrinsic_T` is the **translation vector** from the IMU frame to the LiDAR frame.  
- `extrinsic_R` is the **rotation matrix** from the IMU frame to the LiDAR frame.

In my setup, the IMU is placed at the origin of `base_link` `(0, 0, 0)`, and the LiDAR is mounted with an offset defined by the `lidar_joint` in the robot model.  
Because of that, the values in my `extrinsic_T` **directly match** the translation defined for the `lidar_joint` (the LiDAR position relative to `base_link` / IMU).

In your case, you must set:

- `extrinsic_T` to the **XYZ offset** from your IMU (body frame) to your LiDAR (e.g., “the LiDAR is 0.2 m in front and 0.1 m above the IMU”).  
- `extrinsic_R` to the **rotation** that represents how the LiDAR is oriented relative to the IMU (for example, if the LiDAR is tilted or rotated with respect to the IMU axes).

In other words:  
> You need to configure `extrinsic_T` and `extrinsic_R` according to the **actual relative pose** between your IMU and LiDAR in **your** robot, not by copying the values from my configuration.  
They should be consistent with your URDF/SDF model and your TF tree.


> [!NOTE]
> This step is optional — you can also specify the `config_file` directly in the launch command (see the **Launch** section below).
---


### 🗺️ Configure Localization

The localization package now owns its parameters in `lidar_localization/config/localization.yaml`.
In that file, you can fine-tune how the **localization node** behaves, including:

- The registration algorithm used for pose estimation.
- The precision and robustness of NDT-based matching.
- Whether to use a precomputed PCD map or not.
- The initial pose of the robot in the map frame.
- The reference frames used for TF (`map`, `odom`, `base_link`).
- The use of additional sensors such as odometry and IMU.

Below is an example of the ROS 2 parameter file used by `lidar_localization`:

```yaml
lidar_localization:
  ros__parameters:
    registration_method: "NDT_OMP"   # Registration method used for scan matching "GICP", "NDT", "GICP_OMP" o "NDT_OMP"
    score_threshold: 2.0             # Threshold to accept/reject a registration result
    ndt_resolution: 1.0              # NDT grid resolution [m]
    ndt_step_size: 0.1               # Step size for the optimizer
    ndt_num_threads: 4               # Number of threads used by NDT_OMP
    transform_epsilon: 0.01          # Convergence criteria for the transformation
    voxel_leaf_size: 0.2             # Leaf size for downsampling the input cloud
    use_pcd_map: true                # Use a prebuilt PCD map for localization
    map_path: "package://fast_lio/PCD/test.pcd"
    set_initial_pose: true           # Whether set false, you may have to publish the initial pose via RViz in /initialpose topic
    initial_pose_x: 0.0              # Initial pose (x) in map frame
    initial_pose_y: 0.0              # Initial pose (y) in map frame
    initial_pose_z: 0.0              # Initial pose (z) in map frame
    initial_pose_qx: 0.0             # Initial orientation (qx) in map frame
    initial_pose_qy: 0.0             # Initial orientation (qy) in map frame
    initial_pose_qz: 0.0             # Initial orientation (qz) in map frame
    initial_pose_qw: 1.0             # Initial orientation (qw) in map frame
    use_odom: true                   # Enable fusion with wheel odometry
    use_imu: false                   # Enable fusion with IMU data
    enable_debug: true               # Publish extra debug information / topics
    global_frame_id: map             # Global reference frame
    odom_frame_id: odom              # Odometry frame
    base_frame_id: base_footprint    # Base frame used by localization to keep the TF tree consistent
    enable_map_odom_tf: true         # Publish map->odom and let robot_state_publisher keep base_footprint->base_link->lidar_link

```
### 🛣️ Configure Path Planning
`path_planning_dynamic` is also bundled in this repository.
Configure it directly in `path_planning_dynamic/config/params.yaml`.
Remember to set all parameters according to your robot; the default values are tuned to work safely with `sensors_diffbot`.
Also, make sure `map_path` points to your `.osm` map file.

## 🚀 Usage
> [!IMPORTANT]
> The following sections are intended to be used as a **step-by-step usage guide**, from zero to a complete workflow.
> You can follow them in order, or jump directly to the part you need once you are familiar with the setup.
>
> We work with **two main workflows**:
> - **Mapping** 🗺️  
>   You will:
>   1. **Launch the robot in Gazebo**  
>   2. **Launch FAST_LIO (Mapping)** to build a LiDAR map (.pcd)  
>   3. **Teleoperate the robot** around the environment  
>   4. **Save the map (.pcd)**  
>   5. (Optional) **Display the final map**
>
> - **Localization** 📍  
>   You will:
>   1. **Launch the robot in Gazebo**  
>   2. **Load the previously saved map** and start the localization node  
>   3. **Teleoperate the robot** again, now using the existing map for localization


### 🎮 Launching the Robot in Gazebo

You can start the simulation with:

```bash
cd ~/colcon_ws
colcon build --packages-select ndt_omp_ros2 fast_lio autonomous_robot_simulation --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
```
Then:
```bash
ros2 launch autonomous_robot_simulation one_robot_ign_launch.py
```
> [!NOTE]
> - The first launch may take longer while Gazebo/Ignition caches assets and loads world resources.
> - RViz should display the converted LiDAR topic `/lidar/points_pcl` with **Reliability Policy: Best Effort**. The raw Gazebo topic `/lidar/points_ign` may use a Gazebo-scoped frame such as `r1/base_footprint/gpu_lidar`, which can produce TF errors in RViz.
> - If you change the **LiDAR** or **IMU** topic names, update your RViz displays (reselect topics) so they match the new names.


### 🕹️ Teleoperating the Robot

To teleoperate both the **_differential_** and **_omnidirectional_** mobile robot, use the package node:

```bash
ros2 run autonomous_robot_simulation omni_teleop_keyboard.py
```

To publish a velocity from terminal:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.1, y: 0.1}, angular: {z: 0.3}}"
```
To publish a velocity directly on a **Ignition** Topic from terminal:

```bash
ign topic -t "/model/r1/cmd_vel" -m ignition.msgs.Twist -p "linear: {x: 0.5, y: 0.5}"
```
---


### 🗺️ Mapping

#### ⚡ Launching the SLAM (FAST_LIO Mapping)

In a new terminal and with the steps before completed.

```bash
cd ~/colcon_ws
source install/setup.bash
ros2 launch fast_lio mapping.launch.py
```
Or whit the config_file as an argument:
```bash
ros2 launch fast_lio mapping.launch.py config_file:=simulated.yaml
```
RViz will open with the LiDAR map view. Any warnings or errors will appear in the terminal.

> [!NOTE]
> For algorithm background and the upstream project history, see the original FAST_LIO_ROS2 repository:
> [https://github.com/Ericsii/FAST_LIO_ROS2](https://github.com/Ericsii/FAST_LIO_ROS2)

---

#### 💾 Saving the Map (.pcd)

Move the robot to cover the environment and avoid losing measurements.
When you’re satisfied with the coverage, call the service to save the map (FAST_LIO saves PCD files):

 - Enable the map-save flag `pcd_save.pcd_save_en`, `publish.map_pub_en` and set the output `map_file_path` in `fast_lio/config/simulated.yaml` (e.g., map_file_path: `PCD/name_of_your_map.pcd` and ).  
 - With **Launching the SLAM (FAST_LIO Mapping)** active
 - Open RQt and switch to `Plugins->Services->Service Caller`. Trigger the service `/map_save`, then the pcd map file will be generated

or in a new terminal: 
```bash
ros2 service call /map_save std_srvs/srv/Trigger "{}" 
```
> [!WARNING]
> If you see logs with:
> `No point, skip this scan!` and very low `downsamp` values (e.g. `downsamp 1`)
> check your IMU–LiDAR extrinsics.

#### 📊 Displaying the Map

Once your map has been saved, you can visualize the final result with:

> [!IMPORTANT]
> Make sure the path in `autonomous_robot_simulation/config/config.yaml` matches exactly the location where your map was saved.
> Be careful when mixing relative and absolute paths.
> The default value uses `package://fast_lio/PCD/test.pcd`.

```bash
ros2 launch autonomous_robot_simulation display_map_launch.py
```

If `pcd_visualizer` prints a Fast-CDR symbol error while publishing `/map`:

```text
undefined symbol: _ZN8eprosima7fastcdr3Cdr9serializeEj
```

your ROS 2 Jazzy installation has mixed Fast-CDR/Fast-DDS package versions. Update the Fast-CDR/Fast-DDS runtime packages, then open a new terminal and source the workspace again:

```bash
sudo apt-get update
sudo apt-get install -y \
  ros-jazzy-fastcdr \
  ros-jazzy-fastrtps \
  ros-jazzy-rmw-fastrtps-cpp \
  ros-jazzy-rmw-fastrtps-shared-cpp \
  ros-jazzy-rosidl-typesupport-fastrtps-cpp \
  ros-jazzy-rosidl-typesupport-fastrtps-c

source /opt/ros/jazzy/setup.bash
source ~/colcon_ws/install/setup.bash
```

The map path in `autonomous_robot_simulation/config/config.yaml` may be absolute, package-based, or relative to the installed package share directory. The default test map is:

```yaml
map_file_path: "package://fast_lio/PCD/test.pcd"
```

### 📍 Localization 
#### 🗺️ Localization in a Previous Map Saved

First you have to run the [**Launching the Robot in Gazebo**](https://github.com/JossueE/autonomous_robot_simulation?tab=readme-ov-file#launching-the-robot-in-gazebo) exactly as we defined in the previous section Mapping. 

For localization, you can start the simulation without the default RViz2 window:
```bash
cd ~/colcon_ws
source install/setup.bash
ros2 launch autonomous_robot_simulation one_robot_ign_launch.py rviz:=false
```
Start RViz2 with the Localization Configuration

In a new terminal:
```bash
cd ~/colcon_ws
source install/setup.bash
rviz2 -d install/autonomous_robot_simulation/share/autonomous_robot_simulation/rviz/localization.rviz
```
Launch the Localization Node
In another terminal:
```bash
cd ~/colcon_ws
source install/setup.bash
ros2 launch lidar_localization lidar_localization_launch.py
```

The localization launch now reads its own ROS 2 parameter file from `lidar_localization/config/localization.yaml`. By default it subscribes to the converted LiDAR cloud `/lidar/points_pcl`, uses `/imu/data_ign`, and loads the example map from `package://fast_lio/PCD/test.pcd`. Keep the simulation launch running first so `pc2_to_xyzi`, TF, and the Gazebo bridge are available.

Finally, you can teleoperate the robot using the same teleop node described earlier in [**Teleoperating the Robot**](#teleoperating-the-robot) defined before. 

### 🛣️ Path Planning 
Follow exactly the same steps described above for **Localization** and, once the simulation and localization are running, build and launch the path planning node:

```bash
cd ~/colcon_ws
colcon build --symlink-install --packages-select path_planning_dynamic --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
ros2 launch path_planning_dynamic planning.launch.py 
```
### NMPC Control

colcon build --base-paths src/autonomous_robot_simulation/nmpc_controller --packages-select nmpc_controller

source ~/colcon_ws/install/setup.bash
ros2 launch nmpc_controller sim_nmpc.launch.py

ros2 launch nmpc_controller sim_nmpc.launch.py costmap_topic:=/occupancy_grid_obstacles
