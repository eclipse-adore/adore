# Creating a New ADORe ROS Node

This guide will walk through creating a new node that is auto-linked to all 
ADORe user libraries and messages.

## Quick Start

1. **Copy the template node:**
```bash
cp -r ros2_workspace/src/example_nodes/ros2_hello_world ros2_workspace/src/my_new_node
```

2. **Update configuration files:**
   - Edit `package.xml` - update package name, description, and dependencies
   - Edit `CMakeLists.txt` - update project name and build targets
   - Modify source files and tests as needed

3. **Build the node:**
```bash
make build
```

4. **Run tests:**
```bash
make test
```

5. **Execute the node:**
```bash
make run
```

## Next Steps

- Check existing nodes in `ros2_workspace/src/` for implementation examples
