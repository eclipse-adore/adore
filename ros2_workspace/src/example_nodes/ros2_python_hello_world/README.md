# ROS2 Python Node Template

This is a ros2 hello world python template for creating ROS2 Python packages 
with proper executable entry points that work with `ros2 run`.

## Features

- **Dynamic package naming**: Package name is automatically detected from directory name
- **Automatic entry point handling**: CMake automatically copies setuptools executables to the correct location for `ros2 run`
- **Dynamic requirements**: Automatically reads dependencies from `requirements.pip3`
- **Proper ROS2 structure**: Includes resource files, package.xml, and proper CMake integration

## Template Structure

```
.
├── CMakeLists.txt              # Handles Python package and executable installation
├── Makefile                    # Convenience commands for build/run
├── package.xml                 # ROS2 package metadata
├── requirements.pip3           # Python dependencies (optional)
├── resource/
│   └── <package_name>          # ROS2 resource marker file
├── setup.py                    # Python package configuration with entry points
├── src/
│   └── <package_name>/
│       ├── __init__.py
│       ├── node1.py            # Your ROS2 nodes
│       ├── node2.py            # Add more nodes as needed
│       └── ...
└── test/
    ├── __init__.py
    ├── README.md
    └── test_dummy.py
```

## Creating a New Package from Template

### 1. Copy Template Directory
```bash
# Copy this template to your desired location
cp -r ros2_python_hello_world my_new_package
cd my_new_package
```

### 2. Update Package Name
Rename the resource file to match your new package name:
```bash
mv resource/ros2_python_hello_world resource/my_new_package
```

### 3. Update package.xml
Edit `package.xml` and update:
- `<name>my_new_package</name>`
- `<description>Your package description</description>`
- `<maintainer email="your@email.com">Your Name</maintainer>`
- Add any additional dependencies you need

### 4. Update Python Source Directory
```bash
mv src/ros2_python_hello_world src/my_new_package
```

### 5. Create Your Node(s)
Replace the example nodes with your own:

**src/my_new_package/my_node.py**:
```python
import rclpy
from rclpy.node import Node

class MyNode(Node):
    def __init__(self):
        super().__init__('my_node')
        self.get_logger().info('My node started')
        # Add your node logic here

def main(args=None):
    rclpy.init(args=args)
    node = MyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### 6. Update Entry Points in setup.py
The setup.py automatically detects your package name, but you need to update the entry points for your nodes:

```python
entry_points={
    'console_scripts': [
        f'{package_name} = {package_name}.my_node:main',
        f'{package_name}_other = {package_name}.other_node:main',
        # Add more entry points as needed
    ],
},
```

### 7. Update Dependencies (Optional)
If you need Python dependencies, add them to `requirements.pip3`:
```
numpy>=1.20.0
opencv-python>=4.5.0
# Add your dependencies here
```

### 8. Update Makefile Variables (Optional)
Edit the Makefile to set your package name if it differs from the directory name:
```makefile
ROS2_PACKAGE := my_new_package
```

## Building and Running

### Build the Package
```bash
make build
# or
colcon build --packages-select my_new_package
```

### Run Your Node
```bash
make run
# or
ros2 run my_new_package my_new_package
```

### Run tests 
```bash
make test
# or
colcon test --packages-select my_new_package --event-handlers console_direct+
```

### List Available Executables
```bash
ros2 pkg executables my_new_package
```

## Key Points

1. **Package name detection**: The package name is automatically detected from the directory name, so make sure your directory name matches your desired package name.

2. **Entry points**: Each Python node that you want to run with `ros2 run` must:
   - Have a `main()` function
   - Be listed in the `entry_points` section of `setup.py`

3. **Resource files**: The resource file name must match your package name exactly.

4. **Automatic copying**: The CMakeLists.txt automatically copies all executables from `bin/` to `lib/package_name/` where ROS2 expects them.

## Troubleshooting

- **"No executable found"**: Check that your entry points in `setup.py` match your actual Python module names and main functions.
- **Import errors**: Make sure all your Python dependencies are listed in `requirements.pip3` or `package.xml`.
- **Package not found**: Ensure you've sourced your ROS2 workspace: `source install/setup.bash`

## Example Usage

See the included `hello_world_node.py` and `adore_hello_world_node.py` for examples of basic ROS2 Python nodes.
