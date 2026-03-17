# ./vendor 
The "vendor" directory of the ADORe project provides a normalized build interface
to all external libraries and tools that are available for use within ADORe CLI.
All "vendor" packages, libraries, or tools are provide as git submodules.
When build is invoked all "vendor" components generate a Debian APT .deb package 
in `./vendor/build`.

All vendor packages must provide a `Makefile` with a `make build` and 
`make clean` target. The build target must output a APT archive in 
./vendor/\<package\>/build`.

## Building 
The `Makefile` provides a standard interface that invokes/triggers a build on all 
"vendor" by invoking `make build`.
The artifacts will be output to: `./vendor/build`.

## Adding a new vendor package
1. create a subdirectory with the package name in the vendor directory:
```bash
cd vendor
mkdir mypackage
```

2. Create a Makefile with `clean` and `build` targets inside the `mypackage` directory:
```make
ROOT_DIR:=$(shell dirname "$(realpath $(firstword $(MAKEFILE_LIST)))")
OUTPUT_DIRECTORY=${ROOT_DIR}/output

.EXPORT_ALL_VARIABLES:
DOCKER_BUILDKIT?=1
DOCKER_CONFIG?=
ARCH?=$(shell uname -m)
DOCKER_PLATFORM?=linux/$(ARCH)
CROSS_COMPILE?=$(shell if [ "$(shell uname -m)" != "$(ARCH)" ]; then echo "true"; else echo "false"; fi)

.PHONY: build
build: ## Build "mypackage" 
    echo "todo"

.PHONY: clean
clean:  ## Clean "mypackage" build artifacts 
	rm -rf "${OUTPUT_DIRECTORY}"
```

3. If it is an external project add it as a submodule
```
cd vendor/mypackage
git submodule add git@github.com/mypackage.git
```

4. Update the vendor Makefile to invoke build and clean on `myproject` in the 
build target and clean target respectively.


## Tips
invoking `make build` on any vendor package should output a `.deb` APT archive.
This will be automatically installed by the ADORe CLI. For a complete C++ example
review the vendor package `OptiNLC`.
