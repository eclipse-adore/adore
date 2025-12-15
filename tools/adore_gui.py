
# ********************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# https://www.eclipse.org/legal/epl-2.0
#
# SPDX-License-Identifier: EPL-2.0
# ********************************************************************************

import tkinter as tk
from tkinter import messagebox, Listbox, Scrollbar
from tkinter import ttk
import subprocess
from pathlib import Path
import threading
import time
import os
import re
import getpass


# ==== CONFIGURATION ====
DOCKER_CONTAINER_NAME = "adore"
USER = getpass.getuser()

CONTAINER_ADORE_PATH = f"/home/{USER}/adore"
CONTAINER_WS_PATH = f"{CONTAINER_ADORE_PATH}/.colcon_workspace"
CONTAINER_SCENARIO_DIR = f"{CONTAINER_WS_PATH}/src/adore_scenarios"

LAUNCH_EXT = ".launch.py"
EXCLUDED_DIRS = {"integration_tests", "assets", "scenario_helpers"}
launch_process = None

# Use ROS_DISTRO from inside the container if set; default to jazzy there.
ROS_SETUP_CMD = (
    'source "/opt/ros/${ROS_DISTRO:-jazzy}/setup.zsh" && '
    f'source "{CONTAINER_WS_PATH}/install/setup.zsh"'
)

EXCLUDED_COMMNANDS = {
    "api_restart",
    "api_stop",
    "api_start",
    "api_status",
    "due_diligence_scan",
    "default",
    "help",
    "dev",
    "build_dev",
    "clean_images",
    "cli",
    "stop_cli",
    "save",
    "load",
    "test",
    "docs",
    "ci",
    "docs_all",
    "build_ci",
    "run_ci",
    "docs_build",
    "docs_serve",
    "setup_colcon_src",
    "docs_clean",
    "docs_build_mkdocs",
    "docs_build",
    "docs_lint",
    "docs_publish",
    "docs_publish_gh_pages",
    "clean",
    "docs_watch",
    "edit_roads",
    "gui",
    "lichtblick",
    "docs_spellcheck",
}

# ==== FUNCTIONS ====


