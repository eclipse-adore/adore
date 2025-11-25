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
from datetime import datetime, timezone
from collections import deque, defaultdict
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import signal
import psutil
import argparse
from flask import send_from_directory


model_check_blueprint = None
ros2_blueprint = None
stop_model_check_worker = None

try:
    from adore_model_checker.model_checker_api import get_model_check_blueprint, stop_model_check_worker as _stop_model_check_worker
    stop_model_check_worker = _stop_model_check_worker
    print("✓ ADORe Model Checker library found")
except ImportError as e:
    print(f"⚠ Warning: ADORe Model Checker library not found: {e}")
    print("⚠ Model checking functionality will be disabled")
    print("⚠ To enable model checking, please install the adore_model_checker library")

try:
    from ros2tools.ros2api import *
    print("✓ ros2tools library found")
except ImportError as e:
    print(f"⚠ Warning: ros2tools library not found: {e}")
    print("⚠ ros2tools will be disabled")

try:
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from util.ros_marshaller import ROSMarshaller
    print("✓ ROSMarshaller found")
except ImportError as e:
    print(f"⚠ Warning: ROSMarshaller not found: {e}")
    print("⚠ ROS topic functionality will be limited")
    ROSMarshaller = None

app = Flask(__name__)
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
        """Start model checking first, then scenario after 5 second delay"""
        if self.current_process and self.current_process.poll() is None:
            return {"success": False, "message": "Scenario already running"}

        try:
            with self.model_check_lock:
                self.waiting_for_model_check = False
                self.current_model_check_run_id = None

            # Step 1: Start model checking if enabled
            if model_check_enabled and model_check_blueprint is not None:
                print("Starting model checking first...")
                model_check_result = self._start_model_check(
                    model_check_config)
                print(f"Model check start result: {model_check_result}")

                if model_check_result["success"]:
                    run_id = model_check_result.get("run_id")
                    if run_id is not None:
                        with self.model_check_lock:
                            self.current_model_check_run_id = run_id
                            self.waiting_for_model_check = True
                        print(
                            f"Model checking started with run ID: {self.current_model_check_run_id}")
                    else:
                        print(
                            "Error: Model check start succeeded but no run ID returned")
                        return {
                            "success": False,
                            "message": "Model check start succeeded but no run ID returned",
                            "debug_info": model_check_result
                        }
                else:
                    error_msg = model_check_result.get(
                        'message', 'Unknown error')
                    print(f"Failed to start model checking: {error_msg}")
                    return {
                        "success": False,
                        "message": f"Failed to start model checking: {error_msg}",
                        "debug_info": model_check_result
                    }

                # Wait 5 seconds before starting scenario
                print("Waiting 5 seconds before starting scenario...")
                time.sleep(5)
            else:
                if not model_check_enabled:
                    print("Model checking disabled")
                if model_check_blueprint is None:
                    print("Model check blueprint not available")

            # Step 2: Start the scenario
            print("Starting scenario...")
            scenario_result = self.start_scenario(scenario_input, is_file)
            scenario_result['model_check_result'] = model_check_result
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
                # Custom launch content passed directly
                temp_file = os.path.join(
                    self.base_directory, "temp_custom_scenario.launch.py"
                )
                full_path = os.path.abspath(temp_file)

                with open(full_path, "w") as f:
                    f.write(scenario_input)

                self.current_scenario_content = scenario_input
                self.current_scenario = "temp_custom_scenario.launch.py"

                cmd = ["ros2", "launch", full_path]
                cwd = None

                print(
                    f"[ScenarioManager] Starting custom scenario from temp file: {full_path}"
                )

            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                cwd=cwd,
            )

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


scenario_manager = ScenarioManager()
bag_manager = None


@app.route('/')
def index():
    return render_template('index.html', host=request.host)


@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)


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
    return jsonify({
        "adore_api": "running",
        "model_checker_available": model_check_blueprint is not None,
        "ros_marshaller_available": ROSMarshaller is not None,
        "bag_recording_available": bag_manager is not None
    })


@app.route('/api/scenario/start', methods=['POST'])
def start_scenario_route():
    # Be tolerant if client sends no/invalid JSON
    data = request.get_json(silent=True) or {}

    scenario_input = data.get(
        'scenario', "adore_simulation_scenarios/simulation_test.launch.py"
    )
    is_file = data.get('is_file', True)
    model_check_enabled = data.get('model_check_enabled', False)
    if isinstance(model_check_enabled, str):
        model_check_enabled = model_check_enabled.lower() == 'true'
    model_check_config = data.get('model_check_config', 'config/default.yaml')

    if not scenario_input:
        return jsonify({"success": False, "message": "No scenario provided"}), 400

    # Currently you’re explicitly disabling model checking here
    model_check_enabled = False

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


@app.route('/api/topic/list')
def list_active_topics():
    try:
        stats = topic_manager.get_stats()

        system_topics = []
        try:
            result = subprocess.run(
                ["ros2", "topic", "list"], capture_output=True, text=True, check=True)
            system_topics = [t.strip()
                             for t in result.stdout.split('\n') if t.strip()]
        except:
            pass

        return jsonify({
            "success": True,
            "managed_topics": stats,
            "system_topics": system_topics
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to list topics: {str(e)}"}), 500


@app.route('/api/topic/info/<path:topic_name>')
def get_topic_info(topic_name):
    if not ROSMarshaller:
        return jsonify({"success": False, "message": "ROS functionality not available"}), 500

    try:
        if not topic_name.startswith('/'):
            topic_name = '/' + topic_name

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
            Default: "adore_simulation_scenarios/simulation_test.launch.py"
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
        'scenario', 'adore_simulation_scenarios/simulation_test.launch.py')
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
    global LOG_DIRECTORY, bag_manager, model_check_blueprint

    parser = argparse.ArgumentParser(description='ADORe API Server')
    parser.add_argument('--log-directory', type=str,
                        help='Directory for logs and bag recordings')
    parser.add_argument('--port', type=str,
                        help='TCP listining port. DEFAULT: 8888')

    args = parser.parse_args()

    LOG_DIRECTORY = args.log_directory or os.environ.get('LOG_DIRECTORY')
    PORT = args.port or 8888

    if LOG_DIRECTORY:
        os.makedirs(LOG_DIRECTORY, exist_ok=True)
        bag_manager = BagRecordingManager(LOG_DIRECTORY)
        print(f"✓ Bag recording enabled with log directory: {LOG_DIRECTORY}")
    else:
        print("⚠  Warning: No log directory specified. Bag recording will be disabled.")

    # Register model checker blueprint
    try:
        from adore_model_checker.model_checker_api import get_model_check_blueprint
        model_check_blueprint = get_model_check_blueprint()
        app.register_blueprint(model_check_blueprint)
        print("✓ Model checker API blueprint registered successfully")

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
    app.run(debug=True, host='0.0.0.0', port=PORT)


if __name__ == '__main__':
    main()
