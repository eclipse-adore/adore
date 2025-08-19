# ./vendor 
The "vendor" directory of the ADORe project provides a normalized build interface
to all external libraries and tools that are available for use within ADORe CLI.
All "vendor" packages, libraries, or tools are provide as git submodules.
When build is invoked all "vendor" components generate a Debian APT .deb package 
in `./vendor/build`.


## Building 
The `Makefile` provides a standard interface that invokes/triggers a build on all 
"vendor" by invoking `make build`.
The artifacts will be output to: `./vendor/build`.
