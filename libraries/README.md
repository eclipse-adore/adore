# Target generation
This project contains cmake helper functions to auto-generate library and
executable targets

## Libraries


### Interface Library
To create an interface library make a directory in `lib/<library name>/include`
with the desired library name. The library directory must contain an `include` 
directory to generate an interface library.


### Static Library
Library targets will be auto-generated based off of directory structure.
Any subdirectory in `lib` is assumed to be a library if there is a `include`
and `src` directory that is not matched in the `.cmakeignore` file.

### Example library:
The following directory structure will result in target: `a` being defined as a
static library.
```
lib/a
├── include
│   └── a.h
└── src
    └──── a.cpp
```

- All include directories for all defined targets will be included into target `a`.
- All link libraries for all defined targets will be linked into target `a`.

### Output:
Once target a is defined and `make build` is invoked the resulting output will
be generated for target: `a`
```
build/lib
├── a
│   └── include
│       └── a.h
└── liba.a

```

- A `build/lib` directory will be generated with all artifacts for every library
target.

- A `build/share` directory will be generated so that cmake `find_package(<package name>)` can be invoked on the package.
```
build/share
└── ── a
    └── cmake
        ├── aConfig.cmake
        └── aTargets.cmake
```
Note: the `build/share` directory needs to be appended to the `CMAKE_PREFIX_PATH` in order for cmake `find_package` to 
work

## External packages

External cmake packages can be used. They should be included via a `requirements.cmake` file in the library
directory.

All `requirements.cmake` files are recursively added during target generation.

The example library `boost_hello` requires boost. Inside `lib/boost_hello/requirements.cmake`
`find_package(Boost REQUIRED)` is invoked.

The `requirements.system` captures any necessary Debian package management
system (APT) requirements that are needed for the library. In this example
it is `libboost1.74-all-dev`

### Example `boost_hello` static library
```
lib/boost_hello
├── include
│   └── boost_hello.h
├── requirements.cmake
├── requirements.system
└── src
    └── boost_hello.cpp
```

A static shared library called `boost_hello` will be generated that is dependent
on the external package `Boost` with the following output:

```
build/lib
├── boost_hello
│   └── include
│       └── boost_hello.h
└── libboost_hello.a
```
CMake share directory:
```
build/share
└── boost_hello
    └── cmake
        ├── boost_helloConfig.cmake
        └── boost_helloTargets.cmake
```

## Executable targets

Any `.cpp` file anywhere in `lib` directory tree that is not matched in the 
`.cmakeignore` and contains a `main` method/function will auto-generate an 
executable target.

- All include directories for all defined targets will be included into the executable target.
- All link libraries for all defined targets will be linked into the executable target.


### boost_hello_test_program example
Gives the following structure an executable target called
`boost_hello_test_program` which contains a `main` method will be generated:
```
lib/boost_hello
├── include
│   └── boost_hello.h
├── requirements.cmake
├── requirements.system
└── src
    ├── boost_hello.cpp
    └── boost_hello_test_program.cpp
```
The executable target, in this case `boost_hello_test_program` can be anywhere
in the directory tree for `lib`.

- All target include directories, such as for the library `boost_hello`, will be added to the target `boost_hello_test_program`
- All target link directories, such as for the library `boost_hello`, will be added to the target `boost_hello_test_program`

Once invoking `make build` an executable will be available in the `build/bin` directory with the same name as the executable target itself e.g, `boost_hello_test_program`. 


## `.cmakeignore` file
The `.cmakeignore` file provides a means to disable a target similar to the
.gitignore file. Any pattern matching a directory in `lib` that is in the
`.cmakeignore` will not auto-generate a target and will also not build.
Review the comments in `.cmakeignore` for more information.


