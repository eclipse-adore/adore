# ros_image_streamer

Two ROS 2 nodes for capturing and displaying video streams. The streaming node publishes `sensor_msgs/Image` from a local V4L2 device or an FFmpeg source. The viewer node subscribes to the topic and displays it in an OpenCV window.

## Dependencies

```bash
# System
```
sudo apt install $(cat requirements.system | tr '\n' ' ')
```

# Python (into your venv or system Python used by ROS)
```
pip install -r requirements.pip3
```

## Configuration

Edit `config/streamer_config.yaml` before building.

**Local device:**
```yaml
source_type: device
device:
  path: /dev/video0
  width: 1280
  height: 720
  fps: 30
```

**FFmpeg socket (e.g. TCP MPEG-TS from ffmpeg):**
```yaml
source_type: ffmpeg
ffmpeg:
  url: "tcp://127.0.0.1:12345"
```

Example sender:
```bash
ffmpeg -f v4l2 -framerate 30 -video_size 640x480 -i /dev/video0 \
  -vcodec libx264 -preset ultrafast -tune zerolatency \
  -f mpegts "tcp://127.0.0.1:12345?listen"
```

## Build

```bash
colcon build --packages-select ros_image_streamer
source install/setup.bash
```

## Usage

```bash
# Streamer and viewer together
./start_streamer_and_viewer.sh

# Separately
./start_streamer.sh
./start_viewer.sh

# Override config or topic
./start_streamer.sh /path/to/config.yaml
./start_viewer.sh /camera/image_raw "My Window"
```

Press `q` or `Esc` to close the viewer. `Ctrl+C` terminates any of the above.
