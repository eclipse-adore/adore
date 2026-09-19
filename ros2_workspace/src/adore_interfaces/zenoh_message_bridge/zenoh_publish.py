"""Publish a std_msgs/msg/String to the bridge over zenoh."""
import argparse
import json
import struct
import time
import zenoh

DEFAULT_ENDPOINT = 'tcp/127.0.0.1:7446'


def encode(text: str, fmt: str) -> bytes:
    if fmt == 'json':
        return json.dumps({'data': text}).encode('utf-8')
    # CDR std_msgs/msg/String: encapsulation header, length including the
    # terminator, then the null terminated string.
    body = text.encode('utf-8')
    return b'\x00\x01\x00\x00' + struct.pack('<I', len(body) + 1) + body + b'\x00'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-k', '--key', default='test/json_in')
    parser.add_argument('-e', '--endpoint', default=DEFAULT_ENDPOINT)
    parser.add_argument('-f', '--format', choices=('json', 'cdr'), default='json',
                        help="must match the mapping's format in the bridge config")
    parser.add_argument('-m', '--message', default='Hello, Zenoh!')
    parser.add_argument('-n', '--count', type=int, default=0,
                        help='number of samples, 0 publishes until interrupted')
    parser.add_argument('-i', '--interval', type=float, default=1.0)
    args = parser.parse_args()

    conf = zenoh.Config.from_json5(json.dumps({
        'mode': 'client',
        'connect': {'endpoints': [args.endpoint]},
    }))

    payload = encode(args.message, args.format)
    with zenoh.open(conf) as session:
        pub = session.declare_publisher(args.key)
        sent = 0
        while args.count == 0 or sent < args.count:
            pub.put(payload)
            sent += 1
            print(f'[{args.key}] {args.format}: {args.message}')
            if args.count == 0 or sent < args.count:
                time.sleep(args.interval)


if __name__ == '__main__':
    main()
