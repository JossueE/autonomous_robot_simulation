import os
from pathlib import Path

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

package_name = 'autonomous_robot_simulation'


def load_ros_parameters(config_path: str, node_name: str) -> dict:
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file) or {}

    node_config = config.get(node_name) or config.get('/**') or {}
    return node_config.get('ros__parameters', node_config)


def resolve_map_path(raw_path: str, default_pkg_path: str) -> str:
    expanded_path = Path(os.path.expandvars(os.path.expanduser(raw_path)))
    if raw_path.startswith('package://'):
        map_package_name, _, relative_path = raw_path.removeprefix('package://').partition('/')
        if not map_package_name or not relative_path:
            raise ValueError(f'Invalid package URI: {raw_path}')
        return str((Path(get_package_share_directory(map_package_name)) / relative_path).resolve())

    if expanded_path.is_absolute():
        return str(expanded_path)

    default_pkg = Path(default_pkg_path).resolve()
    workspace_root = default_pkg.parents[3]
    install_root = default_pkg.parents[2]

    candidates = [
        default_pkg / expanded_path,
        workspace_root / expanded_path,
        install_root / expanded_path,
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate.resolve())

    return str((default_pkg / expanded_path).resolve())


def launch_setup(context, *args, **kwargs):
    del args, kwargs

    this_pkg_path = get_package_share_directory(package_name)
    config_path = os.path.abspath(
        os.path.expandvars(
            os.path.expanduser(LaunchConfiguration('display_map_params_file').perform(context))
        )
    )
    params = load_ros_parameters(config_path, 'pcd_to_ros')
    map_file_path = resolve_map_path(
        params.get('map_file_path', 'package://fast_lio/PCD/test.pcd'),
        this_pkg_path,
    )

    open_rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', str(this_pkg_path + "/rviz/display_map.rviz")],
    )

    pcd_visualizer = Node(
        package=package_name,
        executable='pcd_visualizer',
        name='pcd_to_ros',
        output='screen',
        parameters=[config_path, {'map_file_path': map_file_path}],
    )

    return [
        open_rviz,
        pcd_visualizer,
    ]


def generate_launch_description():
    this_pkg_path = get_package_share_directory(package_name)

    display_map_params_file = DeclareLaunchArgument(
        'display_map_params_file',
        default_value=os.path.join(this_pkg_path, 'config', 'config.yaml'),
        description='Full path to the ROS 2 parameters file used by display_map_launch.py',
    )

    return LaunchDescription([
        display_map_params_file,
        OpaqueFunction(function=launch_setup),
    ])
