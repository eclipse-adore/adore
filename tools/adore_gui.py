import tkinter as tk
from tkinter import messagebox, Listbox, Scrollbar
from tkinter import ttk
import subprocess
from pathlib import Path
import threading
import time
import os
import signal
import re
import getpass

# ==== CONFIGURATION ====
DOCKER_CONTAINER_NAME = "adore_dev"
USER = getpass.getuser()

CONTAINER_ADORE_PATH = f"/home/{USER}/adore"
CONTAINER_WS_PATH = f"{CONTAINER_ADORE_PATH}/.colcon_workspace"
CONTAINER_SCENARIO_DIR = f"{CONTAINER_WS_PATH}/src/adore_scenarios"
CONTAINER_MAKEFILE = f"{CONTAINER_WS_PATH}/Makefile"

LAUNCH_EXT = ".py"
EXCLUDED_DIRS = {"integration_tests", "assets", "scenario_helpers"}
launch_process = None

ROS_SETUP_CMD = (
    "source /opt/ros/jazzy/setup.zsh && "
    "source ~/adore/.colcon_workspace/install/setup.zsh"
)

# ==== FUNCTIONS ====


def parse_makefile_targets(makefile_path):
    try:
        result = subprocess.run(
            ["docker", "exec", DOCKER_CONTAINER_NAME, "cat", makefile_path],
            capture_output=True,
            text=True,
        )
        result.check_returncode()
        content = result.stdout
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to read Makefile: {e}")
        return {}

    target_pattern = re.compile(r"^([a-zA-Z0-9_\-]+):(?:[^#]*)(?:##\s*(.*))?$")
    targets = {}
    for line in content.splitlines():
        match = target_pattern.match(line)
        if match:
            targets[match.group(1)] = match.group(2) or ""

    if not targets:
        print("⚠️ No Makefile targets found or matched the expected pattern.")
    else:
        print(f"✅ Found Makefile targets: {list(targets.keys())}")

    return targets


def run_make_target(target):
    try:
        command = [
            "docker", "exec", DOCKER_CONTAINER_NAME,
            "zsh", "-c",
            f'"{ROS_SETUP_CMD} && make -C {CONTAINER_WS_PATH} {target}"'
        ]
        result = subprocess.run(
            " ".join(command),
            shell=True,
            capture_output=False,
            text=True,
        )
        if result.returncode == 0:
            messagebox.showinfo(
                "Make Success", result.stdout or f"Target '{target}' executed successfully.")
        else:
            messagebox.showerror(
                "Make Failed", result.stderr or f"Target '{target}' failed.")
    except Exception as e:
        messagebox.showerror("Execution Error", str(e))


def refresh_scenarios():
    scenario_listbox.delete(0, tk.END)
    try:
        result = subprocess.run(
            ["docker", "exec", DOCKER_CONTAINER_NAME, "find",
                CONTAINER_SCENARIO_DIR, "-name", f"*{LAUNCH_EXT}"],
            capture_output=True,
            text=True,
        )
        result.check_returncode()
        for path in sorted(result.stdout.strip().splitlines()):
            rel_path = os.path.relpath(path, CONTAINER_SCENARIO_DIR)
            if any(part in EXCLUDED_DIRS for part in Path(rel_path).parts):
                continue
            if scenario_filter.get().lower() in rel_path.lower():
                scenario_listbox.insert(tk.END, rel_path)
    except Exception as e:
        messagebox.showerror("Scenario Error", str(e))


def launch_selected_scenario(index):
    global launch_process
    rel_path = scenario_listbox.get(index)
    try:
        command = [
            "docker", "exec", DOCKER_CONTAINER_NAME,
            "zsh", "-c",
            f'"{ROS_SETUP_CMD} && ros2 launch {CONTAINER_SCENARIO_DIR}/{rel_path}"'
        ]
        launch_process = subprocess.Popen(
            " ".join(command),
            shell=True,
            preexec_fn=os.setsid,
        )
    except Exception as e:
        messagebox.showerror("Launch Error", str(e))


