"""Subscribe to a bridge key over zenoh and print what arrives.
"""
import argparse
import json
import struct
import zenoh

DEFAULT_ENDPOINT = 'tcp/127.0.0.1:7446'


def decode(payload: bytes, fmt: str) -> str:
    if fmt == 'raw':
        return repr(payload)
    if fmt == 'json':
        return json.dumps(json.loads(payload.decode('utf-8')))
    # CDR std_msgs/msg/String: 4 byte encapsulation header, 4 byte length
    # including the terminator, then the string.
    length = struct.unpack_from('<I', payload, 4)[0]
    if len(payload) != 8 + length:
        raise ValueError(f'not CDR: length field {length} does not match {len(payload)} bytes')
    return payload[8:8 + length - 1].decode('utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-k', '--key', default='test/json_out')
    parser.add_argument('-e', '--endpoint', default=DEFAULT_ENDPOINT)
    parser.add_argument('-f', '--format', choices=('json', 'cdr', 'raw'), default='json',
                        help="must match the mapping's format in the bridge config")
    args = parser.parse_args()

    conf = zenoh.Config.from_json5(json.dumps({
        'mode': 'client',
        'connect': {'endpoints': [args.endpoint]},
    }))

    print(f'Subscribed to {args.key} via {args.endpoint}, waiting for samples')
    with zenoh.open(conf) as session:
        with session.declare_subscriber(args.key) as sub:
            for sample in sub:
                data = sample.payload.to_bytes()
                try:
                    print(f'[{sample.key_expr}] {decode(data, args.format)}')
                except Exception as e:
                    print(f'[{sample.key_expr}] not decodable as {args.format}: {e}: {data!r}')


if __name__ == '__main__':
    main()
