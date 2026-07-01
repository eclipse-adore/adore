#!/usr/bin/env python3
import json
import sys
from datetime import datetime, timezone


def main():
    out_path = sys.argv[1]
    with open(out_path, 'a', buffering=1) as out:
        for line in sys.stdin:
            line = line.rstrip('\n')
            if not line:
                continue
            topic, _, payload = line.partition('\t')
            try:
                payload_val = json.loads(payload)
            except (ValueError, TypeError):
                payload_val = payload
            record = {
                'ts': datetime.now(timezone.utc).isoformat(),
                'topic': topic,
                'payload': payload_val,
            }
            out.write(json.dumps(record, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    try:
        main()
    except (BrokenPipeError, KeyboardInterrupt):
        pass
