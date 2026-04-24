# ********************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
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

#!/usr/bin/env python3
import argparse
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

import rclpy
from rclpy.qos import QoSProfile
from rclpy.serialization import serialize_message
from ros2topic.api import get_topic_names_and_types, get_msg_class


@dataclass
class TopicStats:
    name: str
    type_str: str
    count: int = 0
    first_time: Optional[float] = None
    last_time: Optional[float] = None
    min_period: Optional[float] = None
    max_period: Optional[float] = None
    total_bytes: int = 0

    def update(self, now: float, msg) -> None:
        size_bytes = len(serialize_message(msg))
        self.total_bytes += size_bytes
        self.count += 1

        if self.first_time is None:
            # first message
            self.first_time = now
            self.last_time = now
            return

        period = now - self.last_time
        self.last_time = now

        if period < 0.0:
            # clock went backwards? ignore this sample
            return

        if self.min_period is None or period < self.min_period:
            self.min_period = period
        if self.max_period is None or period > self.max_period:
            self.max_period = period

    def measurement_duration(self) -> Optional[float]:
        if self.first_time is None or self.last_time is None:
            return None
        return max(self.last_time - self.first_time, 0.0)

    def hz(self) -> Optional[float]:
        # mimic typical hz tools: (N-1) intervals
        if self.count < 2 or self.measurement_duration() is None:
            return None
        duration = self.measurement_duration()
        if duration <= 0.0:
            return None
        return (self.count - 1) / duration

    def bandwidth_bytes_per_sec(self) -> Optional[float]:
        duration = self.measurement_duration()
        if duration is None or duration <= 0.0:
            return None
        return self.total_bytes / duration


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Monitor ROS 2 topic hz and bandwidth for all topics "
                    "using ros2topic API."
    )
    parser.add_argument(
        "-d", "--duration", type=float, default=5.0,
        help="Monitoring duration in seconds (default: 5.0)."
    )
    parser.add_argument(
        "--include-hidden", action="store_true",
        help="Include hidden topics (names starting with '_')."
    )
    parser.add_argument(
        "--min-count", type=int, default=1,
        help="Minimum number of messages required to report stats (default: 1)."
    )
    parser.add_argument(
        "--skip-internal", action="store_true",
        help="Skip /parameter_events, /rosout and other obvious internal topics."
    )
    return parser


INTERNAL_TOPIC_PREFIXES = (
    "/parameter_events",
    "/rosout",
)


def is_internal_topic(name: str) -> bool:
    return any(name.startswith(p) for p in INTERNAL_TOPIC_PREFIXES)


def monitor_topics(
    duration: float,
    include_hidden: bool = True,
    min_count: int = 1,
    skip_internal: bool = True,
) -> Dict[str, TopicStats]:
    rclpy.init(args=None)
    node = rclpy.create_node("ros2_topic_monitor")
    time.sleep(1.0)  # wait a moment for other nodes to start

    try:
        # Discover topics via ros2topic API
        topics_and_types = get_topic_names_and_types(
            node=node, include_hidden_topics=include_hidden
        )

        stats: Dict[str, TopicStats] = {}
        subscriptions = []

        qos = QoSProfile(depth=10)

        for topic_name, type_list in topics_and_types:
            if skip_internal and is_internal_topic(topic_name):
                continue

            if not type_list:
                continue
            type_str = type_list[0]

            msg_class = get_msg_class(
                node=node,
                topic=topic_name,
                blocking=False,
                include_hidden_topics=include_hidden,
            )
            if msg_class is None:
                node.get_logger().warn(
                    f"Could not determine type for topic '{topic_name}', skipping."
                )
                continue

            topic_stats = TopicStats(name=topic_name, type_str=type_str)
            stats[topic_name] = topic_stats

            def make_callback(ts: TopicStats):
                def _cb(msg):
                    now = time.monotonic()  # wall-clock for diagnostics
                    ts.update(now, msg)
                return _cb

            cb = make_callback(topic_stats)
            sub = node.create_subscription(
                msg_class, topic_name, cb, qos
            )
            subscriptions.append(sub)

        if not stats:
            node.get_logger().warn("No topics to monitor.")
            return stats

        start = time.monotonic()
        end_time = start + duration

        # Single spin loop, all subscriptions handled in the same node
        while rclpy.ok() and time.monotonic() < end_time:
            rclpy.spin_once(node, timeout_sec=0.1)

        return stats

    finally:
        node.destroy_node()
        rclpy.shutdown()


def format_table(stats: Dict[str, TopicStats], min_count: int) -> str:
    # Filter topics with too few messages
    rows = []
    for name, s in stats.items():
        if s.count < min_count:
            continue

        hz = s.hz()
        bw = s.bandwidth_bytes_per_sec()
        duration = s.measurement_duration()

        rows.append({
            "name": name,
            "type": s.type_str,
            "count": s.count,
            "hz": hz,
            "period_min": s.min_period,
            "period_max": s.max_period,
            "bw": bw,  # bytes/sec
            "duration": duration,
        })

    if not rows:
        return "No topics met the minimum message count.\n"

    # Compute total bandwidth (bytes/sec) over all reported topics
    total_bw_bps = sum(r["bw"] for r in rows if r["bw"] is not None)
    total_bw_kbps = total_bw_bps / 1024.0

    # Sort rows by bandwidth descending; None goes to the bottom
    rows_sorted = sorted(
        rows,
        key=lambda r: (0.0 if r["bw"] is None else r["bw"]),
        reverse=True,
    )

    # Column widths
    name_w = max(len("TOPIC"), max(len(r["name"]) for r in rows_sorted))
    type_w = max(len("TYPE"), max(len(r["type"]) for r in rows_sorted))

    header = (
        f"{'TOPIC'.ljust(name_w)}  "
        f"{'TYPE'.ljust(type_w)}  "
        f"{'COUNT':>7}  "
        f"{'HZ':>10}  "
        f"{'PERIOD[min,max] s':>23}  "
        f"{'BW [kB/s]':>10}  "
        f"{'DUR[s]':>8}"
    )
    sep = "-" * len(header)
    lines = [header, sep]

    for r in rows_sorted:
        hz_str = f"{r['hz']:.2f}" if r["hz"] is not None else "n/a"
        if r["period_min"] is not None and r["period_max"] is not None:
            per_str = f"{r['period_min']:.3f}, {r['period_max']:.3f}"
        else:
            per_str = "n/a"
        bw_kb = (r["bw"] / 1024.0) if r["bw"] is not None else None
        bw_str = f"{bw_kb:.1f}" if bw_kb is not None else "n/a"
        dur_str = f"{r['duration']:.2f}" if r["duration"] is not None else "n/a"

        line = (
            f"{r['name'].ljust(name_w)}  "
            f"{r['type'].ljust(type_w)}  "
            f"{r['count']:7d}  "
            f"{hz_str:>10}  "
            f"{per_str:>23}  "
            f"{bw_str:>10}  "
            f"{dur_str:>8}"
        )
        lines.append(line)

    lines.append(sep)
    lines.append(f"Total bandwidth (sum of topics): {total_bw_kbps:.1f} kB/s")

    return "\n".join(lines) + "\n"


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    stats = monitor_topics(
        duration=args.duration,
        include_hidden=args.include_hidden,
        min_count=args.min_count,
        skip_internal=args.skip_internal,
    )
    print(format_table(stats, min_count=args.min_count))


if __name__ == "__main__":
    main()
