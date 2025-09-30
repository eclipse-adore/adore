# Problems and Solutions
This section will offer solutions to known issues.


### Do You Have Another Problem?
Have you encountered a problem that is not documented? Create an 
[issue 🔗](https://github.com/eclipse-adore/adore/issues). Chances are if you are 
having an issue someone else will encounter the same issue.  Help the community
and help us document the issues to improve ADORe. We are eager to help you!


## Problem: build fails with "ERROR exporting to image"

```
make build
...
=> CACHED [5/8] RUN python3 setup.py install
 => CACHED [6/8] RUN python3 setup.py --command-packages=stdeb.command bdist_deb
 => CACHED [7/8] RUN mkdir -p /build/ && mv deb_dist/*.deb /build/
 => CACHED [8/8] WORKDIR /output
 => ERROR exporting to image
 => => exporting layers
------
```
### Solution: Clean your docker build cache
Layer cache from docker can become stale resulting in `docker build .` failures.
To fix this clean your docker cache with the following command:
```
docker builder prune
docker buildx prune
```
For a more aggressive approach use:
```
docker system prune
```

## Problem: Docker build fails with various cache-related errors

```
E: Failed to fetch http://archive.ubuntu.com/ubuntu/pool/universe/v/vtk9/libvtk9.1t64_9.1.0%2breally9.1.0%2bdfsg2-7.1build3_amd64.deb  Hash Sum mismatch
   Hashes of expected file:
    - SHA256:d0d467007522b06616612af9f0757e0776c6b67ec2df7b4f8b6bebe54f7baa96
   Hashes of received file:
    - SHA256:7081ba7380da60924663ce8e80f6b2209d2d952f75a2fe971e62aac7cd28ecf9
```

Other symptoms include:
- DNS resolution failures during builds
- Random package download timeouts  
- Network connectivity errors
- Stale package lists causing dependency conflicts

### Solution: Clear Docker build cache systematically

Docker's BuildKit cache mounts can become stale when package repositories are updated between builds, WiFi networks change, or after system updates. Follow these steps in order:

**Step 1: Clear BuildKit cache (most effective)**
```bash
docker builder prune -a -f
docker buildx prune -a -f
```

**Step 2: If problem persists, restart Docker daemon**
```bash
sudo systemctl restart docker
```

## Problem: Docker build fails with registry DNS lookup timeouts

```
 => ERROR [ros2_service internal] load metadata for docker.io/library/ros:jazzy
------
 > [ros2_service internal] load metadata for docker.io/library/ros:jazzy:
------
failed to solve: ros:jazzy: failed to resolve source metadata for docker.io/library/ros:jazzy: failed to do request: Head "https://registry-1.docker.io/v2/lib
rary/ros/manifests/jazzy": dial tcp: lookup registry-1.docker.io on 10.136.106.175:53: read udp 172.17.0.2:39119->10.136.106.175:53: i/o timeout
make: *** [Makefile:29: build] Error 1
```

This typically occurs after:
- Switching WiFi networks
- Connecting/disconnecting from VPN
- Network interface changes
- System sleep/wake cycles
- Router/DNS server changes

Docker's internal networking can retain stale DNS configurations that prevent it from resolving external registry addresses.

### Solution: Restart Docker daemon to refresh network configuration

Docker daemon caches network configuration and DNS settings. When your network environment changes, Docker may still try to use outdated network routes and DNS servers.

```bash
sudo systemctl restart docker
```

## Problem: System crashes or freezes during ADORe build

When running `make build`, the build process may consume too many resources
on systems with limited CPU or memory. By default, ADORe uses parallel builds,
which can overwhelm low-resource systems and lead to crashes, freezes, or the
build being killed by the operating system.

### Solution: Use single-core builds

To prevent resource exhaustion, disable parallel builds. You can do this in two ways:

**Option 1: Modify `adore.env`**  
Set the build variable in the `adore.env` file to disable parallel builds.

**Option 2: Use provided make target**  
Run the single-core build target(inside the ADORe CLI):  
```bash
cd ros2_workspace && make build_single_core
```


## Problem: Build exits with undefined targets
Build fails with missing or undefined targets:
```
cd ros2_observer && make clean
make[2]: * No rule to make target 'clean'.  Stop.
make[1]: * [Makefile:42: clean] Error 2
make: *** [Makefile:72: clean] Error 2
```
The ADORe repositories uses git submodules, if they fail to clone or update 
this will cause other activities to fail.


### Solution:
Verify that the effected submodule directory is not empty.
The following is an example of an uninitialized submodule which will cause a build failure:
```
adore(feature/documentation_improvements:e1f1960) (130)> ls -la vendor/ros2_observer

total 12  
drwxrwxr-x 2   4096 Sep 4 10:48 .
drwxrwxr-x 12   4096 Sep 4 10:26 ..
-rw-rw-r-- 1   48 Jul 24 12:51 .git
```

- Try updating the submodules:
```
git submodule update --init --recursive
```

The submodule should be populated with files after initializing:
```
ls -lan vendor/ros2_observer'

total 76  
drwxrwxr-x 5   4096 Sep 4 10:51 .
drwxrwxr-x 12   4096 Sep 4 10:26 ..
-rw-rw-r-- 1   778 Sep 4 10:51 Dockerfile
-rw-rw-r-- 1   32 Sep 4 10:51 .dockerignore
-rw-rw-r-- 1   48 Jul 24 12:51 .git
-rw-rw-r-- 1   6 Sep 4 10:51 .gitignore
-rw-rw-r-- 1   11358 Sep 4 10:51 LICENSE
-rw-rw-r-- 1   644 Sep 4 10:51 Makefile
...
```
- Try re-cloning the ADORe repository:
```
cd ..
mv adore adore_partially_clonned
git clone git@github.com:eclipse-adore/adore.git
cd adore
git submodule update --init --recursive
make build
```

