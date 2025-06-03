from launch_ros.actions import Node

def create_infrastructure_nodes(position: tuple[float, float],
                                 polygon: list[float],
                                 map_file: str) -> list[Node]:
    x, y = position

    return [
        Node(
            package='simulated_infrastructure',
            namespace='infrastructure',
            executable='simulated_infrastructure',
            name='simulated_infrastructure',
            parameters=[
                {"infrastructure_position_x": x},
                {"infrastructure_position_y": y},
                {"validity_polygon": polygon}
            ]
        ),
        Node(
            package='decision_maker_infrastructure',
            namespace='infrastructure',
            executable='decision_maker_infrastructure',
            name='decision_maker_infrastructure',
            parameters=[
                {"map file": map_file},
                {"infrastructure_position_x": x},
                {"infrastructure_position_y": y},
                {"debug_mode_active": False},
                {"validity_polygon": polygon},
                {"multi_agent_PID_settings_keys": ["preview_distance", "k_yaw", "k_distance"]
                },
                {"multi_agent_PID_settings_values": [4.5, 2.0, 1.0]
                }
            ]
        )
    ]
