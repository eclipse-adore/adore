docker run --rm -d \
  --name mosquitto-broker \
  -p 1883:1883 \
  -p 9001:9001 \
  eclipse-mosquitto:latest
