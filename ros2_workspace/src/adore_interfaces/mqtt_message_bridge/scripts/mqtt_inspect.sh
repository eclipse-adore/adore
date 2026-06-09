#!/usr/bin/env bash
# Subscribes to one or more topics and pretty-prints incoming messages with timestamps.
# Defaults to '#' (all topics) if no topic filter is given.
#
# Usage: ./mqtt_inspect.sh [/path/to/mqtt.env] [topic1] [topic2] ...
#
# Examples:
#   ./mqtt_inspect.sh                              # all topics
#   ./mqtt_inspect.sh mqtt.env ros2/#              # all ROS2 bridge topics
#   ./mqtt_inspect.sh mqtt.env ros2/# mqtt/#       # two filters

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/mqtt_common.sh" "${1:-}"
shift || true  # drop the env file arg (or nothing) so remaining args are topics

TOPICS=("${@}")
if [[ ${#TOPICS[@]} -eq 0 ]]; then
    TOPICS=('#')
fi

_topic_args=()
for t in "${TOPICS[@]}"; do
    _topic_args+=(-t "$t")
done

echo "=== MQTT Inspector ==="
echo "Broker : $MQTT_HOST:$MQTT_PORT"
echo "Topics : ${TOPICS[*]}"
echo "Press Ctrl+C to stop."
echo ""

mosquitto_sub "${_broker_args[@]}" \
    "${_topic_args[@]}" \
    -v \
  | while IFS= read -r line; do
        echo "[$(date '+%H:%M:%S.%3N')] $line"
    done
