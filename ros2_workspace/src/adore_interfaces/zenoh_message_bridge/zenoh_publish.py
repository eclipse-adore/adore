import zenoh
import json
import time

conf = zenoh.Config.from_json5('''
{
  mode: "client",
  connect: { endpoints: ["tcp/127.0.0.1:7447"] }
}
''')

with zenoh.open(conf) as session:
    pub = session.declare_publisher("zenoh/chatter")
    while True:
        payload = json.dumps({"data": "Hello, Zenoh!"}).encode('utf-8')
        pub.put(payload)
        print("Published: Hello, Zenoh!")
        time.sleep(1)
