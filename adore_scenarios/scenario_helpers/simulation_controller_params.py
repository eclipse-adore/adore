# ********************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# https://www.eclipse.org/legal/epl-2.0
#
# SPDX-License-Identifier: EPL-2.0
# ********************************************************************************

# simulation_pid_params = {
#     "k_long": 1.0,
#     "k_v": 1.0,
#     "k_feed_forward_ax": 1.0,
#     "dt": 0.1,
#     "acc_smoothing": 0.95,
#     "min_lookahead": 0.1,
#     "max_lookahead": 1.0,
#     "base_lookahead": 0.5,
#     "lookahead_gain": 0.1,
#     "slow_steer_smoothing": 4.0
# }

simulation_pid_params = {
 "kp_x": 0.1,
 "ki_x": 0.0,
 "velocity_weight": 0.4,
 "kp_y": 0.2,
 "ki_y": 0.0,
 "heading_weight": 0.5,
 "kp_omega": 0.0,
 "dt": 0.05,
 "steering_comfort": 100000.25,
 "acceleration_comfort": 400.0,
 "acceleration_threshold": 0.25,
 "velocity_threshold": 0.25,
 "constant_brake": -1.0,
 "lookahead_time": 0.0
 }