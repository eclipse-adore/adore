docker run --rm -d \
  --name zenoh-router \
  -p 7446:7447/tcp \
  -p 7446:7446/udp \
  eclipse/zenoh:latest
