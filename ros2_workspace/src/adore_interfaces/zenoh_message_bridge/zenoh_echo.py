import zenoh
import struct

def decode_string(payload: bytes) -> str:
    # CDR string: 4-byte header + 4-byte length + string bytes (null terminated)
    length = struct.unpack_from('<I', payload, 4)[0]
    return payload[8:8 + length - 1].decode('utf-8')

conf = zenoh.Config.from_json5('''
{
  mode: "client",
  connect: { endpoints: ["tcp/127.0.0.1:7447"] }
}
''')

with zenoh.open(conf) as session:
    with session.declare_subscriber("chatter") as sub:
        for sample in sub:
            print(f"[{sample.key_expr}] {decode_string(sample.payload.to_bytes())}")
