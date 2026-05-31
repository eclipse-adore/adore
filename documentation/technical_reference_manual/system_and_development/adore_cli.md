<!--
********************************************************************************
* Copyright (C) 2017-2020 German Aerospace Center (DLR). 
* Eclipse ADORe, Automated Driving Open Research https://eclipse.org/adore
*
* This program and the accompanying materials are made available under the 
* terms of the Eclipse Public License 2.0 which is available at
* http://www.eclipse.org/legal/epl-2.0.
*
* SPDX-License-Identifier: EPL-2.0 
*
* Contributors: 
********************************************************************************
-->
## ADORe command line interface (CLI)

The ADORe CLI is a docker run-time context that provides a complete development
and deployment environment for ADORe. For more information on this tool
please visit https://github.com/eclipse-adore/adore_cli

The ADORe CLI context provides the following features: 
* Execution environment for all ADORe related program, nodes, binaries 
* Pre-installed ROS 2 development tools
* Pre-installed system tools such as net-tools (ping), traceroute, nmap, gdb, ZSH etc 
* Pre-installed system dependencies for all ADORe ROS nodes and programs
* Linked filesystem via Docker Volumes to the ADORe repository
* REST API for interaction with ADORe and ROS
* some basic development and debugging tools

### ADORe CLI Usage
Change directory to the root of the ADORe project and run:
```
make cli
```
On first run of the ADORe CLI the system will be built including all core
modules. Initial build can take 10-15 minutes depending on system and network. 

Once the ADORe CLI context builds and starts you will be presented with a 
zsh shell context:
```text
Welcome to the ADORe Development CLI Ubuntu 20.04.6 LTS (GNU/Linux 5.19.0-45-generic x86_64)

            ____ 
         __/  |_\__
        |           -. 
  ......'-(_)---(_)--' 

  Type 'help' for more information.

ADORe CLI: adore git:(main)  (0)>  
```
This will build all necessary ADORe components and launch a docker context.

#### How do I know if I am in the ADORe CLI context?
I am developing a ROS node and I want to add a system dependency. How do I do this?
In the same directory adjacent or next to your `package.xml` file create a file
called `requirements.system`. This file will be picked up by the ADORe CLI
when it is built with:
```
make build
```

Example `requirements.system` file:
```bash
curl
wget
htop
```

#### How do I know if I am in the ADORe CLI context?

- If you are in the ADORe CLI context you should have a shell prompt similar to
  the following: `ADORe CLI: adore git:(master)  (0)>`

#### Persistence
When running the ADORe CLI the adore source directory is mounted as a volume.
It will be mounted with the same path as the parent context. Any changes made 
in the adore source tree will persist on the host/parent file system.



