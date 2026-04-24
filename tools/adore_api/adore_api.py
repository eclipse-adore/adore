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

import os
import subprocess
import threading
import time
import json
import hashlib
import logging
import queue
from datetime import datetime, timezone
from collections import deque, defaultdict
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import signal
import psutil
import argparse
from flask import send_from_directory


# ── Log broadcaster for the model checker log tab ────────────────────────────
class _LogBroadcaster:
    def __init__(self, maxlen=5000):
        self._lock = threading.Lock()
        self._clients = []
        self._buffer = []
        self._maxlen = maxlen

    def write(self, text, stream='stdout'):
        msg = json.dumps({
            'text': text.rstrip(),
            'stream': stream,
            'time': datetime.now().strftime('%H:%M:%S'),
        })
        with self._lock:
            self._buffer.append(msg)
            if len(self._buffer) > self._maxlen:
                self._buffer.pop(0)
            for q in list(self._clients):
                try:
                    q.put_nowait(msg)
                except Exception:
                    pass

    def subscribe(self):
        q = queue.Queue(maxsize=500)
        with self._lock:
            for line in self._buffer[-200:]:
                try:
                    q.put_nowait(line)
                except Exception:
                    pass
            self._clients.append(q)
        return q

    def unsubscribe(self, q):
        with self._lock:
            try:
                self._clients.remove(q)
            except ValueError:
                pass


_adore_log_broadcaster = _LogBroadcaster()


class _BroadcastLogHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = 'stderr' if record.levelno >= logging.WARNING else 'stdout'
            _adore_log_broadcaster.write(msg, stream)
        except Exception:
            pass


def _install_adore_log_handler():
    handler = _BroadcastLogHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s',
                                           datefmt='%H:%M:%S'))
    root = logging.getLogger()
    if not any(isinstance(h, _BroadcastLogHandler) for h in root.handlers):
        root.addHandler(handler)


_install_adore_log_handler()


model_check_blueprint = None
ros2_blueprint = None
stop_model_check_worker = None

try:
    from adore_model_checker.model_checker_api import get_model_check_blueprint, stop_model_check_worker as _stop_model_check_worker
    stop_model_check_worker = _stop_model_check_worker
    print("✓ ADORe Model Checker library found")
except (ImportError, RuntimeError) as e:
    print(f"⚠ Warning: ADORe Model Checker library not available: {e}")
    print("⚠ Model checking functionality will be disabled")
    print("⚠ Ensure ROS is sourced and adore_model_checker is installed to enable model checking")

try:
    from ros2tools.ros2api import *
    from ros2tools import ROS2Tools
    print("✓ ros2tools library found")
except ImportError as e:
    print(f"⚠ Warning: ros2tools library not found: {e}")
    print("⚠ ros2tools will be disabled")
    ROS2Tools = None

try:
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from util.ros_marshaller import ROSMarshaller
    print("✓ ROSMarshaller found")
except ImportError as e:
    print(f"⚠ Warning: ROSMarshaller not found: {e}")
    print("⚠ ROS topic functionality will be limited")
    ROSMarshaller = None

_HERE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__,
            template_folder=os.path.join(_HERE, 'templates'),
            static_folder=os.path.join(_HERE, 'static'))
CORS(app)

LOG_DIRECTORY = None

stored_positions = {
    'start': None,
    'goal': None
}


def sanitize_infinity(obj):
    """Recursively sanitize data for JSON serialization, replacing infinity and NaN values"""
    import math

    if isinstance(obj, dict):
        return {k: sanitize_infinity(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_infinity(item) for item in obj]
    elif isinstance(obj, float):
        if math.isinf(obj):
            return None
        elif math.isnan(obj):
            return None
        else:
            return obj
    else:
        return obj


class BagRecordingManager:
    def __init__(self, log_directory):
        self.log_directory = log_directory
        self.bag_recordings_dir = os.path.join(
            log_directory, "bag_file_recordings")
        os.makedirs(self.bag_recordings_dir, exist_ok=True)

        self.current_process = None
        self.recording_status = "idle"
        self.current_bag_name = None
        self.current_bag_path = None
        self.recording_start_time = None
        self.recording_duration = None
        self.recording_topics = []
        self.output_buffer = deque(maxlen=1000)
        self.output_lock = threading.Lock()

    def start_recording(self, duration=None, topics=None, scenario_name=None):
        if self.current_process and self.current_process.poll() is None:
            return {"success": False, "message": "Recording already in progress"}

        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

            if scenario_name:
                base_name = os.path.splitext(scenario_name)[0]
                bag_name = f"{base_name}_{timestamp}"
            else:
                bag_name = f"recording_{timestamp}"

            bag_path = os.path.join(self.bag_recordings_dir, bag_name)

            cmd = ["ros2", "bag", "record", "-o", bag_path]

            if duration:
                cmd.extend(["--max-bag-duration", str(duration)])

            if topics and len(topics) > 0:
                cmd.extend(topics)
            else:
                cmd.append("-a")

            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )

            self.recording_status = "recording"
            self.current_bag_name = bag_name
            self.current_bag_path = bag_path
            self.recording_start_time = time.time()
            self.recording_duration = duration
            self.recording_topics = topics if topics else ["all"]
            self.output_buffer.clear()

            threading.Thread(
                target=self._monitor_recording_output, daemon=True).start()

            if duration:
                threading.Thread(target=self._auto_stop_recording,
                                 args=(duration,), daemon=True).start()

            return {
                "success": True,
                "message": f"Recording started: {bag_name}",
                "bag_name": bag_name,
                "bag_path": bag_path,
                "topics": self.recording_topics,
                "duration": duration
            }

        except Exception as e:
            self.recording_status = "failed"
            return {"success": False, "message": f"Failed to start recording: {str(e)}"}

    def stop_recording(self):
        if not self.current_process:
            return {"success": False, "message": "No recording in progress"}

        try:
            if self.current_process.poll() is None:
                self.current_process.terminate()

                timeout = 10
                start_time = time.time()
                while self.current_process.poll() is None and (time.time() - start_time) < timeout:
                    time.sleep(0.1)

                if self.current_process.poll() is None:
                    self.current_process.kill()

            self.recording_status = "stopped"

            relative_path = os.path.relpath(
                self.current_bag_path, self.log_directory)

            return {
                "success": True,
                "message": f"Recording stopped: {self.current_bag_name}",
                "bag_name": self.current_bag_name,
                "relative_path": relative_path
            }

        except Exception as e:
            return {"success": False, "message": f"Failed to stop recording: {str(e)}"}

    def get_recording_status(self):
        if self.current_process:
            if self.current_process.poll() is None:
                self.recording_status = "recording"
            else:
                self.recording_status = "completed" if self.current_process.returncode == 0 else "failed"

        runtime = None
        if self.recording_start_time and self.recording_status == "recording":
            runtime = time.time() - self.recording_start_time

        return {
            "status": self.recording_status,
            "bag_name": self.current_bag_name,
            "bag_path": self.current_bag_path,
            "topics": self.recording_topics,
            "duration": self.recording_duration,
            "runtime": runtime,
            "pid": self.current_process.pid if self.current_process else None
        }

    def list_recorded_bags(self):
        try:
            bags = []
            if os.path.exists(self.bag_recordings_dir):
                for item in os.listdir(self.bag_recordings_dir):
                    item_path = os.path.join(self.bag_recordings_dir, item)
                    if os.path.isdir(item_path):
                        relative_path = os.path.relpath(
                            item_path, self.log_directory)
                        stat = os.stat(item_path)
                        bags.append({
                            "name": item,
                            "path": item_path,
                            "relative_path": relative_path,
                            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            "size_mb": sum(os.path.getsize(os.path.join(item_path, f))
                                           for f in os.listdir(item_path)
                                           if os.path.isfile(os.path.join(item_path, f))) / (1024*1024)
                        })

            bags.sort(key=lambda x: x["created"], reverse=True)
            return {"success": True, "bags": bags}
        except Exception as e:
            return {"success": False, "message": f"Failed to list bags: {str(e)}"}

    def get_recording_output(self, lines=100):
        with self.output_lock:
            output_lines = list(self.output_buffer)[-lines:]
            return "\n".join(output_lines)

    def _monitor_recording_output(self):
        if not self.current_process:
            return

        for line in iter(self.current_process.stdout.readline, ''):
            if line:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                formatted_line = f"[{timestamp}] {line.rstrip()}"

                with self.output_lock:
                    self.output_buffer.append(formatted_line)

    def _auto_stop_recording(self, duration):
        time.sleep(duration)
        if self.current_process and self.current_process.poll() is None:
            self.stop_recording()


class TopicManager:
    def __init__(self):
        self.subscribers = {}
        self.publishers = {}
        self.cleanup_interval = 10
        self.message_limit = 10
        self.lock = threading.RLock()
        self.cleanup_thread = None
        self.ros_available = ROSMarshaller is not None

        if self.ros_available:
            self.start_cleanup_thread()

    def start_cleanup_thread(self):
        def cleanup_loop():
            while True:
                try:
                    time.sleep(5)
                    self.cleanup_unused()
                except Exception as e:
                    print(f"Error in cleanup thread: {e}")

        self.cleanup_thread = threading.Thread(
            target=cleanup_loop, daemon=True)
        self.cleanup_thread.start()

    def cleanup_unused(self):
        if not self.ros_available:
            return

        current_time = time.time()

        with self.lock:
            topics_to_remove = []
            for topic, sub_data in self.subscribers.items():
                if current_time - sub_data['last_access'] > self.cleanup_interval:
                    topics_to_remove.append(topic)

            for topic in topics_to_remove:
                print(f"Pruning unused subscriber for topic: {topic}")
                del self.subscribers[topic]

            topics_to_remove = []
            for topic, pub_data in self.publishers.items():
                if current_time - pub_data['last_access'] > self.cleanup_interval:
                    topics_to_remove.append(topic)

            for topic in topics_to_remove:
                print(f"Pruning unused publisher for topic: {topic}")
                del self.publishers[topic]

    def get_or_create_subscriber(self, topic, limit=None):
        if not self.ros_available:
            return []

        if limit is None:
            limit = self.message_limit

        with self.lock:
            current_time = time.time()

            if topic in self.subscribers:
                self.subscribers[topic]['last_access'] = current_time
                messages = list(self.subscribers[topic]['messages'])
                return messages[-limit:] if limit > 0 else messages

            messages_queue = deque(maxlen=1000)

            def topic_callback(json_data, topic_name, datatype):
                try:
                    message_data = {
                        'timestamp': time.time(),
                        'topic': topic_name,
                        'datatype': datatype,
                        'data': json.loads(json_data) if isinstance(json_data, str) else json_data
                    }
                    messages_queue.append(message_data)
                    for listener in self.subscribers.get(topic, {}).get('listeners', []):
                        try:
                            listener(json_data, topic_name, datatype)
                        except Exception:
                            pass
                except Exception as e:
                    print(f"Error processing message for topic {topic}: {e}")

            try:
                sub_thread = ROSMarshaller.subscribe(topic, topic_callback)

                self.subscribers[topic] = {
                    'thread': sub_thread,
                    'messages': messages_queue,
                    'last_access': current_time
                }

                print(f"Created new subscriber for topic: {topic}")
            except Exception as e:
                print(f"Failed to create subscriber for topic {topic}: {e}")

            return []

    def get_publisher(self, topic):
        if not self.ros_available:
            return False

        with self.lock:
            current_time = time.time()

            if topic not in self.publishers:
                self.publishers[topic] = {'last_access': current_time}
                print(f"Registered publisher for topic: {topic}")
            else:
                self.publishers[topic]['last_access'] = current_time

            return True

    def get_stats(self):
        with self.lock:
            return {
                'active_subscribers': len(self.subscribers),
                'active_publishers': len(self.publishers),
                'subscriber_topics': list(self.subscribers.keys()),
                'publisher_topics': list(self.publishers.keys()),
                'ros_available': self.ros_available
            }


