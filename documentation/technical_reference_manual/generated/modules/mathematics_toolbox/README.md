# Mathmatics Toolbox 
This project contains docker contexts and project example programs for several 
C++ mathematics libraries making it easier to build and consume or use the
libraries.

This project uses docker as a rudimentary "package" for each library allowing 
a given package, for example eigen3, to be included, installed, and consumed in 
another docker context.

The build context is licensed under the EPL-2.0. Review the other submodules for their respective licenses 

## Getting Started
Docker and Make are required

### Background
This project contains docker build environments and example run environments
for several math libraries including: 
[Eigen(eigen3)🔗](https://eigen.tuxfamily.org/), [osqp 🔗](https://osqp.org/) 
this project includes examples on how to compile the previously mentioned 
libraries, run, include (via cmake), and install the libraries.


### Caching
By default all dependencies are fetch via docker hub

### build
** The default behavior of the build target/recipe will not compile any dependencies **
A build target is provided that will build every library provided in this 
project. The build target does the following:
1. Fetches all projects from docker hub (if it exists) or from local cache 
(if it exists)
2. builds the docker context for example builds eigne3:latest only if it does
   exist after step 1 
3. Saves the docker layers and image to a local cache in ./.docker_cache

To explicitly build a given project for example eigen3 you must explicitly call
the provided `make build_<project name>` target for example:
```bash
make build_eigen3
```
or 
```
make clean_build
```
to build all dependencies


### osqp
In order to use the osqp library you must first build the docker context
with `make build` or `make build_osqp`. After you build the osqp docker
context a docker image will become available in your local docker repository:
```
mathmatics_toolbox(master) ✗ (0)> docker image ls | grep osqp
osqp                          latest          338a7cc85702   About a minute ago   13.1MB
```
Once available in your docker local repository it can be included in other
projects using the `FROM` key word in a docker file. The osqp context must
be defined in your docker file before your main image declaration such as
follows:
```Dockerfile
FROM osqp:latest as osqp 
...
FROM ubuntu:22.04
```
After including the osqp image in your docker file you can install the pre-built
library to the system libraries within your docker context such as the
following:
```Dockerfile
COPY --from=osqp /tmp/osqp /tmp/osqp 
WORKDIR /tmp/osqp/build
RUN make install/fast
```
Once installed in the system context within your docker context you can use
CMake find_package in your `CMakeLists.txt` to source osqp such as follows:
```cmake
find_package(osqp REQUIRED)
```
In order to compile a target with osqp you must also enable the `fpermissive`
flag by adding the following to your `CMakeLists.txt`:
```cmake
target_compile_options(<TARGET NAME> PRIVATE -fpermissive)
```
Finally, you must add the osqp to the target linked libraries in your
`CMakeLists.txt` such as follows:

```cmake
target_link_libraries(<TARGET NAME> PRIVATE osqp::osqp)
```

You should now be able to include osqp in your C++ project with:
```C++
#include "osqp.h"
...
```

This project also includes a complete example test program for osqp of 
everything previously explained in `test/osqp_hello_world`. To run the osqp test
program use the provided target:
```bash
cd tests
make test_osqp
```


### eigen
As with the osqp library you must first build the eigen library with: 
`make build` or `make build_eigen3`
After building eigen3 add it to your Dockerfile:
```Dockerfile
FROM eigen3:latest as eigen3 
...
FROM ubuntu:22.04
```
Next, install it to the system libraries within your docker context:
```Dockerfile
COPY --from=eigen3 /tmp/eigen3 /tmp/eigen3 
WORKDIR /tmp/eigen3/build
RUN make install
```
Next, use `find_package` in your `CMakeLists.txt`:
```cmake
find_package(Eigen3 REQUIRED)
```
and add the target link libraries for eigen:
```cmake
target_link_libraries(<TARGET NAME> PRIVATE Eigen3::Eigen)
```
Finally, you can include eigen in your C++ sources:
```C++
#include <Eigen/Dense>
...
```
There is a complete example test program provided in the prioject for eigen at:
`tests/eigen3_hello_world`; refer to this.

### Publishing to docker
To build and publish a library to docker hub
1. login with docker: `docker login`
2. build all libraries manually by invoking `make build_<library name>`
3. call the provided publish target: `make publish`
