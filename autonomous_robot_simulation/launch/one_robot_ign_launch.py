import os
from pathlib import Path

import xacro
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, SetEnvironmentVariable, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

package_name = 'autonomous_robot_simulation'


def load_launch_parameters(config_path: str, node_name: str) -> dict:
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file) or {}

    node_config = config.get(node_name) or config.get('/**')
    if isinstance(node_config, dict):
        return node_config.get('ros__parameters', node_config)

    return config


def get_launch_param(params: dict, section_name: str, param_name: str, default_value):
    section = params.get(section_name)
    if isinstance(section, dict) and param_name in section:
        return section[param_name]

    return params.get(param_name, default_value)


def normalize_sequence_arg(value) -> str:
    if isinstance(value, (list, tuple)):
        return ' '.join(str(item) for item in value)

    return str(value)


def normalize_pose(value):
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError(
            'The simulation pose parameter must contain exactly four values: [x, y, z, yaw].'
        )

    return [str(item) for item in value]


def launch_setup(context, *args, **kwargs):
    del args, kwargs

    this_pkg_path = get_package_share_directory(package_name)
    config_path = os.path.abspath(
        os.path.expandvars(
            os.path.expanduser(LaunchConfiguration('simulation_params_file').perform(context))
        )
    )
    cfg = load_launch_parameters(config_path, 'one_robot_ign_launch')
    use_sim_time = LaunchConfiguration('use_sim_time')

    robot_model = get_launch_param(cfg, 'simulation', 'robot_model', 'ackermann')
    robot_ns = get_launch_param(cfg, 'simulation', 'robot_ns', 'r1')
    pose = normalize_pose(
        get_launch_param(cfg, 'simulation', 'pose', ['1.0', '0.0', '0.0', '0.0'])
    )
    robot_base_color = normalize_sequence_arg(
        get_launch_param(cfg, 'simulation', 'robot_base_color', '0.0 0.0 1.0 0.95')
    )
    world_file = get_launch_param(cfg, 'simulation', 'world_file', 'depot.sdf')

    lidar_frequency = get_launch_param(cfg, 'lidar', 'lidar_frequency', 10.0)
    lidar_out_topic = get_launch_param(cfg, 'lidar', 'lidar_out_topic', '/lidar')
    lidar_frame_id = get_launch_param(cfg, 'lidar', 'lidar_frame_id', 'lidar_link')
    horizontal_samples = get_launch_param(cfg, 'lidar', 'horizontal_samples', 360)
    horizontal_resolution = get_launch_param(cfg, 'lidar', 'horizontal_resolution', 1.0)
    horizontal_min_angle = get_launch_param(cfg, 'lidar', 'horizontal_min_angle', -3.14159)
    horizontal_max_angle = get_launch_param(cfg, 'lidar', 'horizontal_max_angle', 3.14159)
    vertical_samples = get_launch_param(cfg, 'lidar', 'vertical_samples', 32)
    vertical_resolution = get_launch_param(cfg, 'lidar', 'vertical_resolution', 1.0)
    vertical_min_angle = get_launch_param(cfg, 'lidar', 'vertical_min_angle', -0.78539)
    vertical_max_angle = get_launch_param(cfg, 'lidar', 'vertical_max_angle', 0.78539)
    min_distance = get_launch_param(cfg, 'lidar', 'min_distance', 0.2)
    max_distance = get_launch_param(cfg, 'lidar', 'max_distance', 100.0)
    resolution = get_launch_param(cfg, 'lidar', 'resolution', 0.017453)

    imu_frequency = get_launch_param(cfg, 'imu', 'imu_frequency', 50.0)
    imu_out_topic = get_launch_param(cfg, 'imu', 'imu_out_topic', '/imu')

    gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=[
            os.path.join(this_pkg_path, 'models'),
            ':' + os.path.join(this_pkg_path, 'worlds'),
            ':' + str(Path(this_pkg_path).parent.resolve()),
        ],
    )

    open_rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', str(this_pkg_path + "/rviz/simulation.rviz")],
        parameters=[{'use_sim_time': use_sim_time}],
    )

    open_ign = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch'),
            '/gz_sim.launch.py',
        ]),
        launch_arguments=[
            ('gz_args', [this_pkg_path + "/worlds/" + world_file, ' -v 4', ' -r'])
        ],
    )

    xacro_file = os.path.join(this_pkg_path, 'urdf', robot_model + '.xacro')
    print("Loading config file: ", xacro_file, flush=True)

    try:
        doc = xacro.process_file(
            xacro_file,
            mappings={
                'base_color': robot_base_color,
                'lidar_frequency': str(lidar_frequency),
                'horizontal_samples': str(horizontal_samples),
                'horizontal_resolution': str(horizontal_resolution),
                'horizontal_min_angle': str(horizontal_min_angle),
                'horizontal_max_angle': str(horizontal_max_angle),
                'vertical_samples': str(vertical_samples),
                'vertical_resolution': str(vertical_resolution),
                'vertical_min_angle': str(vertical_min_angle),
                'vertical_max_angle': str(vertical_max_angle),
                'min_distance': str(min_distance),
                'max_distance': str(max_distance),
                'resolution': str(resolution),
                'imu_frequency': str(imu_frequency),
            },
        )
    except Exception:
        import sys
        import traceback

        print("Error processing xacro:", xacro_file, file=sys.stderr)
        traceback.print_exc()
        raise

    robot_desc = doc.toprettyxml(indent='  ')

    gz_spawn_entity_node = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-string', robot_desc,
            '-x', pose[0], '-y', pose[1], '-z', pose[2],
            '-R', '0.0', '-P', '0.0', '-Y', pose[3],
            '-name', robot_ns,
            '-allow_renaming', 'false',
        ],
    )

    gz_spawn_entity = TimerAction(
        period=7.0,
        actions=[gz_spawn_entity_node],
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_desc,
            'use_sim_time': use_sim_time,
        }],
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/model/' + robot_ns + '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/model/' + robot_ns + '/odometry@nav_msgs/msg/Odometry@gz.msgs.Odometry',
            '/world/world_model/model/' + robot_ns + '/joint_state@sensor_msgs/msg/JointState[gz.msgs.Model',

            # LIDAR
            '/lidar@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan',
            '/lidar/points@sensor_msgs/msg/PointCloud2@gz.msgs.PointCloudPacked',

            #DEEP CAMERA
            # '/depth_camera/points@sensor_msgs/msg/PointCloud2@gz.msgs.PointCloudPacked',
            # '/depth_camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo',
            # '/depth_camera/image@sensor_msgs/msg/Image@gz.msgs.Image',

            # IMU
            '/imu@sensor_msgs/msg/Imu@gz.msgs.IMU',
        ],
        parameters=[{
            'qos_overrides./model/' + robot_ns + '.subscriber.reliability': 'reliable',
            'use_sim_time': use_sim_time,
        }],
        output='screen',
        remappings=[
            ('/model/' + robot_ns + '/cmd_vel', '/cmd_vel'),
            ('/model/' + robot_ns + '/odometry', '/odom'),
            ('/world/world_model/model/' + robot_ns + '/joint_state', 'joint_states'),
            ('/lidar', lidar_out_topic + '/scan'),
            ('/lidar/points', lidar_out_topic + '_ign'),
            ('/imu', imu_out_topic + '_ign'),
        ],
    )

    tf_broadcaster_odom = Node(
        package=package_name,
        executable='tf_broadcaster',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    pc2_to_xyzi = Node(
        package=package_name,
        executable='pc2_to_xyzi',
        output='screen',
        parameters=[{
            'lidar_topic_in_': lidar_out_topic + '_ign',
            'lidar_topic_out_': lidar_out_topic + '_pcl',
            'lidar_frame_id_': lidar_frame_id,
            'use_sim_time': use_sim_time,
        }],
    )

    lidar_imu_sync = Node(
        package=package_name,
        executable='lidar_imu_sync',
        output='screen',
        parameters=[{
            'lidar_topic_in_': lidar_out_topic + '_pcl',
            'imu_topic_in_': imu_out_topic + '_ign',
            'lidar_topic_out_': lidar_out_topic,
            'imu_topic_out_': imu_out_topic,
            'lidar_frame_id_': lidar_frame_id,
            'use_sim_time': use_sim_time,
        }],
    )

    return [
        gz_resource_path,
        open_rviz,
        open_ign,
        gz_spawn_entity,
        robot_state_publisher,
        bridge,
        tf_broadcaster_odom,
        pc2_to_xyzi,
        lidar_imu_sync,
    ]


def generate_launch_description():
    this_pkg_path = get_package_share_directory(package_name)

    simulation_params_file = DeclareLaunchArgument(
        'simulation_params_file',
        default_value=os.path.join(this_pkg_path, 'config', 'config.yaml'),
        description='Full path to the ROS 2 parameters file used by one_robot_ign_launch.py',
    )
    simu_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true',
    )

    return LaunchDescription([
        simulation_params_file,
        simu_time,
        OpaqueFunction(function=launch_setup),
    ])
