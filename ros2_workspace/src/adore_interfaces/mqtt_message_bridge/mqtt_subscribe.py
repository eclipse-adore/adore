import os
import rclpy
import paho.mqtt.client as mqtt
from rclpy.serialization import deserialize_message
from std_msgs.msg import String

rclpy.init()

host = os.environ.get("MQTT_BROKER_HOST", "127.0.0.1")
port = int(os.environ.get("MQTT_BROKER_PORT", 1883))

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        client.subscribe("mqtt/chatter")

def on_message(client, userdata, message):
    msg = deserialize_message(message.payload, String)
    print(f"[{message.topic}] {msg.data}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(host, port)
client.loop_forever()
