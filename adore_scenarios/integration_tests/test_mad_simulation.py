from topic_test_base import *
import os
from topic_test_base import base_topic_test

test_file_dir = os.path.dirname(os.path.realpath(__file__))

def test_simulation_topics():
    required_topics = [
        "/ego_vehicle/vehicle_state/dynamic",
        "/ego_vehicle/local_map",
        "/ego_vehicle/route",
        "/ego_vehicle/trajectory_decision",
        "/ego_vehicle/traffic_participants",
        "/sim_vehicle_2/vehicle_state/dynamic",
        "/sim_vehicle_2/local_map",
        "/sim_vehicle_2/route",
        "/sim_vehicle_2/trajectory_decision"
    ]
    launch_file = os.path.abspath(os.path.join(test_file_dir, "../simulation_scenarios/saad_maad_test.py"))
    base_topic_test(required_topics, launch_file, 20)

