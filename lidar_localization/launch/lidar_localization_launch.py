import os
from pathlib import Path

import launch
import launch.actions
import launch.events
import launch_ros
import launch_ros.actions
import launch_ros.events
import lifecycle_msgs.msg
import yaml

from ament_index_python.packages import get_package_share_directory
from launch.substitutions import LaunchConfiguration

localization_package_name = 'lidar_localization'


def load_ros_parameters(config_path: str, node_name: str) -> dict:
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file) or {}

    node_config = config.get(node_name) or config.get('/**') or {}
    return node_config.get('ros__parameters', node_config)


def resolve_map_path(raw_path: str, default_pkg_path: str) -> str:
    expanded_path = Path(os.path.expandvars(os.path.expanduser(raw_path)))
    if raw_path.startswith('package://'):
        package_name, _, relative_path = raw_path.removeprefix('package://').partition('/')
        if not package_name or not relative_path:
            raise ValueError(f'Invalid package URI: {raw_path}')
        return str((Path(get_package_share_directory(package_name)) / relative_path).resolve())

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


def generate_launch_description():
    ld = launch.LaunchDescription()

    localization_pkg_path = get_package_share_directory(localization_package_name)
    config_path = os.path.join(localization_pkg_path, 'config', 'localization.yaml')
    localization_params = load_ros_parameters(config_path, 'lidar_localization')
    map_file_path = resolve_map_path(
        localization_params.get('map_path', 'package://fast_lio/PCD/test.pcd'),
        localization_pkg_path,
    )

    use_sim_time = LaunchConfiguration('use_sim_time')

    lidar_localization = launch_ros.actions.LifecycleNode(
        name='lidar_localization',
        namespace='',
        package=localization_package_name,
        executable='lidar_localization_node',
        parameters=[config_path, {'map_path': map_file_path}, {'use_sim_time': use_sim_time}],
        output='screen')

    to_inactive = launch.actions.EmitEvent(
        event=launch_ros.events.lifecycle.ChangeState(
            lifecycle_node_matcher=launch.events.matches_action(lidar_localization),
            transition_id=lifecycle_msgs.msg.Transition.TRANSITION_CONFIGURE,
        )
    )

    simu_time = launch.actions.DeclareLaunchArgument(
        'use_sim_time',
        default_value='True',
        description='Use simulation (Gazebo) clock if true')

    from_unconfigured_to_inactive = launch.actions.RegisterEventHandler(
        launch_ros.event_handlers.OnStateTransition(
            target_lifecycle_node=lidar_localization,
            goal_state='unconfigured',
            entities=[
                launch.actions.LogInfo(msg="-- Unconfigured --"),
                launch.actions.EmitEvent(event=launch_ros.events.lifecycle.ChangeState(
                    lifecycle_node_matcher=launch.events.matches_action(lidar_localization),
                    transition_id=lifecycle_msgs.msg.Transition.TRANSITION_CONFIGURE,
                )),
            ],
        )
    )

    from_inactive_to_active = launch.actions.RegisterEventHandler(
        launch_ros.event_handlers.OnStateTransition(
            target_lifecycle_node=lidar_localization,
            start_state='configuring',
            goal_state='inactive',
            entities=[
                launch.actions.LogInfo(msg="-- Inactive --"),
                launch.actions.EmitEvent(event=launch_ros.events.lifecycle.ChangeState(
                    lifecycle_node_matcher=launch.events.matches_action(lidar_localization),
                    transition_id=lifecycle_msgs.msg.Transition.TRANSITION_ACTIVATE,
                )),
            ],
        )
    )

    ld.add_action(simu_time)
    ld.add_action(from_unconfigured_to_inactive)
    ld.add_action(from_inactive_to_active)
    ld.add_action(lidar_localization)
    ld.add_action(to_inactive)

    return ld
