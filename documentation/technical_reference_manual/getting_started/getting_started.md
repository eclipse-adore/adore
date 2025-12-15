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
*   Andrew Koerner
*   Björn Bahn
********************************************************************************
-->
This guide will help you get your system set up and configured to run ADORe.

1. First review the [System Requirements 🔗](system_requirements.md). 

2. Next review the [Prerequisites 🔗](prerequisites.md) 

## Cloning the ADORe repository
> **ℹ️INFO:**
> By default this guide assumes you have ssh keys configured for GitHub your GitHub account.
> For help on configuring your ssh keys visit: https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account


```bash
git clone git@github.com:eclipse-adore/adore.git
cd adore
git submodule update --init --recursive
```

> **⚠️ WARNING:** Failing to update and recursively clone the submodules will result in build failures!

> **ℹ️INFO:** If you would rather clone ADORe anonymously over https please review the [Anonymous Cloning 🔗](../system_and_development/anonymous_cloning.md) guide.

## Building ADORe Developer Environment
> **⚠️ WARNING:**
> To use the ADORe developer environment you must have Docker installed.

To have the easiest entry you can [install just](https://github.com/casey/just)

and run:
```bash
just dev
```

Alternatively, simple call

```bash
.docker/scripts/run_dev.sh
```

This will create and the developer environment where you can build all relevant packages with

```bash
just build
```

The full command list is available with

```bash
just help
```

> **⚠️ WARNING:**
> Building ADORe **will** fail until all submodules have been properly initialized. 
> If cloning or repository initialization fails refer to the
> [troubleshooting](../problems_and_solutions.md) guide before proceeding.
> Do not proceed with building ADORe until `git submodule update --init --receive`
> finishes without error. 

Next proceed to [Running Your First Scenario 🔗](running_your_first_scenario.md) 

## Using in an existing ROS2 project

The ADORe packages adore_(libraries/ros2_conversions/ros2_msgs/ros2_nodes/scenarios) can all be used directly in your existing ros2 project by pasting or symlining them into you ros2/colcon workspace.