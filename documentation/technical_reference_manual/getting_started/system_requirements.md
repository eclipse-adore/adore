# System Requirements
The following section details the recommended hardware/system configuration,
as well as the required software configuration, in order to build and run ADORe
and its components.

### Minimum System Configurations 

**CPU:** 

- **Recommended Development System:** x86-based system, such as Intel Core i7-9xxxK or better.
- The more cores you have, the more trajectory planners you can run in parallel.
- No dedicated graphics card is required as everything (except plotting) runs on the CPU.
- **Also Supported:** ARM64 architectures, including NVIDIA Jetson platforms and raspberry pi, are 
  supported for deployment and testing.  

  For more details, see [Multi-Architecture Support](../system_and_development/multiarch_support.md).

> **⚠️ WARNING: Building ADORe ROS nodes on systems with limited resources may cause crashes!**  
> By default, ADORe uses parallel builds, which can overwhelm low-resource systems.  
> To prevent this, either:  
> - Edit the `.colcon_workspace/colcon_defaults.yaml` file to disable parallel builds, **or**  
> - Run a single-core build with:  
>   ```bash
>   cd .colcon_workspace && colcon build --parallel-workers 1
>   ```

**RAM:** 

- Minimum: 8 GB for execution  
- Recommended: 16 GB+ for faster compilation

**HD Storage:**

- At least 1.5 GB to clone the repository  
- At least 10 GB to build all necessary Docker contexts

**Operating System:** 

- Any OS supporting recent Docker versions  
- Recommended: Ubuntu 20.04, 22.04, or 24.04

**Network:**

- A reliable network with high throughput and low latency.  
- The initial build can take significant time to pull dependencies from `apt` and Docker.  
- Poor connections can cause non-deterministic build failures.

### Software Requirements

- [Docker 🔗](https://www.docker.com/) v20.10.17 or greater and Docker Compose v2.6.0 or greater.  
  For a guide on installing docker, see [Installing Docker](installing_docker.md).
