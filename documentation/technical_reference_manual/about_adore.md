# About ADORe

ADORe (Automated Driving Open Research) is an open-source software framework for **testing and developing automated driving** – on real vehicles, in simulation, and in combination with intelligent road infrastructure. It is developed mainly at the German Aerospace Center (DLR), but is explicitly intended for **everyone** to use, extend, and embed in their own projects.

At its core, ADORe is not a “finished” self-driving product. Instead, it is a **research and experimentation platform**:

- A set of **modular libraries** for automated driving (planning, control, multi-agent coordination, interfaces, etc.).
- A **system-level framework** that connects vehicles, simulations, and infrastructure.
- An environment to **try out new ideas**, compare strategies, and run experiments under realistic conditions.

---

## What problems ADORe tries to solve

Modern automated driving isn’t just about making one clever car. It’s about how many vehicles and the surrounding infrastructure **work together as a system**:

- Vehicles need to drive safely and comfortably on their own.
- They should also be able to **cooperate** with other vehicles and roadside units.
- Researchers need a way to evaluate algorithms at this **system level**, not just as isolated components.

ADORe is built to support exactly this kind of work:

- **Single-vehicle autonomy** – local planning and control on the vehicle itself.
- **Multi-agent / infrastructure-supported automation** – coordination via V2X (vehicle-to-everything) communication, infrastructure assistance, and backend services.
- **End-to-end experiments** – from high-level mission goals down to trajectory tracking and feedback.

---

## Key ideas

### 1. Modular building blocks, not a monolith

ADORe is organised as a set of **ROS 2–based components** that can be combined and swapped:

- Core libraries for geometry, motion planning and trajectory tracking.
- Nodes for single-vehicle automation (SAAD).
- Nodes and services for multi-agent / infrastructure-based automation (MAAD).
- Interfaces towards sensors, vehicles, simulators, and backends.

You can:

- Use individual libraries inside your own stack.
- Replace ADORe components with your own, as long as you respect the interfaces.
- Embed ADORe modules into existing projects without adopting everything.

The idea is that you can **start small** (e.g. just use a planning or control component) and grow into more of the framework over time.

---

### 2. Designed for both vehicles and infrastructure

ADORe is built around the assumption that automation will often be **shared between vehicle and infrastructure**, rather than living only inside the car:

- On-board stack for local autonomy on research vehicles.
- Infrastructure-side components that monitor traffic, compute cooperative plans, or assist vehicles via V2X.
- Back-end middleware to connect ADORe to project-specific cloud or edge services.

This makes it possible to run experiments such as:

- Infrastructure-guided trajectories in complex intersections.
- Cooperative manoeuvres between several vehicles.
- Remote-supported operation and supervision.

---

### 3. Works in simulation and on real vehicles

ADORe is meant to be **portable across environments**:

- Integration with traffic and vehicle simulators (e.g. SUMO, CARLA and related tools) for large-scale or repeatable tests.
- Deployment on DLR’s research vehicles with real sensors and actuators.
- Containerised setups so that the same software can run in CI, on dev machines, and on cars with minimal change.

This allows workflows like:

1. Prototype an idea purely in simulation.
2. Move the same ADORe components to a vehicle, keeping interfaces and behaviour consistent.
3. Use infrastructure-side ADORe instances to coordinate both simulated and real traffic participants in mixed scenarios.

---

## Who ADORe is for

Although ADORe is developed at DLR, it is meant for a **wider community**:

- **Research groups** working on planning, control, cooperative driving, V2X, traffic management, remote operation, or safety concepts.
- **Industry teams** who need a flexible, inspectable framework for experiments or prototyping.
- **Students and hobbyists** who want to explore automated driving beyond single-vehicle demos.

The software is open source, and the goal is to make it possible to:

- Reproduce and extend research results.
- Plug in your own algorithms (planners, controllers, decision-makers).
- Integrate ADORe into larger toolchains or platforms.

---

## What ADORe is *not*

To set expectations clearly:

- ADORe is **not** a ready-to-deploy commercial driverless system.
- It **does not target full SAE Level 4+ product deployments**, but rather research, prototyping, and demonstrations. 
- It assumes expert users who are comfortable working with ROS 2, Docker, and modern C++/Python.

Safety, validation, and certification for production systems remain the responsibility of whoever uses the framework.

---

## Typical ways people use ADORe

Here are a few common patterns:

- **Use it as a full stack** on a research vehicle or in simulation, and tune or swap selected modules.
- **Embed individual libraries** (e.g. motion planning, trajectory tracking) inside your own ROS 2 system.
- **Connect your infrastructure** (traffic controllers, roadside units, digital twins) to ADORe’s multi-agent layer and run cooperative experiments.
- **Prototype new ideas** (e.g. new decision logic, cooperative strategies, remote support concepts), while reusing all the “boring but necessary” parts like map handling, routing, and interfaces.

---

## Learn more

If you want to dive deeper into the architecture and research background behind ADORe, see the VEHITS 2025 paper *“ADORe: Unified Modular Framework for Vehicle and Infrastructure-Based System Level Automation”* included in this repository.   

For the practical side (how to build, run, and extend the framework), check the developer-oriented documentation and package-level READMEs in the codebase.