topic_manager = TopicManager()


class ScenarioManager:
    def __init__(self, base_directory=None):
        # Make base_directory relative to this file, not to current working dir
        if base_directory is None:
            here = os.path.dirname(os.path.abspath(__file__))
            # Adjust this relative path if your repo layout changes
            base_directory = os.path.abspath(
                os.path.join(here, "../../adore_scenarios")
            )

        self.base_directory = base_directory
        self.current_process = None
        self.status = "idle"
        self.current_scenario = None
        self.current_scenario_content = None
        self.output_buffer = deque(maxlen=10000)
        self.loop_mode = False
        self.loop_delay = 0
        self.default_runtime = 60
        self.loop_thread = None
        self.output_lock = threading.Lock()
        self.scenario_start_time = None
        self.loop_active = False
        self.model_check_enabled = True
        self.model_check_config = "config/default.yaml"
        self.current_model_check_run_id = None
        self.waiting_for_model_check = False
        self.model_check_lock = threading.Lock()

        os.makedirs(self.base_directory, exist_ok=True)

    def get_available_scenarios(self):
        if not os.path.exists(self.base_directory):
            return []

        scenarios = []
        for root, dirs, files in os.walk(self.base_directory):
            for file in files:
                if file.endswith('.launch.py') or file.endswith('.launch.xml'):
                    rel_path = os.path.relpath(
                        os.path.join(root, file), self.base_directory)
                    scenarios.append(rel_path)
        return scenarios

    def get_scenario_content(self, scenario_path):
        try:
            full_path = os.path.join(self.base_directory, scenario_path)
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    return {"success": True, "content": f.read(), "path": scenario_path}
            else:
                return {"success": False, "message": f"Scenario file not found: {scenario_path}"}
        except Exception as e:
            return {"success": False, "message": f"Error reading scenario: {str(e)}"}

    def save_scenario(self, scenario_name, content):
        try:
            if not scenario_name.endswith('.launch.py'):
                scenario_name += '.launch.py'

            full_path = os.path.join(self.base_directory, scenario_name)

            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, 'w') as f:
                f.write(content)

            return {"success": True, "message": f"Scenario saved as {scenario_name}"}
        except Exception as e:
            return {"success": False, "message": f"Error saving scenario: {str(e)}"}

    def start_model_check_then_scenario(self, scenario_input, is_file=True, model_check_enabled=True, model_check_config="config/default.yaml"):
        """Start scenario first, wait for ROS nodes to publish, then start model checker"""
        if self.current_process and self.current_process.poll() is None:
            return {"success": False, "message": "Scenario already running"}

        try:
            with self.model_check_lock:
                self.waiting_for_model_check = False
                self.current_model_check_run_id = None

            # Step 1: Start the scenario
            print("Starting scenario...")
            scenario_result = self.start_scenario(scenario_input, is_file)
            if not scenario_result["success"]:
                return scenario_result

            if model_check_enabled and model_check_blueprint is not None:
                # Wait for ROS nodes to come up and begin publishing before
                # the model checker opens its monitoring window
                print("Waiting 5 seconds for ROS nodes to publish...")
                time.sleep(5)

                # Step 2: Start model checking
                print("Starting model checking...")
                model_check_result = self._start_model_check(model_check_config)
                print(f"Model check start result: {model_check_result}")

                if model_check_result["success"]:
                    run_id = model_check_result.get("run_id")
                    if run_id is not None:
                        with self.model_check_lock:
                            self.current_model_check_run_id = run_id
                            self.waiting_for_model_check = True
                        print(f"Model checking started with run ID: {self.current_model_check_run_id}")
                    else:
                        print("Error: Model check start succeeded but no run ID returned")
                        return {
                            "success": False,
                            "message": "Model check start succeeded but no run ID returned",
                            "debug_info": model_check_result
                        }
                else:
                    error_msg = model_check_result.get('message', 'Unknown error')
                    print(f"Failed to start model checking: {error_msg}")
                    return {
                        "success": False,
                        "message": f"Failed to start model checking: {error_msg}",
                        "debug_info": model_check_result
                    }

                scenario_result['model_check_result'] = model_check_result
            else:
                if not model_check_enabled:
                    print("Model checking disabled")
                if model_check_blueprint is None:
                    print("Model check blueprint not available")

            return scenario_result

        except Exception as e:
            print(f"Exception in start_model_check_then_scenario: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"Failed to start model check and scenario: {str(e)}"}

    def _start_model_check(self, config_file):
        """Start model checking using internal test client"""
        try:
            print(f"Starting model check with config: {config_file}")

            # Check if model checker is available
            if model_check_blueprint is None:
                return {"success": False, "message": "Model checker blueprint not available"}

            # Import here to avoid circular imports
            try:
                from adore_model_checker.model_checker_api import _get_api
            except ImportError as e:
                print(f"Failed to import model checker API: {e}")
                return {"success": False, "message": f"Failed to import model checker API: {e}"}

            # Get the API instance
            try:
                api_instance = _get_api()
                print("Got model checker API instance")
            except Exception as e:
                print(f"Failed to get model checker API instance: {e}")
                return {"success": False, "message": f"Failed to get model checker API instance: {e}"}

            # Verify the API instance has required components
            if not hasattr(api_instance, 'worker'):
                return {"success": False, "message": "Model checker API instance missing worker"}

            if not hasattr(api_instance.worker, 'queue_online_run'):
                return {"success": False, "message": "Model checker worker missing queue_online_run method"}

            # Queue the model check run directly
            try:
                print(
                    f"Queuing online run with duration: {self.default_runtime}, vehicle_id: 0")
                run_id = api_instance.worker.queue_online_run(
                    config_file=config_file,
                    duration=self.default_runtime,
                    vehicle_id=0
                )
                self.current_model_check_run_id = run_id
                print(f"Queued model check run with ID: {run_id}")
            except Exception as e:
                print(f"Failed to queue model check run: {e}")
                import traceback
                traceback.print_exc()
                return {"success": False, "message": f"Failed to queue model check run: {e}"}

            # Verify the run was created
            if run_id is None:
                return {"success": False, "message": "Model check run ID is None"}

            try:
                run = api_instance.cache.get_run(run_id)
                if run:
                    print(
                        f"Verified run {run_id} exists with status: {run.status}")
                else:
                    print(
                        f"Warning: Could not verify run {run_id} was created")
                    return {"success": False, "message": f"Could not verify run {run_id} was created"}
            except Exception as e:
                print(f"Error verifying run creation: {e}")
                # Don't fail here, just log the warning

            return {"success": True, "run_id": run_id}

        except Exception as e:
            print(f"Exception starting model check: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"Exception starting model check: {str(e)}"}

    def start_scenario(self, scenario_input, is_file=True):
        if self.current_process and self.current_process.poll() is None:
            return {"success": False, "message": "Scenario already running"}

        try:
            if is_file:
                # scenario_input like:
                #   "adore_simulation_scenarios/dlr_118_to_gate.launch.py"
                # relative to self.base_directory (which points at adore_scenarios/)
                scenario_path = os.path.join(
                    self.base_directory, scenario_input)
                full_path = os.path.abspath(scenario_path)

                if not os.path.exists(full_path):
                    return {
                        "success": False,
                        "message": f"Scenario file not found: {full_path}",
                    }

                # Store content for status/debug
                with open(full_path, "r") as f:
                    self.current_scenario_content = f.read()

                # 🔧 Important: use absolute path, not package/file
                # This maps directly onto the working CLI command:
                #   ros2 launch /abs/path/to/launch.py
                cmd = ["ros2", "launch", full_path]
                cwd = None
                self.current_scenario = scenario_input

                print(
                    f"[ScenarioManager] Starting scenario via ros2 launch: "
                    f"{full_path} (base_directory='{self.base_directory}')"
                )
            else:
                # Always write the temp file into simulation_scenarios/ so
                # that sys.path.append(os.path.dirname(__file__)) inside the
                # launch file resolves position.py, simulated_vehicle.py etc.
                scenario_dir = os.path.join(self.base_directory, "simulation_scenarios")
                os.makedirs(scenario_dir, exist_ok=True)
                temp_file = os.path.join(scenario_dir, "temp_custom_scenario.launch.py")
                full_path = os.path.abspath(temp_file)

                with open(full_path, "w") as f:
                    f.write(scenario_input)

                self.current_scenario_content = scenario_input
                self.current_scenario = os.path.relpath(full_path, self.base_directory)

                cmd = ["ros2", "launch", full_path]
                cwd = None

                print(
                    f"[ScenarioManager] Starting custom scenario from temp file: {full_path}"
                )

            scenario_env = _source_workspace_env()
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                cwd=cwd,
                env=scenario_env,
            )

            time.sleep(0.5)
            if self.current_process.poll() is not None:
                self.status = "failed"
                output = self.current_process.stdout.read()
                return {
                    "success": False,
                    "message": f"Scenario process exited immediately (rc={self.current_process.returncode}): {output}",
                }

            self.status = "running"
            self.scenario_start_time = time.time()
            self.output_buffer.clear()

            threading.Thread(target=self._monitor_output, daemon=True).start()

            return {"success": True, "message": "Scenario started successfully"}

        except Exception as e:
            self.status = "failed"
            return {
                "success": False,
                "message": f"Failed to start scenario: {str(e)}",
            }

    def stop_scenario(self):
        if not self.current_process:
            return {"success": False, "message": "No scenario running"}

        try:
            if self.current_process.poll() is None:
                self.current_process.terminate()
                time.sleep(2)
                if self.current_process.poll() is None:
                    self.current_process.kill()

            self.status = "idle"
            return {"success": True, "message": "Scenario stopped"}

        except Exception as e:
            return {"success": False, "message": f"Failed to stop scenario: {str(e)}"}

    def halt_all(self):
        try:
            all_processes = []
            try:
                result = subprocess.run(
                    ["ps", "aux"], capture_output=True, text=True, check=False)
                if result.stdout:
                    all_processes = result.stdout.strip().split('\n')[1:]
            except:
                pass

            ros2_pids_to_kill = []
            for line in all_processes:
                if 'ros2' in line.lower():
                    parts = line.split()
                    if len(parts) >= 11:
                        pid = parts[1]
                        command = ' '.join(parts[10:])

                        if any(exclude in command.lower() for exclude in [
                            'docker exec',
                            'docker-',
                            'containerd',
                            'sleep infinity',
                            'rsyslogd',
                            'entrypoint.sh',
                            '/bin/bash',
                            '/bin/zsh',
                            'adore-cli-main'
                        ]):
                            continue

                        if any(exclude in command.lower() for exclude in [
                            'bash -c',
                            'zsh -c',
                            '/usr/bin/zsh',
                            '/bin/bash',
                            'source ~/.zshrc'
                        ]):
                            continue

                        if any(include in command.lower() for include in [
                            'ros2 launch',
                            'ros2 run',
                            'ros2 bag',
                            'ros2 topic',
                            'ros2 service',
                            'ros2 node',
                            '_node',
                            'launch.py'
                        ]) or ('python3' in command.lower() and 'ros2' in command.lower()):
                            ros2_pids_to_kill.append(pid)

            for pid in ros2_pids_to_kill:
                try:
                    subprocess.run(["kill", "-TERM", pid],
                                   check=False, timeout=5)
                except:
                    pass

            import time
            time.sleep(2)

            for pid in ros2_pids_to_kill:
                try:
                    subprocess.run(["kill", "-KILL", pid],
                                   check=False, timeout=5)
                except:
                    pass

            subprocess.run(["ros2", "daemon", "stop"], check=False, timeout=10)

            if self.current_process:
                try:
                    self.current_process.terminate()
                    self.current_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.current_process.kill()
                    self.current_process.wait()
                except:
                    pass

            self.status = "idle"
            self.current_process = None
            return {"success": True, "message": f"Halted {len(ros2_pids_to_kill)} ROS2 processes"}

        except Exception as e:
            return {"success": False, "message": f"Failed to halt scenarios: {str(e)}"}

    def restart_scenario(self):
        self.halt_all()
        time.sleep(2)

        if self.current_scenario:
            return self.start_model_check_then_scenario(
                self.current_scenario,
                is_file=True,
                model_check_enabled=self.model_check_enabled,
                model_check_config=self.model_check_config
            )
        else:
            return {"success": False, "message": "No scenario to restart"}

    def get_output(self, lines=1000):
        with self.output_lock:
            output_lines = list(self.output_buffer)[-lines:]
            return "\n".join(output_lines)

    def is_model_check_complete(self):
        """Check if model checking is complete or failed"""
        if not self.waiting_for_model_check or not self.current_model_check_run_id:
            return True  # No model checking in progress

        try:
            print(
                f"Checking completion status for run {self.current_model_check_run_id}")
            with app.test_client() as client:
                response = client.get(
                    f'/api/model_check/result/{self.current_model_check_run_id}')

                if response.status_code == 200:
                    result = response.get_json()
                    status = result.get('status', 'unknown')
                    print(f"Model check status: {status}")

                    if status in ['completed', 'failed', 'cancelled', 'error']:
                        with self.model_check_lock:
                            self.waiting_for_model_check = False
                        print(
                            f"Model checking completed with status: {status}")

                        # If failed, log the error
                        if status in ['failed', 'error']:
                            error_msg = result.get(
                                'error_message', 'Unknown error')
                            print(f"Model checking failed: {error_msg}")

                        return True
                    else:
                        return False  # Still running
                elif response.status_code == 404:
                    print(f"Run {self.current_model_check_run_id} not found")
                    with self.model_check_lock:
                        self.waiting_for_model_check = False
                    return True
                else:
                    print(
                        f"Error checking status: HTTP {response.status_code}")
                    return False

        except Exception as e:
            print(f"Error checking model check status: {e}")
            import traceback
            traceback.print_exc()
            # On error, assume complete to avoid hanging
            with self.model_check_lock:
                self.waiting_for_model_check = False
            return True

    def get_status(self):
        if self.current_process:
            if self.current_process.poll() is None:
                self.status = "running"
            else:
                self.status = "failed" if self.current_process.returncode != 0 else "idle"

        runtime = None
        if self.scenario_start_time and self.status == "running":
            runtime = time.time() - self.scenario_start_time

        return {
            "status": self.status,
            "scenario": self.current_scenario,
            "scenario_content": self.current_scenario_content,
            "loop_mode": self.loop_mode,
            "loop_delay": self.loop_delay,
            "default_runtime": self.default_runtime,
            "runtime": runtime,
            "pid": self.current_process.pid if self.current_process else None,
            "model_check_enabled": self.model_check_enabled,
            "model_check_config": self.model_check_config,
            "waiting_for_model_check": self.waiting_for_model_check,
            "current_model_check_run_id": self.current_model_check_run_id  # Add this line
        }

    def set_loop_mode(self, enabled, delay=0, runtime=60, model_check_enabled=True, model_check_config="config/default.yaml"):
        self.loop_mode = enabled
        self.loop_delay = delay
        self.default_runtime = runtime
        self.model_check_enabled = model_check_enabled
        self.model_check_config = model_check_config

        if enabled:
            self.loop_active = True
            if not self.loop_thread or not self.loop_thread.is_alive():
                self.loop_thread = threading.Thread(
                    target=self._loop_monitor, daemon=True)
                self.loop_thread.start()
        else:
            self.loop_active = False

    def _monitor_output(self):
        if not self.current_process:
            return

        for line in iter(self.current_process.stdout.readline, ''):
            if line:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                formatted_line = f"[{timestamp}] {line.rstrip()}"

                with self.output_lock:
                    self.output_buffer.append(formatted_line)

    def _loop_monitor(self):
        while self.loop_active:
            if self.loop_mode and self.current_scenario:
                # Check if scenario is running
                if self.current_process and self.current_process.poll() is None:
                    # Check if runtime has been exceeded
                    if self.scenario_start_time and (time.time() - self.scenario_start_time) >= self.default_runtime:
                        print(
                            f"Loop: Runtime ({self.default_runtime}s) reached, halting...")
                        self.halt_all()

                        # Wait for model checking to complete if it's running
                        if self.waiting_for_model_check:
                            print("Loop: Waiting for model checking to complete...")
                            max_wait_time = 300  # 5 minutes max wait
                            wait_start = time.time()

                            while self.waiting_for_model_check and (time.time() - wait_start) < max_wait_time:
                                if self.is_model_check_complete():
                                    print("Loop: Model checking completed")
                                    break
                                time.sleep(2)

                            if self.waiting_for_model_check:
                                print(
                                    "Loop: Model checking timeout, proceeding anyway")
                                with self.model_check_lock:
                                    self.waiting_for_model_check = False

                        time.sleep(2)

                        if self.loop_mode and self.current_scenario:
                            print(
                                f"Loop: Waiting {self.loop_delay}s before restart...")
                            time.sleep(self.loop_delay)
                            print(
                                f"Loop: Starting scenario: {self.current_scenario}")
                            self.start_model_check_then_scenario(
                                self.current_scenario,
                                is_file=True,
                                model_check_enabled=self.model_check_enabled,
                                model_check_config=self.model_check_config
                            )

                elif self.current_process and self.current_process.poll() is not None:
                    print(
                        f"Loop: Process ended, waiting for model check and restarting after {self.loop_delay}s...")

                    # Wait for model checking to complete
                    if self.waiting_for_model_check:
                        print(
                            "Loop: Waiting for model checking to complete after scenario end...")
                        max_wait_time = 300
                        wait_start = time.time()

                        while self.waiting_for_model_check and (time.time() - wait_start) < max_wait_time:
                            if self.is_model_check_complete():
                                print(
                                    "Loop: Model checking completed after scenario end")
                                break
                            time.sleep(2)

                        if self.waiting_for_model_check:
                            print("Loop: Model checking timeout after scenario end")
                            with self.model_check_lock:
                                self.waiting_for_model_check = False

                    self.halt_all()
                    time.sleep(2)

                    if self.loop_mode and self.current_scenario:
                        time.sleep(self.loop_delay)
                        self.start_model_check_then_scenario(
                            self.current_scenario,
                            is_file=True,
                            model_check_enabled=self.model_check_enabled,
                            model_check_config=self.model_check_config
                        )

                elif not self.current_process:
                    print(
                        f"Loop: No process running, starting scenario: {self.current_scenario}")
                    self.start_model_check_then_scenario(
                        self.current_scenario,
                        is_file=True,
                        model_check_enabled=self.model_check_enabled,
                        model_check_config=self.model_check_config
                    )

            time.sleep(1)


class WorkspaceMonitor:
    """
    Watches ros2_workspace/build for changes and re-sources
    ros2_workspace/install/setup.bash whenever the build directory is mutated.

    The environment snapshot produced by sourcing setup.bash is injected into
    os.environ so that all subsequent subprocess calls (ros2 launch, ros2 bag,
    etc.) inherit the updated ROS environment without restarting the API.
    """

    POLL_INTERVAL = 2.0

    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.build_dir = os.path.join(workspace_root, "ros2_workspace", "build")
        self.install_dir = os.path.join(workspace_root, "ros2_workspace", "install")
        self.setup_script = os.path.join(self.install_dir, "setup.bash")

        self._lock = threading.Lock()
        self._last_snapshot: str | None = None
        self._sourced_at: float | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name="workspace-monitor")
        self._thread.start()
        print(f"✓ Workspace monitor watching: {self.build_dir}")

    def stop(self):
        self._running = False

    def check_build_ready(self) -> dict | None:
        """
        Returns an error dict (suitable for jsonify) when the build directory
        is absent or empty, or None when everything looks fine.
        """
        if not os.path.isdir(self.build_dir):
            return {
                "success": False,
                "error": "workspace_not_built",
                "message": (
                    f"ROS 2 workspace build directory not found: {self.build_dir}. "
                    "Run `colcon build` inside ros2_workspace to fix this."
                ),
            }

        entries = [e for e in os.scandir(self.build_dir) if not e.name.startswith(".")]
        if not entries:
            return {
                "success": False,
                "error": "workspace_not_built",
                "message": (
                    f"ROS 2 workspace build directory is empty: {self.build_dir}. "
                    "Run `colcon build` inside ros2_workspace to fix this."
                ),
            }

        return None

    def get_status(self) -> dict:
        with self._lock:
            return {
                "build_dir": self.build_dir,
                "build_dir_exists": os.path.isdir(self.build_dir),
                "install_dir_exists": os.path.isdir(self.install_dir),
                "setup_script_exists": os.path.isfile(self.setup_script),
                "last_sourced_at": self._sourced_at,
                "monitoring": self._running,
            }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _snapshot(self) -> str:
        """
        Produce a fingerprint of the build directory based on the mtimes and
        sizes of all regular files.  Lightweight enough to run every few seconds.
        """
        if not os.path.isdir(self.build_dir):
            return ""

        hasher = hashlib.md5()
        for root, dirs, files in os.walk(self.build_dir):
            dirs.sort()
            for fname in sorted(files):
                path = os.path.join(root, fname)
                try:
                    st = os.stat(path)
                    hasher.update(f"{path}:{st.st_mtime}:{st.st_size}".encode())
                except OSError:
                    pass
        return hasher.hexdigest()

    def _source_setup(self):
        if not os.path.isfile(self.setup_script):
            print(f"⚠  Workspace setup script not found: {self.setup_script}")
            return

        try:
            result = subprocess.run(
                ["bash", "-c", f"source '{self.setup_script}' && env -0"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                print(f"⚠  Failed to source workspace setup: {result.stderr.strip()}")
                return

            new_env = {}
            for entry in result.stdout.split("\0"):
                if "=" in entry:
                    k, _, v = entry.partition("=")
                    new_env[k] = v

            os.environ.update(new_env)

            with self._lock:
                self._sourced_at = time.time()

            print(f"✓ Workspace re-sourced: {self.setup_script}")
        except subprocess.TimeoutExpired:
            print("⚠  Timeout sourcing workspace setup script")
        except Exception as e:
            print(f"⚠  Error sourcing workspace setup script: {e}")

    def _poll_loop(self):
        # Source immediately on startup if the workspace already exists
        initial = self._snapshot()
        if initial:
            self._source_setup()

        with self._lock:
            self._last_snapshot = initial

        while self._running:
            time.sleep(self.POLL_INTERVAL)
            try:
                current = self._snapshot()
                with self._lock:
                    changed = current != self._last_snapshot
                    self._last_snapshot = current

                if changed and current:
                    print("Workspace build directory changed, re-sourcing install/setup.bash...")
                    self._source_setup()
            except Exception as e:
                print(f"⚠  Workspace monitor error: {e}")


workspace_monitor: WorkspaceMonitor | None = None


def _source_workspace_env() -> dict:
    """
    Source ros2_workspace/install/setup.bash (falling back to setup.sh) and
    return a copy of the environment with the workspace overlaid.  Called
    immediately before every scenario Popen so the child always inherits a
    current workspace environment regardless of when the monitor last ran.
    """
    workspace_root = os.environ.get(
        'WORKSPACE_ROOT',
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    )
    install_dir = os.path.join(workspace_root, 'ros2_workspace', 'install')

    for candidate in ('setup.bash', 'setup.sh'):
        script = os.path.join(install_dir, candidate)
        if os.path.isfile(script):
            break
    else:
        print('⚠  Workspace setup script not found — launching with current environment')
        return dict(os.environ)

    try:
        result = subprocess.run(
            ['bash', '-c', f"source '{script}' && env -0"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(f'⚠  Failed to source workspace setup: {result.stderr.strip()}')
            return dict(os.environ)

        env = dict(os.environ)
        for entry in result.stdout.split('\0'):
            if '=' in entry:
                k, _, v = entry.partition('=')
                env[k] = v
        print(f'✓ Workspace sourced for scenario: {script}')
        return env
    except subprocess.TimeoutExpired:
        print('⚠  Timeout sourcing workspace setup script')
        return dict(os.environ)
    except Exception as e:
        print(f'⚠  Error sourcing workspace setup script: {e}')
        return dict(os.environ)


def _workspace_guard():
    """
    Return a 503-ready error dict if the workspace build dir is absent or
    empty, or None when ready.  Works even before WorkspaceMonitor is started
    by falling back to a direct filesystem check using WORKSPACE_ROOT.
    """
    if workspace_monitor is not None:
        return workspace_monitor.check_build_ready()

    workspace_root = os.environ.get(
        'WORKSPACE_ROOT',
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    )
    build_dir = os.path.join(workspace_root, 'ros2_workspace', 'build')

    if not os.path.isdir(build_dir):
        return {
            "success": False,
            "error": "workspace_not_built",
            "message": (
                f"ROS 2 workspace build directory not found: {build_dir}. "
                "Run `colcon build` inside ros2_workspace to fix this."
            ),
        }

    entries = [e for e in os.scandir(build_dir) if not e.name.startswith('.')]
    if not entries:
        return {
            "success": False,
            "error": "workspace_not_built",
            "message": (
                f"ROS 2 workspace build directory is empty: {build_dir}. "
                "Run `colcon build` inside ros2_workspace to fix this."
            ),
        }

    return None


scenario_manager = ScenarioManager()
bag_manager = None


@app.route('/')
def index():
    return render_template('index.html', host=request.host)



@app.route('/api_reference.md')
def serve_api_reference():
    try:
        return send_from_directory(os.path.dirname(__file__), 'api_reference.md')
    except FileNotFoundError:
        return "API reference file not found", 404


@app.route('/goal_picker')
def goal_picker():
    return render_template('goal_picker.html')


@app.route('/api/status')
def api_status():
    ws_status = workspace_monitor.get_status() if workspace_monitor else None
    build_error = _workspace_guard()
    return jsonify({
        "adore_api": "running",
        "model_checker_available": model_check_blueprint is not None,
        "ros_marshaller_available": ROSMarshaller is not None,
        "bag_recording_available": bag_manager is not None,
        "workspace": ws_status,
        "workspace_ready": build_error is None,
    })


@app.route('/api/workspace/status')
def workspace_status():
    if workspace_monitor is None:
        return jsonify({"monitoring": False, "message": "Workspace monitor not initialised"}), 503
    status = workspace_monitor.get_status()
    build_error = workspace_monitor.check_build_ready()
    status["ready"] = build_error is None
    if build_error:
        status["error"] = build_error["message"]
    return jsonify(status)


@app.route('/api/scenario/start', methods=['POST'])
def start_scenario_route():
    err = _workspace_guard()
    if err:
        return jsonify(err), 503

    data = request.get_json(silent=True) or {}

    scenario_input = data.get(
        'scenario', "simulation_scenarios/simulation_test.launch.py"
    )
    is_file = data.get('is_file', True)
    model_check_enabled = data.get('model_check_enabled', False)
    if isinstance(model_check_enabled, str):
        model_check_enabled = model_check_enabled.lower() == 'true'
    model_check_config = data.get('model_check_config', 'config/default.yaml')

    if not scenario_input:
        return jsonify({"success": False, "message": "No scenario provided"}), 400

    if model_check_enabled:
        result = scenario_manager.start_model_check_then_scenario(
            scenario_input,
            is_file,
            model_check_enabled,
            model_check_config,
        )
    else:
        result = scenario_manager.start_scenario(scenario_input, is_file)

    return jsonify(result)


@app.route('/api/scenario/stop', methods=['POST'])
def stop_scenario():
    result = scenario_manager.stop_scenario()
    return jsonify(result)


@app.route('/api/scenario/restart', methods=['POST'])
def restart_scenario():
    err = _workspace_guard()
    if err:
        return jsonify(err), 503
    result = scenario_manager.restart_scenario()
    return jsonify(result)


@app.route('/api/scenario/halt', methods=['POST'])
def halt_scenarios():
    result = scenario_manager.halt_all()
    return jsonify(result)


@app.route('/api/scenario/output')
def get_output():
    lines = request.args.get('lines', 1000, type=int)
    output = scenario_manager.get_output(lines)
    return jsonify({"output": output})


@app.route('/api/scenario/status')
def get_status():
    status = scenario_manager.get_status()
    return jsonify(status)


@app.route('/api/scenario/get')
def get_scenarios():
    scenarios = scenario_manager.get_available_scenarios()
    return jsonify({"scenarios": scenarios})


@app.route('/api/scenario/content/<path:scenario_path>')
def get_scenario_content(scenario_path):
    result = scenario_manager.get_scenario_content(scenario_path)
    return jsonify(result)


@app.route('/api/scenario/save', methods=['POST'])
def save_scenario():
    data = request.json
    scenario_name = data.get('name')
    content = data.get('content')

    if not scenario_name or not content:
        return jsonify({"success": False, "message": "Name and content are required"}), 400

    result = scenario_manager.save_scenario(scenario_name, content)
    return jsonify(result)


@app.route('/api/scenario/loop', methods=['POST'])
def set_loop_mode():
    data = request.json
    enabled = data.get('enabled', False)
    delay = data.get('delay', 0)
    runtime = data.get('runtime', 60)
    model_check_enabled = data.get('model_check_enabled', True)
    model_check_config = data.get('model_check_config', 'config/default.yaml')

    scenario_manager.set_loop_mode(
        enabled, delay, runtime, model_check_enabled, model_check_config)
    return jsonify({"success": True, "message": f"Loop mode {'enabled' if enabled else 'disabled'}"})


@app.route('/api/bag/start', methods=['POST'])
def start_bag_recording():
    if not bag_manager:
        return jsonify({"success": False, "message": "Bag recording not available - log directory not configured"}), 500

    data = request.json
    duration = data.get('duration')
    topics = data.get('topics', [])

    scenario_name = None
    scenario_status = scenario_manager.get_status()
    if scenario_status['scenario']:
        scenario_name = scenario_status['scenario']

    result = bag_manager.start_recording(
        duration=duration, topics=topics, scenario_name=scenario_name)
    return jsonify(result)


@app.route('/api/bag/stop', methods=['POST'])
def stop_bag_recording():
    if not bag_manager:
        return jsonify({"success": False, "message": "Bag recording not available"}), 500

    result = bag_manager.stop_recording()
    return jsonify(result)


@app.route('/api/bag/status')
def get_bag_status():
    if not bag_manager:
        return jsonify({"success": False, "message": "Bag recording not available"}), 500

    status = bag_manager.get_recording_status()
    return jsonify(status)


@app.route('/api/bag/list')
def list_bag_recordings():
    if not bag_manager:
        return jsonify({"success": False, "message": "Bag recording not available"}), 500

    result = bag_manager.list_recorded_bags()
    return jsonify(result)


@app.route('/api/bag/output')
def get_bag_output():
    if not bag_manager:
        return jsonify({"success": False, "message": "Bag recording not available"}), 500

    lines = request.args.get('lines', 100, type=int)
    output = bag_manager.get_recording_output(lines)
    return jsonify({"output": output})


@app.route('/api/positions/set', methods=['POST'])
def set_positions():
    global stored_positions
    data = request.json

    if 'start' in data:
        stored_positions['start'] = data['start']
    if 'goal' in data:
        stored_positions['goal'] = data['goal']

    return jsonify({"success": True, "message": "Positions stored successfully"})


@app.route('/api/positions/get')
def get_positions():
    return jsonify(stored_positions)


@app.route('/api/positions/clear', methods=['POST'])
def clear_positions():
    global stored_positions
    stored_positions = {'start': None, 'goal': None}
    return jsonify({"success": True, "message": "Positions cleared"})


@app.route('/api/topic/subscribe')
def subscribe_to_topic():
    if not ROSMarshaller:
        return jsonify({"success": False, "message": "ROS functionality not available"}), 500

    topic = request.args.get('topic')
    limit = request.args.get('limit', 10, type=int)
    wait_timeout = request.args.get('wait_timeout', 1.0, type=float)

    if not topic:
        return jsonify({"success": False, "message": "Topic parameter is required"}), 400

    try:
        is_new_subscriber = topic not in topic_manager.subscribers

        messages = topic_manager.get_or_create_subscriber(topic, limit)

        if not messages and is_new_subscriber and wait_timeout > 0:
            import time
            wait_interval = 0.1
            waited = 0

            while waited < wait_timeout:
                time.sleep(wait_interval)
                waited += wait_interval

                with topic_manager.lock:
                    if topic in topic_manager.subscribers:
                        current_messages = list(
                            topic_manager.subscribers[topic]['messages'])
                        if current_messages:
                            messages = current_messages[-limit:
                                                        ] if limit > 0 else current_messages
                            break

        return jsonify({
            "success": True,
            "topic": topic,
            "messages": messages,
            "count": len(messages),
            "new_subscriber": is_new_subscriber,
            "waited": waited if 'waited' in locals() else 0
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to subscribe to topic: {str(e)}"}), 500


@app.route('/api/topic/publish', methods=['POST'])
def publish_to_topic():
    if not ROSMarshaller:
        return jsonify({"success": False, "message": "ROS functionality not available"}), 500

    data = request.json

    if not data:
        return jsonify({"success": False, "message": "JSON data is required"}), 400

    topic = data.get('topic')
    message_data = data.get('data')
    datatype = data.get('datatype')

    if not topic or not message_data:
        return jsonify({"success": False, "message": "Topic and data are required"}), 400

    try:
        topic_manager.get_publisher(topic)

        if not datatype:
            datatype = ROSMarshaller.get_datatype(topic)
            if not datatype:
                return jsonify({"success": False, "message": f"Could not determine datatype for topic {topic}. Please specify datatype parameter."}), 400

        ROSMarshaller.publish(json.dumps(message_data), topic, datatype)

        return jsonify({
            "success": True,
            "message": f"Message published to {topic}",
            "topic": topic,
            "datatype": datatype
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to publish message: {str(e)}"}), 500


@app.route('/api/ros2/nodes/running')
def list_running_nodes():
    try:
        nodes = ROS2Tools.get_nodes() if ROS2Tools else []
        return jsonify({"success": True, "running_nodes": nodes, "count": len(nodes)})
    except Exception as e:
        return jsonify({"success": False, "running_nodes": [], "count": 0, "message": str(e)}), 500


@app.route('/api/topic/list')
def list_active_topics():
    try:
        stats = topic_manager.get_stats()
        topic_datatypes = {}
        system_topics = []
        if ROS2Tools:
            try:
                topic_datatypes = ROS2Tools.get_topics()
                system_topics = sorted(topic_datatypes.keys())
            except Exception as e:
                logging.warning(f"ROS2Tools.get_topics() failed: {e}")
        if not system_topics:
            # Fallback: raw subprocess when ros2tools unavailable or returned nothing
            try:
                r = subprocess.run(["ros2", "topic", "list", "-t"],
                                   capture_output=True, text=True, timeout=8)
                for line in r.stdout.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    if " [" in line:
                        topic, rest = line.split(" [", 1)
                        topic = topic.strip()
                        system_topics.append(topic)
                        topic_datatypes[topic] = rest.rstrip("]").strip()
                    else:
                        system_topics.append(line)
                system_topics.sort()
            except Exception:
                pass
        return jsonify({
            "success": True,
            "managed_topics": stats,
            "system_topics": system_topics,
            "topic_datatypes": topic_datatypes
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to list topics: {str(e)}"}), 500


@app.route('/api/topic/info/<path:topic_name>')
def get_topic_info(topic_name):
    try:
        if not topic_name.startswith('/'):
            topic_name = '/' + topic_name

        datatype = None
        if ROS2Tools:
            datatype = ROS2Tools.get_topic_datatype(topic_name)
        elif ROSMarshaller:
            datatype = ROSMarshaller.get_datatype(topic_name)

        managed = False
        with topic_manager.lock:
            managed = topic_name in topic_manager.subscribers or topic_name in topic_manager.publishers

        return jsonify({
            "success": True,
            "topic": topic_name,
            "datatype": datatype,
            "managed": managed
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to get topic info: {str(e)}"}), 500


@app.route('/api/scenario/start/model_checked', methods=['POST'])
def start_scenario_model_checked():
    """
    Start a scenario with model checking and return results when complete.

    This endpoint provides a synchronous interface for running a scenario with model checking.
    It starts the model checker, runs the scenario for the specified duration, waits for
    model checking to complete, and returns both scenario and model checking results.

    Args:
        None (uses JSON payload from request)

    Request JSON Parameters:
        scenario (str, optional): Name of the launch file to run. 
            Default: "adore_scenarios/simulation_scenarios/simulation_test.launch.py"
        duration (int|float, optional): How long to run the scenario in seconds.
            Must be a positive number. Default: 5

    Returns:
        flask.Response: JSON response with the following structure:

        Success response (200):
        {
            "success": true,
            "scenario": str,           # Name of scenario that was run
            "duration": float,         # Duration the scenario ran for
            "scenario_result": dict,   # Result from starting the scenario
            "model_check_result": dict,# Model checking results (if available)
            "model_check_available": bool  # Whether model checking was available
        }

        Error response (400 or 200 with success=false):
        {
            "success": false,
            "error": str,              # Error message describing what went wrong
            "scenario": str,           # Name of scenario attempted
            "duration": float          # Requested duration
        }

    Raises:
        None (all exceptions are caught and returned as error responses)

    Notes:
        - This is a blocking endpoint that waits for both scenario and model checking to complete
        - The endpoint will halt all running scenarios before starting the new one
        - Model checking runs alongside the scenario and may take additional time after scenario ends
        - If model checking is not available, the scenario will still run without it
        - Any infinity or NaN values in model check results are sanitized to null for valid JSON

    Example:
        >>> import requests
        >>> response = requests.post(
        ...     'http://localhost:8888/api/scenario/start/model_checked',
        ...     json={'scenario': 'test.launch.py', 'duration': 10}
        ... )
        >>> result = response.json()
        >>> if result['success']:
        ...     print(f"Model check passed: {result['model_check_result']['results']['SUMMARY']['overall_result']}")
    """
    data = request.json or {}
    scenario = data.get(
        'scenario', 'simulation_scenarios/simulation_test.launch.py')
    duration = data.get('duration', 5)

    if not isinstance(duration, (int, float)) or duration <= 0:
        return jsonify({
            "success": False,
            "error": "Duration must be a positive number",
            "scenario": scenario,
            "duration": duration
        }), 400

    try:
        # Stop any existing scenarios first
        scenario_manager.halt_all()
        time.sleep(2)

        # Reset model check state
        with scenario_manager.model_check_lock if hasattr(scenario_manager, 'model_check_lock') else threading.Lock():
            scenario_manager.waiting_for_model_check = False
            scenario_manager.current_model_check_run_id = None

        if model_check_blueprint is None:
            # Just run scenario for the duration without model checking
            print("Model checker not available, running scenario only")
            scenario_result = scenario_manager.start_scenario(
                scenario, is_file=True)
            if not scenario_result["success"]:
                return jsonify({
                    "success": False,
                    "error": f"Failed to start scenario: {scenario_result['message']}",
                    "scenario": scenario,
                    "duration": duration,
                    "scenario_result": scenario_result
                })

            time.sleep(duration)
            scenario_manager.halt_all()
            return jsonify({
                "success": True,
                "scenario": scenario,
                "duration": duration,
                "scenario_result": scenario_result,
                "model_check_available": False,
                "message": "Scenario completed without model checking (model checker not available)"
            })

        # Set the model check configuration for the duration
        scenario_manager.default_runtime = duration
        scenario_manager.model_check_enabled = True
        scenario_manager.model_check_config = 'config/default.yaml'

        print(
            f"Starting model checking and scenario for {duration} seconds...")

        # Use the synchronized method
        result = scenario_manager.start_model_check_then_scenario(
            scenario,
            is_file=True,
            model_check_enabled=True,
            model_check_config='config/default.yaml'
        )

        if not result["success"]:
            return jsonify({
                "success": False,
                "error": f"Failed to start scenario with model checking: {result['message']}",
                "scenario": scenario,
                "duration": duration,
                "scenario_result": result
            })

        print(f"Scenario started, waiting {duration} seconds...")
        time.sleep(duration)

        # Get the run ID before waiting
        print(f"Scenario start result: {result}")
        current_run_id = result['model_check_result']['run_id']
        print(f"Current model check run ID: {current_run_id}")

        if current_run_id is None:
            print("Warning: No model check run ID found")
            scenario_manager.halt_all()
            return jsonify({
                "success": False,
                "error": "Model checking was enabled but no run ID was created",
                "scenario": scenario,
                "duration": duration,
                "scenario_result": result,
                "model_check_available": True,
                "debug_info": {
                    "waiting_for_model_check": getattr(scenario_manager, 'waiting_for_model_check', None),
                    "model_check_enabled": getattr(scenario_manager, 'model_check_enabled', None)
                }
            })

        # Wait for model checking to complete with better monitoring
        print(
            f"Waiting for model checking to complete (run ID: {current_run_id})...")
        max_wait_time = duration + 60  # Give model checking extra time
        wait_start = time.time()
        last_status = None

        while time.time() - wait_start < max_wait_time:
            try:
                # Check model check status directly
                with app.test_client() as client:
                    status_response = client.get(
                        f'/api/model_check/result/{current_run_id}')

                    if status_response.status_code == 200:
                        status_data = status_response.get_json()
                        current_status = status_data.get('status', 'unknown')

                        if current_status != last_status:
                            print(f"Model check status: {current_status}")
                            last_status = current_status

                        if current_status in ['completed', 'failed', 'cancelled', 'error']:
                            print(
                                f"Model checking finished with status: {current_status}")
                            break
                    elif status_response.status_code == 404:
                        print(f"Model check run {current_run_id} not found")
                        break
                    else:
                        print(
                            f"Error checking status: HTTP {status_response.status_code}")

            except Exception as e:
                print(f"Error checking model check status: {e}")

            time.sleep(2)

        # Get final results with detailed error checking
        model_check_result = None
        try:
            print(f"Fetching final results for run ID: {current_run_id}")
            with app.test_client() as client:
                response = client.get(
                    f'/api/model_check/result/{current_run_id}')
                print(f"Result fetch response code: {response.status_code}")

                if response.status_code == 200:
                    model_check_result = response.get_json()
                    print(
                        f"Got model check results with status: {model_check_result.get('status')}")

                    # Check if results contain actual analysis data
                    if model_check_result and 'results' in model_check_result:
                        if model_check_result['results']:
                            model_check_result['results'] = sanitize_infinity(
                                model_check_result['results'])
                            print("Model check results contain analysis data")
                        else:
                            print("Warning: Model check results are empty")
                    else:
                        print("Warning: Model check results missing 'results' field")

                elif response.status_code == 404:
                    print(f"Model check run {current_run_id} not found")
                else:
                    print(
                        f"Failed to get model check results: HTTP {response.status_code}")
                    response_text = response.get_data(as_text=True)
                    print(f"Response body: {response_text}")

        except Exception as e:
            print(f"Exception getting final model check results: {e}")
            import traceback
            traceback.print_exc()

        # Halt everything
        scenario_manager.halt_all()

        # Provide detailed response based on what we got
        if not model_check_result:
            # Check if we can get any debug info from the model checker
            debug_info = {}
            try:
                with app.test_client() as client:
                    debug_response = client.get('/api/model_check/status')
                    if debug_response.status_code == 200:
                        debug_info = debug_response.get_json()
            except:
                pass

            return jsonify({
                "success": False,
                "error": "Model checking did not produce results",
                "scenario": scenario,
                "duration": duration,
                "scenario_result": result,
                "model_check_available": True,
                "model_check_run_id": current_run_id,
                "debug_info": debug_info,
                "waited_time": time.time() - wait_start
            })

        # Check if we got meaningful results
        if not model_check_result.get('results'):
            return jsonify({
                "success": False,
                "error": "Model checking completed but produced no analysis results",
                "scenario": scenario,
                "duration": duration,
                "scenario_result": result,
                "model_check_available": True,
                "model_check_result": model_check_result
            })

        return jsonify({
            "success": True,
            "scenario": scenario,
            "duration": duration,
            "scenario_result": result,
            "model_check_result": model_check_result,
            "model_check_available": True
        })

    except Exception as e:
        print(f"Unexpected error in start_scenario_model_checked: {e}")
        import traceback
        traceback.print_exc()

        try:
            scenario_manager.halt_all()
        except:
            pass

        return jsonify({
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "scenario": scenario,
            "duration": duration
        })


@app.route('/model-checker/dashboard')
def model_check_dashboard():
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        # Dev layout: tools/adore_api/../../vendor/adore_model_checker/
        os.path.normpath(os.path.join(here, '..', '..', 'vendor', 'adore_model_checker', 'adore_model_checker_dashboard.html')),
        # Dev layout: inside the package subdir
        os.path.normpath(os.path.join(here, '..', '..', 'vendor', 'adore_model_checker', 'adore_model_checker', 'adore_model_checker_dashboard.html')),
        os.path.join(here, 'adore_model_checker_dashboard.html'),
    ]
    html = None
    for path in candidates:
        if os.path.exists(path):
            with open(path, 'r') as fh:
                html = fh.read()
            break

    if html is None:
        try:
            from importlib.resources import files
            resource = files('adore_model_checker').joinpath('adore_model_checker_dashboard.html')
            if resource.is_file():
                html = resource.read_text(encoding='utf-8')
        except Exception:
            pass

    if html is None:
        return "Model Checker dashboard not found", 404

    inject = (
        "<script>"
        "window.ADORE_API_BASE = window.location.protocol + '//' + window.location.host + '/api/model_checker';"
        "</script>"
    )
    html = html.replace('</head>', inject + '\n</head>', 1)
    return Response(html, mimetype='text/html')


_mc_continuous_disabled = {'props': set()}


@app.route('/api/model_checker/continuous/disabled', methods=['POST'])
def mc_set_disabled():
    data = request.get_json(silent=True) or {}
    _mc_continuous_disabled['props'] = set(data.get('disabled_propositions', []))
    return jsonify({'ok': True})


@app.route('/api/model_checker/continuous/violations/filtered')
def mc_filtered_violations():
    from flask import current_app
    fn = current_app.view_functions.get('model_check_blueprint.continuous_violations')
    if fn is None:
        return jsonify({'error': 'Continuous monitoring not available'}), 404
    try:
        resp = fn()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    disabled = _mc_continuous_disabled['props']
    if not disabled:
        return resp

    import json as _json
    try:
        body = _json.loads(resp.get_data(as_text=True))
        body['violations'] = [v for v in body.get('violations', [])
                              if v.get('proposition') not in disabled]
        body['count'] = len(body['violations'])
        return jsonify(body)
    except Exception:
        return resp


@app.route('/api/model_checker/continuous/<path:subpath>', methods=['GET', 'POST', 'OPTIONS'])
def proxy_continuous(subpath):
    from flask import current_app
    parts = subpath.split('/')
    base = parts[0]
    endpoint = f'model_check_blueprint.continuous_{base}'
    fn = current_app.view_functions.get(endpoint)
    if fn is None:
        return jsonify({'error': f'Unknown endpoint: /continuous/{subpath}'}), 404
    try:
        return fn(*parts[1:]) if len(parts) > 1 else fn()
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/model_checker/result/<int:run_id>')
def proxy_result(run_id):
    from flask import current_app
    fn = current_app.view_functions.get('model_check_blueprint.get_result')
    if fn is None:
        return jsonify({'error': 'Result endpoint not available'}), 404
    try:
        return fn(run_id)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _mc_config_dir():
    candidates = [
        os.environ.get('ADORE_CONFIG_DIR'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     '..', '..', 'vendor', 'adore_model_checker', 'config'),
    ]
    for path in candidates:
        if path:
            os.makedirs(path, exist_ok=True)
            _mc_seed_default(path)
            return path
    raise RuntimeError("Cannot determine model checker config directory")


def _mc_seed_default(config_dir):
    """Copy the canonical package default.yaml into config_dir if not already present."""
    dest = os.path.join(config_dir, 'default.yaml')
    if os.path.exists(dest):
        return

    content = _mc_load_package_default_yaml()
    if content:
        with open(dest, 'w') as f:
            f.write(content)
        return

    raise RuntimeError(
        "Cannot locate adore_model_checker/config/default.yaml — "
        "ensure the package is installed correctly."
    )


def _mc_load_package_default_yaml():
    """Return the canonical default.yaml content from the package, or None on failure."""
    try:
        from importlib.resources import files
        resource = files('adore_model_checker').joinpath('config/default.yaml')
        if resource.is_file():
            return resource.read_text(encoding='utf-8')
    except Exception:
        pass

    here = os.path.dirname(os.path.abspath(__file__))
    for candidate in [
        os.path.normpath(os.path.join(here, '..', '..', 'vendor', 'adore_model_checker', 'adore_model_checker', 'config', 'default.yaml')),
        os.path.normpath(os.path.join(here, '..', '..', 'vendor', 'adore_model_checker', 'config', 'default.yaml')),
    ]:
        if os.path.exists(candidate):
            with open(candidate, 'r') as f:
                return f.read()

    return None


# ── ROS Workspace Build Management ──────────────────────────────────────────

_workspace_build_procs: dict = {}
_workspace_build_broadcaster = _LogBroadcaster(maxlen=5000)


def _get_ros2_workspace_dir():
    workspace_root = os.environ.get(
        'WORKSPACE_ROOT',
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    )
    return os.path.join(workspace_root, 'ros2_workspace')


@app.route('/api/ros_workspace/status')
def ros_workspace_status():
    ws_dir = _get_ros2_workspace_dir()
    build_dir = os.path.join(ws_dir, 'build')
    install_dir = os.path.join(ws_dir, 'install')
    src_dir = os.path.join(ws_dir, 'src')
    makefile_exists = os.path.isfile(os.path.join(ws_dir, 'Makefile'))
    running = {k: (p.poll() is None) for k, p in _workspace_build_procs.items()}

    # Quick package counts without full mtime scan
    total_pkgs = 0
    built_pkgs = 0
    if os.path.isdir(src_dir):
        for pkg_path in _find_packages(src_dir):
            total_pkgs += 1
            if os.path.isdir(os.path.join(build_dir, os.path.basename(pkg_path))):
                built_pkgs += 1

    return jsonify({
        'workspace_dir': ws_dir,
        'workspace_exists': os.path.isdir(ws_dir),
        'makefile_exists': makefile_exists,
        'build_dir_exists': os.path.isdir(build_dir),
        'install_dir_exists': os.path.isdir(install_dir),
        'running': running,
        'total_packages': total_pkgs,
        'built_packages': built_pkgs,
    })


# Extensions and directories to skip when scanning source mtimes
_SRC_SKIP_DIRS = frozenset({'.git', '__pycache__', '.cache', 'node_modules', '.eggs', 'dist', 'build', 'install', 'log'})
_SRC_SKIP_EXTS = frozenset({'.pyc', '.pyo'})

# Track packages colcon has reported as unknown so we can exclude them from auto-rebuild
_colcon_unknown_packages: set = set()


def _max_mtime(root: str, skip_dirs: frozenset) -> float:
    best = 0.0
    try:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames
                           if d not in skip_dirs and not d.endswith('.egg-info')]
            for fname in filenames:
                if os.path.splitext(fname)[1] in _SRC_SKIP_EXTS:
                    continue
                try:
                    mt = os.stat(os.path.join(dirpath, fname)).st_mtime
                    if mt > best:
                        best = mt
                except OSError:
                    pass
    except OSError:
        pass
    return best


def _find_packages(src_dir: str) -> list:
    """Recursively find all directories containing package.xml under src_dir."""
    found = []
    try:
        for dirpath, dirnames, filenames in os.walk(src_dir):
            # Don't descend into hidden dirs or known non-source dirs
            dirnames[:] = sorted(d for d in dirnames
                                 if not d.startswith('.') and d not in ('build', 'install', 'log', '__pycache__'))
            if 'package.xml' in filenames:
                found.append(dirpath)
                # Don't recurse into a package — packages don't nest inside packages
                dirnames.clear()
    except OSError:
        pass
    return found


def _package_info(name: str, src_path: str, build_dir: str) -> dict:
    pkg_build_dir = os.path.join(build_dir, name)
    built = os.path.isdir(pkg_build_dir)
    stale = False
    if built:
        src_mtime = _max_mtime(src_path, _SRC_SKIP_DIRS)
        build_mtime = _max_mtime(pkg_build_dir, frozenset())
        stale = src_mtime > build_mtime and src_mtime > 0
    return {
        'name': name,
        'path': src_path,
        'built': built,
        'stale': stale,
        'colcon_unknown': name in _colcon_unknown_packages,
    }


@app.route('/api/ros_workspace/packages')
def ros_workspace_packages():
    ws_dir = _get_ros2_workspace_dir()
    src_dir = os.path.join(ws_dir, 'src')
    build_dir = os.path.join(ws_dir, 'build')

    packages = []
    if os.path.isdir(src_dir):
        for pkg_path in _find_packages(src_dir):
            name = os.path.basename(pkg_path)
            packages.append(_package_info(name, pkg_path, build_dir))
        packages.sort(key=lambda p: p['name'])

    built_count = sum(1 for p in packages if p['built'])
    return jsonify({'packages': packages, 'total': len(packages), 'built_count': built_count})


@app.route('/api/ros_workspace/build_package', methods=['POST'])
def ros_workspace_build_package():
    data = request.get_json(silent=True) or {}
    package = data.get('package', '').strip()
    if not package or '/' in package or package.startswith('.'):
        return jsonify({'success': False, 'message': 'Invalid package name'}), 400
    return jsonify(_run_workspace_make(f'__pkg__{package}'))


def _run_workspace_make(target: str):
    ws_dir = _get_ros2_workspace_dir()
    if not os.path.isdir(ws_dir):
        return {'success': False, 'message': f'Workspace directory not found: {ws_dir}'}
    existing = _workspace_build_procs.get(target)
    if existing and existing.poll() is None:
        return {'success': False, 'message': f'{target} already running'}

    # __pkg__<name> targets use colcon instead of make
    if target.startswith('__pkg__'):
        package = target[len('__pkg__'):]
        cmd = ['colcon', 'build', '--packages-select', package]
        label = f'colcon build --packages-select {package}'
    else:
        cmd = ['make', target]
        label = f'make {target}'

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=ws_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
        )
        _workspace_build_procs[target] = proc

        def _stream():
            _workspace_build_broadcaster.write(f'=== {label} started ===', 'stdout')
            unknown_warned = False
            for line in iter(proc.stdout.readline, ''):
                if line:
                    stripped = line.rstrip()
                    _workspace_build_broadcaster.write(stripped, 'stdout')
                    # Detect colcon "ignoring unknown package '<name>'" and record it
                    if 'ignoring unknown package' in stripped and target.startswith('__pkg__'):
                        pkg_name = target[len('__pkg__'):]
                        _colcon_unknown_packages.add(pkg_name)
                        unknown_warned = True
            rc = proc.wait()
            _workspace_build_broadcaster.write(
                f'=== {label} exited (rc={rc}) ===',
                'stdout' if rc == 0 else 'stderr'
            )

        threading.Thread(target=_stream, daemon=True).start()
        return {'success': True, 'message': f'{label} started'}
    except Exception as e:
        return {'success': False, 'message': str(e)}


@app.route('/api/ros_workspace/clean', methods=['POST'])
def ros_workspace_clean():
    return jsonify(_run_workspace_make('clean'))


@app.route('/api/ros_workspace/ccache/stats')
def ccache_stats():
    try:
        r = subprocess.run(['ccache', '-s', '-v'], capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            r2 = subprocess.run(['ccache', '-s'], capture_output=True, text=True, timeout=10)
            raw = r2.stdout.strip() or r2.stderr.strip()
            return jsonify({'available': True, 'raw': raw, 'verbose': False})
        return jsonify({'available': True, 'raw': r.stdout.strip(), 'verbose': True})
    except FileNotFoundError:
        return jsonify({'available': False, 'message': 'ccache not found'})
    except Exception as e:
        return jsonify({'available': False, 'message': str(e)}), 500


@app.route('/api/ros_workspace/ccache/clear', methods=['POST'])
def ccache_clear():
    try:
        r = subprocess.run(['ccache', '-C'], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return jsonify({'success': False, 'message': r.stderr.strip() or 'ccache -C failed'}), 500
        return jsonify({'success': True, 'message': r.stdout.strip() or 'Cache cleared'})
    except FileNotFoundError:
        return jsonify({'success': False, 'message': 'ccache not found'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/ros_workspace/build', methods=['POST'])
def ros_workspace_build():
    return jsonify(_run_workspace_make('build'))


@app.route('/api/ros_workspace/log/stream')
def ros_workspace_log_stream():
    def generate():
        q = _workspace_build_broadcaster.subscribe()
        try:
            yield 'retry: 3000\n\n'
            while True:
                try:
                    msg = q.get(timeout=20)
                    yield f'data: {msg}\n\n'
                except queue.Empty:
                    yield ': keepalive\n\n'
        except GeneratorExit:
            pass
        finally:
            _workspace_build_broadcaster.unsubscribe(q)

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


# ── ROS Topics extended API ──────────────────────────────────────────────────

@app.route('/api/topic/hz', methods=['POST'])
def topic_hz():
    data = request.get_json(silent=True) or {}
    topic = data.get('topic', '').strip()
    if not topic:
        return jsonify({'success': False, 'message': 'topic required'}), 400
    if not ROS2Tools:
        return jsonify({'success': False, 'message': 'ros2tools not available'}), 500
    try:
        output = ROS2Tools.topic_hz(topic)
        return jsonify({'success': True, 'topic': topic, 'output': output})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/topic/echo', methods=['POST'])
def topic_echo_once():
    data = request.get_json(silent=True) or {}
    topic = data.get('topic', '').strip()
    if not topic:
        return jsonify({'success': False, 'message': 'topic required'}), 400

    if ROSMarshaller:
        received = []
        done = threading.Event()

        def _cb(json_str, _topic, _dtype):
            if not done.is_set():
                received.append(json_str)
                done.set()

        try:
            sub = ROSMarshaller.subscribe(topic, _cb)
            done.wait(timeout=10)
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

        if received:
            try:
                msg = json.loads(received[0])
                msg.pop('topic', None)
                msg.pop('datatype', None)
                return jsonify({'success': True, 'topic': topic, 'msg': msg})
            except Exception:
                pass

        return jsonify({'success': False, 'message': 'Timeout waiting for message'}), 504

    try:
        result = subprocess.run(
            ['ros2', 'topic', 'echo', '--once', topic],
            capture_output=True, text=True, timeout=10
        )
        raw = result.stdout.strip() or result.stderr.strip()
        return jsonify({'success': True, 'topic': topic, 'raw': raw})
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'message': 'Timeout waiting for message'}), 504
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/topic/empty_message', methods=['POST'])
def topic_empty_message():
    data = request.get_json(silent=True) or {}
    datatype = data.get('datatype', '').strip()
    if not datatype:
        return jsonify({'success': False, 'message': 'datatype required'}), 400

    # Try ros2tools first (handles fallback to interface show internally)
    if ROS2Tools:
        try:
            proto = ROS2Tools.get_interface_proto(datatype)
            if proto and isinstance(proto, dict):
                return jsonify({'success': True, 'datatype': datatype, 'msg': proto})
        except Exception as e:
            logging.warning(f'ROS2Tools.get_interface_proto failed: {e}')

    # Direct subprocess: try ros2 interface proto then fall back to interface show
    import yaml as _yaml

    def _build_proto_from_show(dtype):
        r2 = subprocess.run(
            ['ros2', 'interface', 'show', dtype],
            capture_output=True, text=True, timeout=20
        )
        if r2.returncode != 0 or not r2.stdout.strip():
            return None
        return _parse_interface_to_proto(r2.stdout.strip())

    def _parse_interface_to_proto(text):
        """Build a zero-value dict from ros2 interface show output."""
        PRIM = {
            'bool': False, 'byte': 0, 'char': 0,
            'float32': 0.0, 'float64': 0.0,
            'int8': 0, 'uint8': 0, 'int16': 0, 'uint16': 0,
            'int32': 0, 'uint32': 0, 'int64': 0, 'uint64': 0,
            'string': '', 'wstring': '',
        }
        result = {}
        lines = [l for l in text.splitlines() if l.strip() and not l.strip().startswith('#')]
        for line in lines:
            if line.startswith(' ') or line.startswith('	'):
                continue  # skip nested lines — handled by ros2tools parse
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            dtype_part, label = parts[0], parts[1]
            if '=' in label or '=' in dtype_part:
                continue  # constant
            is_array = '[]' in dtype_part or (len(parts) > 2 and '[' in parts[0])
            base_type = dtype_part.replace('[]', '').split('[')[0]
            if is_array:
                result[label] = []
            elif base_type in PRIM:
                result[label] = PRIM[base_type]
            else:
                result[label] = {}  # nested object placeholder
        return result if result else None

    try:
        r = subprocess.run(
            ['ros2', 'interface', 'proto', datatype],
            capture_output=True, text=True, timeout=20
        )
        if r.returncode == 0 and r.stdout.strip():
            parsed = _yaml.safe_load(r.stdout)
            if parsed and isinstance(parsed, dict):
                return jsonify({'success': True, 'datatype': datatype, 'msg': parsed})
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass

    # Last resort: build from interface show
    try:
        proto = _build_proto_from_show(datatype)
        if proto:
            return jsonify({'success': True, 'datatype': datatype, 'msg': proto})
        err = f'Could not build prototype for {datatype}'
        return jsonify({'success': False, 'message': err}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'message': 'Timeout fetching interface'}), 504
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ── Publish session registry ────────────────────────────────────────────────
# Each entry: {'proc': Popen|None, 'stop': Event, 'datatype': str, 'mode': str}
_publish_sessions = {}
_publish_sessions_lock = threading.Lock()

_MSG_STRIP = frozenset(('topic', 'datatype', 'WARNING', 'WARN', 'ERROR', 'INFO', 'DEBUG'))


def _clean_msg(msg):
    if isinstance(msg, dict):
        return {k: v for k, v in msg.items() if k not in _MSG_STRIP}
    return msg


def _resolve_datatype(topic, datatype):
    if datatype:
        return datatype
    dt = ROSMarshaller.get_datatype(topic) if ROSMarshaller else None
    if ROS2Tools and not dt:
        dt = ROS2Tools.get_topic_datatype(topic)
    return dt


def _stop_session(topic):
    """Stop any active publish session for a topic."""
    with _publish_sessions_lock:
        entry = _publish_sessions.pop(topic, None)
    if not entry:
        return
    entry['stop'].set()
    if entry.get('proc'):
        ROSMarshaller.stop_persistent(entry['proc'])


@app.route('/api/topic/publish_timed', methods=['POST'])
def publish_timed():
    if not ROSMarshaller:
        return jsonify({'success': False, 'message': 'ROS functionality not available'}), 500

    data = request.get_json(silent=True) or {}
    topic = data.get('topic', '').strip()
    message_data = data.get('data')
    datatype = data.get('datatype', '').strip()
    frequency = data.get('frequency', 0)
    action = data.get('action', 'publish')

    if action == 'stop':
        _stop_session(topic)
        return jsonify({'success': True, 'message': f'Stopped publishing to {topic}'})

    if not topic or message_data is None:
        return jsonify({'success': False, 'message': 'topic and data required'}), 400

    message_data = _clean_msg(message_data)

    datatype = _resolve_datatype(topic, datatype)
    if not datatype:
        return jsonify({'success': False, 'message': f'Could not determine datatype for {topic}'}), 400

    _stop_session(topic)

    if frequency and float(frequency) > 0:
        hz = float(frequency)
        stop_event = threading.Event()
        try:
            proc = ROSMarshaller.publish_persistent(topic, datatype, message_data, hz)
            with _publish_sessions_lock:
                _publish_sessions[topic] = {'proc': proc, 'stop': stop_event,
                                             'datatype': datatype, 'mode': 'persistent'}
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
        return jsonify({'success': True, 'message': f'Publishing to {topic} at {hz} Hz',
                        'topic': topic, 'datatype': datatype})

    try:
        ROSMarshaller.publish(json.dumps(message_data), topic, datatype)
        return jsonify({'success': True, 'message': f'Published to {topic}',
                        'topic': topic, 'datatype': datatype})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/topic/publish_batch', methods=['POST'])
def publish_batch():
    """
    Publish a sequence of messages (batch/replay) with optional looping.

    JSON body:
      topic     str           target topic
      datatype  str           message type (optional, auto-detected if omitted)
      messages  list[dict]    ordered message list
      frequency float         publish rate Hz (default 1.0)
      loop      bool          repeat the sequence indefinitely (default false)

    Or send raw JSONL as text/plain body (one JSON object per line).
    POST /api/topic/publish_batch?topic=...&datatype=...&frequency=1&loop=true

    Returns immediately; the batch runs in a background thread.
    Use POST /api/topic/publish_timed  {action: stop, topic: ...} to cancel.
    """
    if not ROSMarshaller:
        return jsonify({'success': False, 'message': 'ROS functionality not available'}), 500

    ct = request.content_type or ''
    if 'application/json' in ct:
        data = request.get_json(silent=True) or {}
        topic = data.get('topic', request.args.get('topic', '')).strip()
        datatype = data.get('datatype', request.args.get('datatype', '')).strip()
        messages = data.get('messages', [])
        frequency = float(data.get('frequency', request.args.get('frequency', 1)))
        loop = bool(data.get('loop', request.args.get('loop', 'false').lower() == 'true'))
    else:
        # Raw JSONL body
        topic = request.args.get('topic', '').strip()
        datatype = request.args.get('datatype', '').strip()
        frequency = float(request.args.get('frequency', 1))
        loop = request.args.get('loop', 'false').lower() == 'true'
        messages = []
        for line in request.get_data(as_text=True).splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                messages.append(json.loads(line))
            except Exception:
                pass

    if not topic:
        return jsonify({'success': False, 'message': 'topic required'}), 400
    if not messages:
        return jsonify({'success': False, 'message': 'no messages provided'}), 400

    datatype = _resolve_datatype(topic, datatype)
    if not datatype:
        return jsonify({'success': False, 'message': f'Could not determine datatype for {topic}'}), 400

    messages = [_clean_msg(m) for m in messages]
    interval = 1.0 / frequency if frequency > 0 else 1.0
    _stop_session(topic)

    stop_event = threading.Event()
    with _publish_sessions_lock:
        _publish_sessions[topic] = {'proc': None, 'stop': stop_event,
                                     'datatype': datatype, 'mode': 'batch',
                                     'count': len(messages), 'loop': loop}

    def _batch_loop():
        iteration = 0
        while not stop_event.is_set():
            for msg in messages:
                if stop_event.is_set():
                    break
                try:
                    ROSMarshaller.publish(json.dumps(msg), topic, datatype)
                except Exception as e:
                    logging.error(f'Batch publish error on {topic}: {e}')
                stop_event.wait(interval)
            iteration += 1
            if not loop:
                break
        with _publish_sessions_lock:
            _publish_sessions.pop(topic, None)
        logging.info(f'Batch publish complete: {topic} ({iteration} iteration(s))')

    t = threading.Thread(target=_batch_loop, daemon=True)
    t.start()

    return jsonify({
        'success': True,
        'topic': topic,
        'datatype': datatype,
        'messages': len(messages),
        'frequency': frequency,
        'loop': loop,
        'message': f'Batch started: {len(messages)} messages at {frequency} Hz{"  (looping)" if loop else ""}'
    })


@app.route('/api/topic/publish_status')
def publish_status():
    with _publish_sessions_lock:
        active = {}
        for t, v in list(_publish_sessions.items()):
            proc = v.get('proc')
            alive = (proc is None or proc.poll() is None) and not v['stop'].is_set()
            if alive:
                active[t] = {
                    'datatype': v['datatype'],
                    'mode': v.get('mode', 'unknown'),
                    'loop': v.get('loop', False),
                    'count': v.get('count'),
                }
    return jsonify({'active': active})


@app.route('/api/topic/interface_types')
def list_interface_types():
    """Return all installed ROS message types, merging installed types with active topic datatypes."""
    types = set()

    # Active topic datatypes — always available, fast
    try:
        if ROS2Tools:
            td = ROS2Tools.get_topics()
            types.update(v for v in td.values() if v)
        else:
            r = subprocess.run(['ros2', 'topic', 'list', '-t'],
                               capture_output=True, text=True, timeout=8)
            for line in r.stdout.splitlines():
                if ' [' in line:
                    types.add(line.split(' [', 1)[1].rstrip(']').strip())
    except Exception:
        pass

    # All installed message types
    try:
        if ROS2Tools:
            types.update(ROS2Tools.get_message_types())
        else:
            r = subprocess.run(['ros2', 'interface', 'list', '--only-msgs'],
                               capture_output=True, text=True, timeout=15)
            if r.returncode == 0:
                types.update(t.strip() for t in r.stdout.splitlines() if t.strip())
    except Exception:
        pass

    return jsonify({'types': sorted(types)})


@app.route('/api/topic/stream')
def topic_stream():
    topic = request.args.get('topic', '').strip()
    try:
        max_hz = min(float(request.args.get('max_hz', 10)), 20.0)
    except ValueError:
        max_hz = 10.0
    min_interval = 1.0 / max_hz if max_hz > 0 else 0.1

    if not topic:
        return Response('data: {"error":"topic required"}\n\n', mimetype='text/event-stream')

    if not ROSMarshaller:
        return Response('data: {"error":"ROSMarshaller not available"}\n\n', mimetype='text/event-stream')

    def generate():
        # Per-client queue; callback posts here, generator drains and throttles.
        client_q = queue.Queue(maxsize=200)

        def _callback(json_data, _topic_name, _datatype):
            try:
                parsed = json.loads(json_data) if isinstance(json_data, str) else json_data
                # Drop oldest rather than blocking if client is slow
                if client_q.full():
                    try:
                        client_q.get_nowait()
                    except queue.Empty:
                        pass
                client_q.put_nowait(parsed)
            except Exception:
                pass

        # Reuse the shared TopicManager subscriber so ROSMarshaller only
        # spawns one ros2 topic echo process per topic regardless of how
        # many SSE clients are connected.  We register our callback on top
        # of the existing deque-based subscriber.
        with topic_manager.lock:
            topic_manager.get_or_create_subscriber(topic)
            topic_manager.subscribers[topic]['last_access'] = time.time()
            listeners = topic_manager.subscribers[topic].setdefault('listeners', [])
            listeners.append(_callback)

        try:
            yield 'retry: 3000\n\n'

            pending = None
            dropped = 0
            last_emit = 0.0

            while True:
                # Non-blocking drain — keep only the latest message
                while True:
                    try:
                        item = client_q.get_nowait()
                        if pending is not None:
                            dropped += 1
                        pending = item
                    except queue.Empty:
                        break

                now = time.monotonic()
                if pending is not None and now - last_emit >= min_interval:
                    payload = json.dumps({
                        'msg': pending,
                        'time': datetime.now().strftime('%H:%M:%S'),
                        'dropped': dropped,
                    })
                    pending = None
                    dropped = 0
                    last_emit = now
                    yield f'data: {payload}\n\n'
                else:
                    try:
                        item = client_q.get(timeout=20)
                        if pending is not None:
                            dropped += 1
                        pending = item
                    except queue.Empty:
                        yield ': keepalive\n\n'

        except GeneratorExit:
            pass
        finally:
            with topic_manager.lock:
                if topic in topic_manager.subscribers:
                    listeners = topic_manager.subscribers[topic].get('listeners', [])
                    try:
                        listeners.remove(_callback)
                    except ValueError:
                        pass

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


def _mc_safe_name(name):
    return (name and os.sep not in name and not name.startswith('.')
            and name.lower().endswith(('.yaml', '.yml')))


@app.route('/api/model_checker/configs', methods=['GET'])
def mc_configs_list():
    try:
        cdir = _mc_config_dir()
        configs = []
        for fname in sorted(os.listdir(cdir)):
            if not fname.lower().endswith(('.yaml', '.yml')):
                continue
            fpath = os.path.join(cdir, fname)
            stat = os.stat(fpath)
            configs.append({
                'name': fname,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            })
        return jsonify({'configs': configs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/model_checker/configs/<path:name>', methods=['GET'])
def mc_config_get(name):
    if not _mc_safe_name(name):
        return jsonify({'error': 'Invalid filename'}), 400
    path = os.path.join(_mc_config_dir(), name)
    if not os.path.exists(path):
        return jsonify({'error': 'Not found'}), 404
    with open(path) as f:
        return jsonify({'name': name, 'content': f.read()})


@app.route('/api/model_checker/configs', methods=['POST'])
def mc_config_save():
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    content = data.get('content', '')
    if not _mc_safe_name(name):
        return jsonify({'error': 'Invalid filename'}), 400
    with open(os.path.join(_mc_config_dir(), name), 'w') as f:
        f.write(content)
    return jsonify({'success': True, 'name': name})


@app.route('/api/model_checker/configs/<path:name>', methods=['DELETE'])
def mc_config_delete(name):
    if not _mc_safe_name(name):
        return jsonify({'error': 'Invalid filename'}), 400
    path = os.path.join(_mc_config_dir(), name)
    if not os.path.exists(path):
        return jsonify({'error': 'Not found'}), 404
    os.remove(path)
    return jsonify({'success': True})


def _mc_history_dir():
    candidates = [
        os.environ.get('ADORE_HISTORY_DIR'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     '..', '..', 'vendor', 'adore_model_checker', 'history'),
    ]
    for path in candidates:
        if path:
            os.makedirs(path, exist_ok=True)
            return path
    raise RuntimeError("Cannot determine history directory")


@app.route('/api/model_checker/history')
def mc_history_list():
    try:
        hdir = _mc_history_dir()
        runs = []
        for fname in sorted(os.listdir(hdir), reverse=True):
            if not fname.startswith('run_') or not fname.endswith('.json'):
                continue
            try:
                with open(os.path.join(hdir, fname)) as f:
                    d = json.load(f)
                runs.append({
                    'run_id': d.get('run_id'),
                    'status': d.get('status'),
                    'overall_result': (d.get('results') or {}).get('SUMMARY', {}).get('overall_result'),
                    'config_file': d.get('config_file'),
                    'completed_at': d.get('completed_at'),
                })
            except Exception:
                pass
        return jsonify({'runs': runs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/model_checker/history/<int:run_id>/log')
def mc_history_log(run_id):
    log_path = os.path.join(_mc_history_dir(), f'run_{run_id}.log')
    if not os.path.exists(log_path):
        return jsonify({'log': None})
    with open(log_path) as f:
        return jsonify({'log': f.read()})


@app.route('/api/model_checker/logs/stream')
def mc_logs_stream():
    def generate():
        q = _adore_log_broadcaster.subscribe()
        try:
            yield 'retry: 3000\n\n'
            while True:
                try:
                    msg = q.get(timeout=20)
                    yield f'data: {msg}\n\n'
                except queue.Empty:
                    yield ': keepalive\n\n'
        except GeneratorExit:
            pass
        finally:
            _adore_log_broadcaster.unsubscribe(q)

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


@app.route('/api/model_check/debug', methods=['GET'])
def debug_model_check():
    """Debug endpoint to check model checker status"""
    debug_info = {
        "model_check_blueprint_available": model_check_blueprint is not None,
        "model_check_api_importable": False,
        "api_instance_available": False,
        "worker_available": False,
        "cache_available": False
    }

    try:
        from adore_model_checker.model_checker_api import _get_api
        debug_info["model_check_api_importable"] = True

        api_instance = _get_api()
        debug_info["api_instance_available"] = True
        debug_info["api_instance_type"] = str(type(api_instance))

        if hasattr(api_instance, 'worker'):
            debug_info["worker_available"] = True
            debug_info["worker_running"] = getattr(
                api_instance.worker, 'running', None)
            debug_info["worker_type"] = str(type(api_instance.worker))

        if hasattr(api_instance, 'cache'):
            debug_info["cache_available"] = True
            debug_info["cache_type"] = str(type(api_instance.cache))
            try:
                runs = api_instance.cache.get_all_runs()
                debug_info["total_runs"] = len(runs)
                debug_info["running_runs"] = len(
                    [r for r in runs.values() if r.status.value == 'running'])
            except Exception as e:
                debug_info["cache_error"] = str(e)

    except Exception as e:
        debug_info["import_error"] = str(e)

    return jsonify(debug_info)


def main():
    global LOG_DIRECTORY, bag_manager, model_check_blueprint, workspace_monitor

    parser = argparse.ArgumentParser(description='ADORe API Server')
    parser.add_argument('--log-directory', type=str,
                        help='Directory for logs and bag recordings')
    parser.add_argument('--port', type=str,
                        help='TCP listining port. DEFAULT: 8888')
    parser.add_argument('--workspace-root', type=str,
                        help='Repository root containing ros2_workspace/. Defaults to two levels above this script.')

    args = parser.parse_args()

    LOG_DIRECTORY = args.log_directory or os.environ.get('LOG_DIRECTORY')
    PORT = args.port or 8888

    workspace_root = (
        args.workspace_root
        or os.environ.get('WORKSPACE_ROOT')
        or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    )
    workspace_monitor = WorkspaceMonitor(workspace_root)
    workspace_monitor.start()

    if LOG_DIRECTORY:
        os.makedirs(LOG_DIRECTORY, exist_ok=True)
        bag_manager = BagRecordingManager(LOG_DIRECTORY)
        print(f"✓ Bag recording enabled with log directory: {LOG_DIRECTORY}")
    else:
        print("⚠  Warning: No log directory specified. Bag recording will be disabled.")

    # Register model checker blueprint
    try:
        from adore_model_checker.model_checker_api import get_model_check_blueprint, _get_api
        model_check_blueprint = get_model_check_blueprint()
        app.register_blueprint(model_check_blueprint)
        print("✓ Model checker API blueprint registered successfully")

        # Patch the installed model_checker module so ContinuousMonitorEngine
        # never tries to create a history directory inside the read-only package tree.
        try:
            import adore_model_checker.model_checker as _mc_mod
            _mc_history_path = os.path.join(_get_api().log_directory, 'continuous')
            os.makedirs(_mc_history_path, exist_ok=True)
            _mc_mod._history_dir = lambda: _mc_history_path
            print(f"✓ Model checker history dir set to: {_mc_history_path}")
        except Exception as _patch_err:
            print(f"⚠ Could not patch model checker history dir: {_patch_err}")

        # Test the API is working
        with app.test_client() as client:
            response = client.get('/api/model_check/status')
            if response.status_code == 200:
                print("✓ Model checker API is responding")
            else:
                print(
                    f"⚠ Model checker API status check failed: {response.status_code}")

    except Exception as e:
        print(f"✗ Failed to register model checker blueprint: {e}")
        print("✗ Model checking functionality will not be available")
        import traceback
        traceback.print_exc()

    # Register ros2tools blueprint
    try:
        from ros2tools.ros2api import get_ros2tools_blueprint
        ros2tools_blueprint = get_ros2tools_blueprint()
        app.register_blueprint(ros2tools_blueprint)
        print("✓ ROS2 API blueprint registered successfully")
    except Exception as e:
        print(f"✗ Failed to register ros2tools blueprint: {e}")
        print("✗ ros2tools functionality will not be available")

    print(f"\n🚀 Starting ADORe API server on http://0.0.0.0:{PORT}")
    print(f"📊 API status available at: http://localhost:{PORT}/api/status")
    print(f"🔧 Workspace status at: http://localhost:{PORT}/api/workspace/status")
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=PORT)


if __name__ == '__main__':
    main()
