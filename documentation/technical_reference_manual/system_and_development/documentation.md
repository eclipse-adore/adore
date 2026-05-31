# Documentation
ADORe provides several sources of Documentation which will be detailed below.

## Landing page
The ADORe landing page is the main GitHub io information web page.
Location: [https://eclipse.github.io/adore/ 🔗](https://eclipse.github.io/adore/)

## mkdocs
ADORe uses mkdocs to compile markdown into a searchable document hub.

Location: [https://eclipse.github.io/adore/mkdocs/ 🔗](../)

## Doxygen
ADORe utilized Doxygen to auto generate in-source 

Location: [doxygen_documentation.md 🔗](doxygen_documentation.md)

## GNU Make
Every ADORe module provides a Makefile providing "documentation-as-code". To
learn what a module offers inspect the available make targets. Every ADORe
module also offers a `make help` target. Call 'make help' to learn what it
offers such as with the following example:
```bash
adore(develop:c0ec4a8) (0)> make help
Usage: make <target>                                           
  cli                                       Start ADORe CLI docker context or attach to it if it is already running
  run                                       Execute a command in the ADORe CLI context `make run cmd="<command to execute>"`
  stop                                      Stop ADORe CLI docker compose context if it is running
  build                                     Build and setup adore cli
  clean                                     Clean ADORe  build artifacts
  start                                     Start the ADORe CLI docker compose context
```

## Documentation Generation
For information on how to build the documentation please visit the
[Documentation Generation 🔗](documentation_generation_system.md)
guide.
