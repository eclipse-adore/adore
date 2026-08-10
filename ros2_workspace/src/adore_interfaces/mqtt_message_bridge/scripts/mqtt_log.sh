#!/usr/bin/env bash
# Subscribes to one or more topics and appends each message to a JSON Lines file.
# Connection settings come from bridge_config.yaml (same as the bridge).
#
# Usage: ./mqtt_log.sh [/path/to/bridge_config.yaml] [-o OUTFILE] [topic ...]
#
# Examples:
#   ./mqtt_log.sh                                   # all topics -> mqtt_log_<ts>.jsonl
#   ./mqtt_log.sh -o solbox.jsonl 'od_imoger/solbox/+/notifications'
#   ./mqtt_log.sh bridge_config.yaml -o run.jsonl 'od_imoger/#'

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

_config=""
if [[ "${1:-}" == *.yaml || "${1:-}" == *.yml ]]; then
    _config="$1"
    shift
fi

OUTFILE="mqtt_log_$(date '+%Y%m%d_%H%M%S').jsonl"
if [[ "${1:-}" == "-o" ]]; then
    OUTFILE="$2"
    shift 2
fi

source "$SCRIPT_DIR/mqtt_common.sh" "$_config"

TOPICS=("$@")
if [[ ${#TOPICS[@]} -eq 0 ]]; then
    TOPICS=('#')
fi

_topic_args=()
for t in "${TOPICS[@]}"; do
    _topic_args+=(-t "$t")
done

echo "=== MQTT Logger ==="
echo "Broker : $MQTT_HOST:$MQTT_PORT"
echo "Topics : ${TOPICS[*]}"
echo "Output : $OUTFILE"
echo "Press Ctrl+C to stop."
echo ""

# -F %j: topic-then-payload separated by a tab, payload raw, one line per message.
mosquitto_sub "${_broker_args[@]}" "${_topic_args[@]}" -F '%t	%p' \
  | python3 "$SCRIPT_DIR/mqtt_log_writer.py" "$OUTFILE"
