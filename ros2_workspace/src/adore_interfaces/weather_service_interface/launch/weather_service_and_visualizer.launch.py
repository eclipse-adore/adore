from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os
import yaml


def _use_xterm(config_path: str) -> bool:
    try:
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        return bool(cfg.get('visualizer', {}).get('use_xterm', False))
    except Exception:
        return False


def _xterm_available() -> bool:
    import shutil
    return shutil.which('xterm') is not None


def generate_launch_description():
    default_config = os.path.join(
        get_package_share_directory('weather_service_interface'),
        'config', 'weather_service_config.yaml',
    )

    config_path = LaunchConfiguration('config_path')

    # Resolve the config at launch-description-generation time so we can read
    # the visualizer.use_xterm flag. LaunchConfiguration values are not yet
    # substituted here, so we read the default directly; if the caller passes
    # config_path on the command line we honour that too via the env-var path.
    resolved_config = os.environ.get('WEATHER_CONFIG_PATH', default_config)

    use_xterm = _use_xterm(resolved_config) and _xterm_available()
    visualizer_prefix = 'xterm -e' if use_xterm else ''

    return LaunchDescription([
        DeclareLaunchArgument('config_path', default_value=default_config),

        Node(
            package='weather_service_interface',
            executable='weather_service_node',
            name='weather_service_node',
            parameters=[{'config_path': config_path}],
            output='screen',
        ),

        # The visualizer owns a TTY for curses. When use_xterm is enabled it
        # runs in its own xterm window; otherwise it takes the current terminal.
        Node(
            package='weather_service_interface',
            executable='weather_visualizer_node',
            name='weather_visualizer_node',
            parameters=[{'config_path': config_path}],
            prefix=visualizer_prefix,
            output='screen',
        ),
    ])