def update_ros_node_list():
    while True:
        try:
            command = [
                "docker", "exec", DOCKER_CONTAINER_NAME,
                "zsh", "-c",
                f'"{ROS_SETUP_CMD} && ros2 node list"'
            ]
            result = subprocess.run(
                " ".join(command),
                shell=True,
                capture_output=True,
                text=True,
            )
            nodes = result.stdout.strip().splitlines()
        except Exception:
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
style.theme_create("modern_light", parent="clam", settings={
    ".": {
        "configure": {
            "background": "#f5f7fa",
            "foreground": "#2e2e2e",
            "font": ("Segoe UI", 10)
        }
    },
    "TFrame": {
        "configure": {
            "background": "#f5f7fa"
        }
    },
    "TLabel": {
        "configure": {
            "background": "#f5f7fa",
            "foreground": "#222222",
            "font": ("Segoe UI", 11, "bold")
        }
    },
    "TButton": {
        "configure": {
            "padding": [8, 4],
            "relief": "flat",
            "background": "#e0e8f0",
            "foreground": "#1a1a1a",
            "borderwidth": 1
        },
        "map": {
            "background": [
                ("active", "#d0deed"),
                ("pressed", "#bfd1e2"),
                ("disabled", "#f0f0f0")
            ],
            "foreground": [
                ("disabled", "#a3a3a3")
            ],
            "relief": [
                ("pressed", "sunken"),
                ("!pressed", "flat")
            ]
        }
    },
    "TEntry": {
        "configure": {
            "padding": 5,
            "relief": "solid",
            "borderwidth": 1,
            "font": ("Segoe UI", 10),
            "foreground": "#1a1a1a",
            "fieldbackground": "#ffffff",
            "background": "#ffffff"
        }
    },
    "Vertical.TScrollbar": {
        "configure": {
            "gripcount": 0,
            "background": "#d9d9d9",
            "troughcolor": "#f0f0f0",
            "bordercolor": "#f0f0f0",
            "arrowcolor": "#555"
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
            "relief": "flat"
        }
    }
})
style.theme_use("modern_light")


main_frame = ttk.Frame(root, padding=10)
main_frame.pack(fill=tk.BOTH, expand=True)
main_frame.columnconfigure(1, weight=1)
main_frame.columnconfigure(2, weight=1)
main_frame.rowconfigure(0, weight=1)

# === MAKE TARGETS COLUMN ===
button_frame = ttk.Frame(main_frame)
button_frame.grid(row=0, column=0, sticky="ns", padx=(0, 15))
ttk.Label(button_frame, text="Make Targets", font=(
    "Arial", 12, "bold")).pack(pady=(0, 5))

make_targets = parse_makefile_targets(CONTAINER_MAKEFILE)
for target in make_targets:
    ttk.Button(
        button_frame,
        text=target,
        width=25,
        command=lambda t=target: run_make_target(t),
    ).pack(pady=2, fill=tk.X)

# === SCENARIOS COLUMN ===
scenario_frame = ttk.Frame(main_frame)
scenario_frame.grid(row=0, column=1, sticky="nsew")
scenario_frame.rowconfigure(2, weight=1)
scenario_frame.columnconfigure(0, weight=1)
ttk.Label(scenario_frame, text="Launchable Scenarios", font=(
    "Arial", 12, "bold")).grid(row=0, column=0, sticky="w")

scenario_filter = tk.StringVar()
scenario_filter.trace_add("write", lambda *args: refresh_scenarios())
ttk.Entry(scenario_frame, textvariable=scenario_filter).grid(
    row=1, column=0, sticky="ew", pady=5)

scenario_listbox = Listbox(scenario_frame)
scenario_listbox.grid(row=2, column=0, sticky="nsew")
scrollbar = Scrollbar(scenario_frame, orient=tk.VERTICAL,
                      command=scenario_listbox.yview)
scrollbar.grid(row=2, column=1, sticky="ns")
scenario_listbox.config(yscrollcommand=scrollbar.set)

scenario_listbox.bind(
    "<Double-Button-1>", lambda e: launch_selected_scenario(scenario_listbox.curselection()[0]))

# === ROS 2 NODES COLUMN ===
node_frame = ttk.Frame(main_frame)
node_frame.grid(row=0, column=2, sticky="nsew")
node_frame.rowconfigure(1, weight=1)
node_frame.columnconfigure(0, weight=1)
ttk.Label(node_frame, text="Active ROS 2 Nodes", font=(
    "Arial", 12, "bold")).grid(row=0, column=0, sticky="w")
ros_node_listbox = Listbox(node_frame)
ros_node_listbox.grid(row=1, column=0, sticky="nsew")

# # === CONTROL BUTTONS ===
# button_bar = ttk.Frame(root)
# button_bar.pack(pady=5)
# ttk.Button(button_bar, text="Stop Launch", command=stop_launch).pack(side=tk.LEFT, padx=10)

# === STARTUP ===
refresh_scenarios()
threading.Thread(target=update_ros_node_list, daemon=True).start()
root.mainloop()
