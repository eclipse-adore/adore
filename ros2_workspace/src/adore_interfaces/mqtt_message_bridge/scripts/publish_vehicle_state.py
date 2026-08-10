#!/usr/bin/env python3
"""Take one message off /ego_vehicle/vehicle_state_dynamic and republish it as a
Supervision Gateway VehicleTelemetryUpdate.

    python3 scripts/publish_vehicle_state.py
"""
import json
import math
import os
import re
import time

import rclpy
from adore_ros2_msgs.msg import TrafficParticipantSet, VehicleStateDynamic
from rclpy.qos import QoSProfile, DurabilityPolicy, HistoryPolicy, ReliabilityPolicy
from std_msgs.msg import String

STATE_TOPIC = '/ego_vehicle/vehicle_state_dynamic'
PARTICIPANT_TOPIC = '/ego_vehicle/traffic_participants'
TELEMETRY_TOPIC = '/supervision/telemetry'
TIMEOUT = 10.0

VEHICLE_ID = 'MV-001'
UTM_ZONE = 32
UTM_NORTHERN = True

# No source in VehicleStateDynamic.
STATE = 'NOMINAL_DRIVING'
BATTERY = 100.0
PASSENGERS = 0

_A_AXIS = 6378137.0
_F = 1.0 / 298.257223563
_K0 = 0.9996
_FALSE_EASTING = 500000.0
_FALSE_NORTHING = 10000000.0

_n = _F / (2.0 - _F)
_A = (_A_AXIS / (1.0 + _n)) * (1 + _n**2 / 4 + _n**4 / 64 + _n**6 / 256)

_BETA = (
    _n / 2 - 2 * _n**2 / 3 + 37 * _n**3 / 96 - _n**4 / 360 - 81 * _n**5 / 512 + 96199 * _n**6 / 604800,
    _n**2 / 48 + _n**3 / 15 - 437 * _n**4 / 1440 + 46 * _n**5 / 105 - 1118711 * _n**6 / 3870720,
    17 * _n**3 / 480 - 37 * _n**4 / 840 - 209 * _n**5 / 4480 + 5569 * _n**6 / 90720,
    4397 * _n**4 / 161280 - 11 * _n**5 / 504 - 830251 * _n**6 / 7257600,
    4583 * _n**5 / 161280 - 108847 * _n**6 / 3991680,
    20648693 * _n**6 / 638668800,
)
_DELTA = (
    2 * _n - 2 * _n**2 / 3 - 2 * _n**3 + 116 * _n**4 / 45 + 26 * _n**5 / 45 - 2854 * _n**6 / 675,
    7 * _n**2 / 3 - 8 * _n**3 / 5 - 227 * _n**4 / 45 + 2704 * _n**5 / 315 + 2323 * _n**6 / 945,
    56 * _n**3 / 15 - 136 * _n**4 / 35 - 1262 * _n**5 / 105 + 73814 * _n**6 / 2835,
    4279 * _n**4 / 630 - 332 * _n**5 / 35 - 399572 * _n**6 / 14175,
    4174 * _n**5 / 315 - 144838 * _n**6 / 6237,
    601676 * _n**6 / 22275,
)


def utm_to_latlon(easting, northing, zone, northern):
    """Inverse transverse Mercator, Krueger series. Avoids a PROJ data dependency."""
    xi = (northing if northern else northing - _FALSE_NORTHING) / (_K0 * _A)
    eta = (easting - _FALSE_EASTING) / (_K0 * _A)

    xi_p = xi - sum(b * math.sin(2 * j * xi) * math.cosh(2 * j * eta)
                    for j, b in enumerate(_BETA, 1))
    eta_p = eta - sum(b * math.cos(2 * j * xi) * math.sinh(2 * j * eta)
                      for j, b in enumerate(_BETA, 1))

    chi = math.asin(math.sin(xi_p) / math.cosh(eta_p))
    phi = chi + sum(d * math.sin(2 * j * chi) for j, d in enumerate(_DELTA, 1))
    lam = math.radians(zone * 6 - 183) + math.atan2(math.sinh(eta_p), math.cos(xi_p))

    return math.degrees(phi), (math.degrees(lam) + 180.0) % 360.0 - 180.0


def utm_frame(frame_id):
    """'UTM32U' -> (32, True). Falls back to the configured zone if unrecognised."""
    m = re.match(r'^UTM(\d{1,2})([C-HJ-NP-X])?$', frame_id or '', re.IGNORECASE)
    if not m:
        return UTM_ZONE, UTM_NORTHERN
    return int(m.group(1)), (m.group(2) or 'N').upper() >= 'N'


