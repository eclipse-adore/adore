# ADORe Libraries

This project contains C++ support libraries for **ADORe**.  
For details on each library, see the corresponding README:  

- [adore_map](./lib/adore_map/README.md)  
- [adore_dynamics](./lib/adore_dynamics/README.md)  
- [adore_planning](./lib/adore_planning/README.md)  
- [adore_math](./lib/adore_math/README.md)  
- [adore_controllers](./lib/adore_controllers/README.md)

For a quick guide on creating a new library or using a library see the
[Library Creation Guide](library_creation_guide.md)

For a deeper technical guide on the library generation system see 
[CMake Library Auto-Generation](cmake_library_auto_generation.md)

## Building ADORe Libraries
Using the provide makefile invoke make build inside the ADORe CLI in the 
libraries directory:
```bash
make build
```

## Make help target
For more features see the make help target/recipe:
```bash
make help
```


