# Adding a new ROS 2 node to ADORe

This guide explains how to add a new ROS 2 node to the ADORe codebase, using the **official ROS 2 tutorials** as the primary reference and then describing what’s different in the ADORe setup.

## Recommended ROS 2 tutorials

Before or while adding a node, it’s worth skimming these (Jazzy docs shown, Humble is essentially identical):

* **Developing a ROS 2 package** (creating packages, C++/Python, install rules) ([docs.ros.org][1])

  * Jazzy: `https://docs.ros.org/en/jazzy/How-To-Guides/Developing-a-ROS-2-Package.html`

* There you can follow **Writing a simple publisher and subscriber** : 

  * `Writing a simple publisher and subscriber (C++)`
  * `Writing a simple publisher and subscriber (Python)`
* Optional but useful:

  * `Creating custom msg and srv files`
  * `Creating a launch file` and `Integrating launch files into ROS 2 packages`


---

## Where packages live in ADORe

In a generic ROS 2 tutorial, you create packages under something like `~/ros2_ws/src`. ([docs.ros.org][1])

In ADORe, the layout is slightly different:

* The **repo root** is mounted inside the dev container at:

  ```bash
  /home/<user>/adore
  ```

* The **colcon workspace** is:

  ```bash
  /home/<user>/adore/.colcon_workspace
  ```

* `.colcon_workspace/src` is populated via symlinks, created by `.docker/scripts/setup_colcon_src.sh`, to mirror a set of top-level “category” directories in the repo (nodes, libraries, interfaces, vendor, etc.).

**Where to put your new node package**

1. Open the repo in the dev container:

   ```bash
   just dev
   ```

2. In the container, inspect the top-level directories to see how things are grouped:

   ```bash
   ls
   ```

   You’ll see one or more directories that contain other ROS 2 packages already (for example, a “nodes” directory, a “libraries” directory, etc.). Choose the category that matches what you’re adding:

   * A runtime ROS node → put it alongside other node packages.
   * A pure library → put it alongside existing library packages.
   * New message/service definitions → put them in the interfaces/messages category.

3. You can create the package either:

   * Directly in the **top-level category directory**, or
   * Via the **colcon symlink** under `.colcon_workspace/src/<category>` → both end up in the same place because of the symlink.

---


## What’s different vs the vanilla ROS 2 tutorials?

Here’s a quick comparison between the official docs and the ADORe flow:

| Topic                    | ROS 2 tutorials                                     | ADORe specifics                                               |
| ------------------------ | --------------------------------------------------- | ------------------------------------------------------------- |
| Workspace location       | `~/ros2_ws/src`                                     | Repo root + `.colcon_workspace/src` via symlinks              |
| Environment setup        | Manually source `/opt/ros/<distro>/setup`           | Dev container auto-sources ROS Jazzy and the colcon overlay   |
| Package creation command | `ros2 pkg create ...`                               | Same command, but run inside the dev container                |
| Where to create packages | Directly in `~/ros2_ws/src`                         | In the appropriate top-level category inside the repo         |
| Build command            | `colcon build`                                      | `just build` or `colcon build` inside `.colcon_workspace`     |
| Running nodes            | `ros2 run <pkg> <exec>`                             | Same, but from inside dev container (recommended)             |

If you follow the official Jazzy “Developing a ROS 2 package” tutorial step-by-step **inside** the ADORe dev container and just adjust the workspace paths and category directory, you’ll end up with a node that behaves exactly like any other ADORe node, and it will be built and tested automatically by the existing `just`/colcon workflow.

[1]: https://docs.ros.org/en/jazzy/How-To-Guides/Developing-a-ROS-2-Package.html "Developing a ROS 2 package — ROS 2 Documentation: Jazzy  documentation"