def speed(state):
    return math.hypot(state.vx, state.vy)


def participant_to_obstacle(participant, ego):
    motion = participant.motion_state
    body = participant.physical_parameters
    dx, dy = motion.x - ego.x, motion.y - ego.y
    c, s = math.cos(-ego.yaw_angle), math.sin(-ego.yaw_angle)
    return {
        'position': {'x': c * dx - s * dy, 'y': s * dx + c * dy},
        'heading': motion.yaw_angle,
        'dimensions': {
            'height': body.body_height,
            'width': body.body_width,
            'length': body.body_length,
        },
        'velocity': speed(motion),
    }


def build_telemetry(ego, participants):
    zone, northern = utm_frame(ego.header.frame_id)
    lat, lon = utm_to_latlon(ego.x, ego.y, zone, northern)

    return {
        'telemetry': {
            'vehicleId': VEHICLE_ID,
            'telemetry': {
                'state': STATE,
                'position': {'lat': lat, 'lon': lon},
                'heading': ego.yaw_angle,
                'velocity': speed(ego),
                'battery': BATTERY,
                'obstacles': [participant_to_obstacle(d.participant_data, ego)
                              for d in participants],
                'acceleration': ego.ax,
                'passengers': PASSENGERS,
            },
            'isConnected': True,
        }
    }


def _no_message_reason(node):
    infos = node.get_publishers_info_by_topic(STATE_TOPIC)
    if not infos:
        rmw = os.environ.get('RMW_IMPLEMENTATION', 'rmw_fastrtps_cpp (default)')
        return (f'nothing is publishing {STATE_TOPIC}. Check the topic name, and that '
                f'the publisher uses the same middleware (RMW_IMPLEMENTATION={rmw}).')
    expected = 'adore_ros2_msgs/msg/VehicleStateDynamic'
    wrong = [i.topic_type for i in infos if i.topic_type != expected]
    if wrong:
        return (f'{STATE_TOPIC} carries {wrong[0]}, not {expected}. '
                f'A subscription with the wrong type never matches.')
    endpoints = ', '.join(
        f'{i.node_name} [{i.qos_profile.reliability.name}/{i.qos_profile.durability.name}]'
        for i in infos
    )
    return f'{len(infos)} publisher(s) on {STATE_TOPIC} but nothing arrived in {TIMEOUT:g}s: {endpoints}'


def _sub_qos():
    """Best effort + volatile so the subscription matches any publisher QoS."""
    return QoSProfile(
        depth=1,
        history=HistoryPolicy.KEEP_LAST,
        reliability=ReliabilityPolicy.BEST_EFFORT,
        durability=DurabilityPolicy.VOLATILE,
    )


def _pub_qos():
    """Reliable so the bridge's best-effort subscription still matches, but the
    single message is not dropped on the way out."""
    return QoSProfile(
        depth=1,
        history=HistoryPolicy.KEEP_LAST,
        reliability=ReliabilityPolicy.RELIABLE,
        durability=DurabilityPolicy.VOLATILE,
    )


def capture_and_publish(node):
    ego, participants = [], []
    node.create_subscription(VehicleStateDynamic, STATE_TOPIC, ego.append, _sub_qos())
    node.create_subscription(TrafficParticipantSet, PARTICIPANT_TOPIC,
                             lambda m: participants.append(m.data), _sub_qos())
    pub = node.create_publisher(String, TELEMETRY_TOPIC, _pub_qos())

    deadline = time.monotonic() + TIMEOUT
    while not ego and time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
    if not ego:
        raise SystemExit(_no_message_reason(node))
    rclpy.spin_once(node, timeout_sec=0.5)

    payload = json.dumps(build_telemetry(ego[0], participants[-1] if participants else []))

    deadline = time.monotonic() + 5.0
    while node.count_subscribers(TELEMETRY_TOPIC) == 0 and time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
    if node.count_subscribers(TELEMETRY_TOPIC) == 0:
        raise SystemExit(f'no subscriber on {TELEMETRY_TOPIC}; is the bridge running?')

    pub.publish(String(data=payload))
    for _ in range(5):
        rclpy.spin_once(node, timeout_sec=0.1)
    return payload


def main():
    rclpy.init()
    node = rclpy.create_node('publish_vehicle_state')
    try:
        payload = capture_and_publish(node)
    except KeyboardInterrupt:
        raise SystemExit('interrupted')
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

    print(f'published {len(payload)} bytes to {TELEMETRY_TOPIC}')


if __name__ == '__main__':
    main()