def parse_just_targets():
    """
    Query the dev container for available just recipes and return a dict
    {target_name: description}.
    """
    try:
        cmd = [
            "docker",
            "exec",
            DOCKER_CONTAINER_NAME,
            "bash",
            "-lc",
            f"cd {CONTAINER_ADORE_PATH} && just --list",
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        content = result.stdout
    except subprocess.CalledProcessError as exc:
        messagebox.showerror(
            "Error", f"Failed to run 'just --list':\n{exc}\n{exc.stderr}")
        return {}

    target_pattern = re.compile(r"^\s*([a-zA-Z0-9_-]+)\s*(?:#\s*(.*))?$")
    targets = {}

    for line in content.splitlines():
        # Skip the header line like "Available recipes:"
        if line.strip().startswith("Available recipes"):
            continue

        match = target_pattern.match(line)
        if not match:
            continue

        name = match.group(1)
        desc = match.group(2) or ""

        # Filter out recipes that don't make sense from inside the dev container
        if name in EXCLUDED_COMMNANDS:
            continue

        targets[name] = desc

    if not targets:
        print("⚠️ No just targets found or matched the expected pattern.")
    else:
        print(f"✅ Found just targets: {list(targets.keys())}")

    return targets


def run_just_target(target: str) -> None:
    """
    Run a just recipe inside the dev container from the repo root.
    """
    try:
        cmd = [
            "docker",
            "exec",
            DOCKER_CONTAINER_NAME,
            "bash",
            "-lc",
            f"cd {CONTAINER_ADORE_PATH} && just {target}",
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            messagebox.showinfo(
                "Success",
                result.stdout or f"Target '{target}' executed successfully.",
            )
        else:
            messagebox.showerror(
                "Failed",
                result.stderr
                or f"Target '{target}' failed with exit code {result.returncode}.",
            )
    except Exception as exc:  # noqa: BLE001
        messagebox.showerror("Execution Error", str(exc))


def refresh_scenarios():
    scenario_listbox.delete(0, tk.END)

    cmd = [
        "docker",
        "exec",
        DOCKER_CONTAINER_NAME,
        "bash",
        "-lc",
        # -L: follow symlinks; -type f: only real files at the targets
        f'find -L "{CONTAINER_SCENARIO_DIR}" -type f -name "*{LAUNCH_EXT}" 2>/dev/null',
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
    except Exception as exc:  # noqa: BLE001
        messagebox.showerror(
            "Scenario Error", f"Error running docker exec:\n{exc}")
        return

    if result.returncode != 0:
        message = (
            "Failed to list scenarios.\n\n"
            f"Command: {' '.join(cmd)}\n\n"
            f"Exit code: {result.returncode}\n"
            f"stderr:\n{result.stderr}"
        )
        print(message)
        messagebox.showerror("Scenario Error", message)
        return

    lines = [l for l in result.stdout.strip().splitlines() if l]
    if not lines:
        print(
            f"[adore_gui] No matching files under {CONTAINER_SCENARIO_DIR} "
            f"for pattern '*{LAUNCH_EXT}'"
        )

    for path in sorted(lines):
        rel_path = os.path.relpath(path, CONTAINER_SCENARIO_DIR)
        if any(part in EXCLUDED_DIRS for part in Path(rel_path).parts):
            continue
        if scenario_filter.get().lower() in rel_path.lower():
            # neat_path = rel_path[:-len(LAUNCH_EXT)]
            # # remove "adore" or "scenarios" prefixes if present
            # neat_path = neat_path.replace(
            #     "adore_", "").replace("_scenarios", "")
            scenario_listbox.insert(tk.END, rel_path)


def launch_selected_scenario(index):
    global launch_process
    rel_path = scenario_listbox.get(index)
    try:
        cmd = [
            "docker",
            "exec",
            DOCKER_CONTAINER_NAME,
            "zsh",
            "-lc",
            f'{ROS_SETUP_CMD} && ros2 launch "{CONTAINER_SCENARIO_DIR}/{rel_path}"',
        ]
        launch_process = subprocess.Popen(
            cmd,
            preexec_fn=os.setsid,
        )
    except Exception as exc:  # noqa: BLE001
        messagebox.showerror("Launch Error", str(exc))


def update_ros_node_list():
    while True:
        try:
            cmd = [
                "docker",
                "exec",
                DOCKER_CONTAINER_NAME,
                "zsh",
                "-lc",
                f"{ROS_SETUP_CMD} && ros2 node list",
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )
            nodes = result.stdout.strip().splitlines()
        except Exception:  # noqa: BLE001
            nodes = ["(Error running ros2 node list)"]
        ros_node_listbox.after(0, lambda: refresh_ros_node_listbox(nodes))
        time.sleep(0.5)


def refresh_ros_node_listbox(nodes):
    ros_node_listbox.delete(0, tk.END)
    for node in nodes:
        ros_node_listbox.insert(tk.END, node)


# ==== GUI SETUP ====
root = tk.Tk()
root.title("ADORe GUI")
root.geometry("1000x600")

style = ttk.Style()
style.theme_create(
    "modern_light",
    parent="clam",
    settings={
        ".": {
            "configure": {
                "background": "#f5f7fa",
                "foreground": "#2e2e2e",
                "font": ("Segoe UI", 10),
            }
        },
        "TFrame": {
            "configure": {
                "background": "#f5f7fa",
            }
        },
        "TLabel": {
            "configure": {
                "background": "#f5f7fa",
                "foreground": "#222222",
                "font": ("Segoe UI", 11, "bold"),
            }
        },
        "TButton": {
            "configure": {
                "padding": [8, 4],
                "relief": "flat",
                "background": "#e0e8f0",
                "foreground": "#1a1a1a",
                "borderwidth": 1,
            },
            "map": {
                "background": [
                    ("active", "#d0deed"),
                    ("pressed", "#bfd1e2"),
                    ("disabled", "#f0f0f0"),
                ],
                "foreground": [
                    ("disabled", "#a3a3a3"),
                ],
                "relief": [
                    ("pressed", "sunken"),
                    ("!pressed", "flat"),
                ],
            },
        },
        "TEntry": {
            "configure": {
                "padding": 5,
                "relief": "solid",
                "borderwidth": 1,
                "font": ("Segoe UI", 10),
                "foreground": "#1a1a1a",
                "fieldbackground": "#ffffff",
                "background": "#ffffff",
            }
        },
        "Vertical.TScrollbar": {
            "configure": {
                "gripcount": 0,
                "background": "#d9d9d9",
                "troughcolor": "#f0f0f0",
                "bordercolor": "#f0f0f0",
                "arrowcolor": "#555",
            }
        },
        "Listbox": {
            "configure": {
                "background": "#ffffff",
                "foreground": "#333",
                "selectbackground": "#cce0f5",
                "selectforeground": "#000000",
                "font": ("Segoe UI", 10),
                "borderwidth": 0,
                "relief": "flat",
            }
        },
    },
)
style.theme_use("modern_light")

main_frame = ttk.Frame(root, padding=10)
main_frame.pack(fill=tk.BOTH, expand=True)
main_frame.columnconfigure(1, weight=1)
main_frame.columnconfigure(2, weight=1)
main_frame.rowconfigure(0, weight=1)

# === JUST TARGETS COLUMN (formerly "Make Targets") ===
button_frame = ttk.Frame(main_frame)
button_frame.grid(row=0, column=0, sticky="ns", padx=(0, 15))
ttk.Label(button_frame, text="Just Targets", font=("Arial", 12, "bold")).pack(
    pady=(0, 5)
)

just_targets = parse_just_targets()
for target in just_targets:
    ttk.Button(
        button_frame,
        text=target,
        width=25,
        command=lambda t=target: run_just_target(t),
    ).pack(pady=2, fill=tk.X)

# === SCENARIOS COLUMN ===
scenario_frame = ttk.Frame(main_frame)
scenario_frame.grid(row=0, column=1, sticky="nsew")
scenario_frame.rowconfigure(2, weight=1)
scenario_frame.columnconfigure(0, weight=1)
ttk.Label(
    scenario_frame, text="Launchable Scenarios", font=("Arial", 12, "bold")
).grid(row=0, column=0, sticky="w")

scenario_filter = tk.StringVar()
scenario_filter.trace_add("write", lambda *args: refresh_scenarios())
ttk.Entry(scenario_frame, textvariable=scenario_filter).grid(
    row=1, column=0, sticky="ew", pady=5
)

scenario_listbox = Listbox(scenario_frame)
scenario_listbox.grid(row=2, column=0, sticky="nsew")
scrollbar = Scrollbar(
    scenario_frame, orient=tk.VERTICAL, command=scenario_listbox.yview
)
scrollbar.grid(row=2, column=1, sticky="ns")
scenario_listbox.config(yscrollcommand=scrollbar.set)

scenario_listbox.bind(
    "<Double-Button-1>",
    lambda e: launch_selected_scenario(scenario_listbox.curselection()[0]),
)

# === ROS 2 NODES COLUMN ===
node_frame = ttk.Frame(main_frame)
node_frame.grid(row=0, column=2, sticky="nsew")
node_frame.rowconfigure(1, weight=1)
node_frame.columnconfigure(0, weight=1)
ttk.Label(node_frame, text="Active ROS 2 Nodes", font=("Arial", 12, "bold")).grid(
    row=0, column=0, sticky="w"
)
ros_node_listbox = Listbox(node_frame)
ros_node_listbox.grid(row=1, column=0, sticky="nsew")

# === STARTUP ===
refresh_scenarios()
threading.Thread(target=update_ros_node_list, daemon=True).start()
root.mainloop()
