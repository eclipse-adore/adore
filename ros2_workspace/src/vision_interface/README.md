# vision_interface
A node for converting messages from camera detection into usable objects for ADORe

For initial demo this just subscribes to a DetectionArray2D message on a topic settable from launch file and ouputs a red light signal at a point given from launch file.

In the future this should expand to correctly localize and assign objects in 3d space and even fuse with map data.
