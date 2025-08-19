# ros2_syslog
The ros2_syslog node/program subscribes to  ROS2 messages of type `telemetry`
and writes them to the syslog.

The syslog is rate limited.  This is defined by a global variable 
`MAX_MESSAGES_PER_SECOND`

Syslog messages are automatically forward by rsyslog as telemetry if configured
by the host.


1. Build the package with:
```bash
bash build.sh
```
2. Run the node:
```bash
bash run.sh
```
