from topic_test_base import *
import os
from topic_test_base import base_topic_test
from state_test_base import base_vehicle_state_test

test_file_dir = os.path.dirname(os.path.realpath(__file__))
launch_file = os.path.abspath(os.path.join(test_file_dir, "../simulation_scenarios/simulation_test.py"))

def test_simulation():
    required_topics = [
        "/ego_vehicle/vehicle_state/dynamic",
        "/ego_vehicle/local_map",
        "/ego_vehicle/trajectory_decision",
    ]
    base_topic_test(required_topics, launch_file)

def test_simulation_state():

    target_points = [
        (606454.0, 5797310.0)
    ] 

    base_vehicle_state_test(launch_file, target_points, 20, 2)
