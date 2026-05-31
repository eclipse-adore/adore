# Third-Party Libraries and Tools

This project makes use of the following third-party libraries, tools, and components.
Paths indicate where the content lives in this repository or how it is consumed
(vendored vs. system / container dependency).

| Name               | License                          | Location / Role                                   | URL / Notes |
|--------------------|----------------------------------|--------------------------------------------------|-------------|
| Helix Editor       | Mozilla Public License 2.0       | Dev container only (installed in Docker image)   | https://helix-editor.com/ |
| lichtblick-suite   | Mozilla Public License 2.0       | External visualization tool (not vendored)       | https://github.com/lichtblick-suite/lichtblick |
| libOpenDRIVE       | Apache License 2.0               | `vendor/libOpenDRIVE`                            | https://github.com/DLR-TS/libOpenDRIVE (fork of https://github.com/pageldev/libOpenDRIVE) |
| nlohmann/json      | MIT License                      | System dependency (`nlohmann-json3-dev` via apt) | https://github.com/nlohmann/json |
| Eigen3             | MPL-2.0 (plus BSD/LGPL parts)    | System dependency (`libeigen3-dev` via apt)      | https://eigen.tuxfamily.org |
| OSQP               | Apache License 2.0               | `vendor/osqp`                                    | https://osqp.org/ |
| OSQP-Eigen         | BSD 3-Clause License             | `vendor/osqp_eigen`                              | https://github.com/robotology/osqp-eigen |
| multi_agent_solver | Apache License 2.0               | `vendor/multi_agent_solver`                      | https://https://github.com/markomiz/multi_agent_solver |
| adore_model_checker| Apache License 2.0               | `vendor/adore_model_checker`                      | https://github.com/DLR-TS/adore_model_checker |
| ros2_observer      | Apache License 2.0               | `vendor/ros2_observer`                            | https://github.com/DLR-TS/ros2_observer |
| ROS 2              | Apache License 2.0               | System dependency                                | https://docs.ros.org/ |
| MkDocs & Material  | BSD 2-Clause / MIT               | `documentation/` (documentation build system)    | https://www.mkdocs.org/ ; https://squidfunk.github.io/mkdocs-material/ |
| spline.h           | GNU General Public License v2    | `libraries/lib/adore_math/include/spline.h`      | https://kluge.in-chemnitz.de/opensource/spline/spline.h |
| Tracecompass       | Eclipse Public License 2.0       | `vendor/ros2_observer/trace_compass`             | https://github.com/eclipse-tracecompass/org.eclipse.tracecompass |
| lttng-scope        | Eclipse Public License 1.0       | `vendor/ros2_observer/lttng_scope`               | https://github.com/lttng/lttng-scope |
| caches             | BSD 3-Clause License             | `vendor/caches/LICENSE.md`                       | https://github.com/s0nofab1t/caches (fork of https://github.com/vpetrigo/caches) |

---

## License Summary

- **Mozilla Public License 2.0 (MPL-2.0)**
- **Apache License 2.0**
- **MIT License**
- **BSD 2-Clause / 3-Clause Licenses**
- **GNU GPL / LGPL**
- **Eclipse Public License 2.0 (EPL-2.0)**
- **Eclipse Public License 1.0 (EPL-1.0)**

Please consult the individual projects and files for full license texts and any additional conditions.
