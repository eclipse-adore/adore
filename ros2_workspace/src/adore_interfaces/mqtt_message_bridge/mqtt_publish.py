import os
import time
import rclpy
import paho.mqtt.client as mqtt
from rclpy.serialization import serialize_message
from std_msgs.msg import String

rclpy.init()

host = os.environ.get("MQTT_BROKER_HOST", "127.0.0.1")
port = int(os.environ.get("MQTT_BROKER_PORT", 1883))

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(host, port)
client.loop_start()

msg = String()
while True:
    msg.data = "Hello, MQTT!"
    client.publish("mqtt/chatter", serialize_message(msg))
    print("Published: Hello, MQTT!")
    time.sleep(1)
