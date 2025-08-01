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

class BagRecordingManager:
    def __init__(self, log_directory):
        self.log_directory = log_directory
        self.bag_recordings_dir = os.path.join(log_directory, "bag_file_recordings")
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
            
            threading.Thread(target=self._monitor_recording_output, daemon=True).start()
            
            if duration:
                threading.Thread(target=self._auto_stop_recording, args=(duration,), daemon=True).start()
            
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
            
            relative_path = os.path.relpath(self.current_bag_path, self.log_directory)
            
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
                        relative_path = os.path.relpath(item_path, self.log_directory)
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
                    
        self.cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
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
    def __init__(self, base_directory="../../adore_scenarios/simulation_scenarios"):
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
        
        os.makedirs(self.base_directory, exist_ok=True)
        
    def get_available_scenarios(self):
        if not os.path.exists(self.base_directory):
            return []
        
        scenarios = []
        for root, dirs, files in os.walk(self.base_directory):
            for file in files:
                if file.endswith('.launch.py') or file.endswith('.launch.xml'):
                    rel_path = os.path.relpath(os.path.join(root, file), self.base_directory)
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
    
    def start_scenario(self, scenario_input, is_file=True):
        if self.current_process and self.current_process.poll() is None:
            return {"success": False, "message": "Scenario already running"}
        
        try:
            if is_file:
                scenario_path = os.path.join(self.base_directory, scenario_input)
                if not os.path.exists(scenario_path):
                    return {"success": False, "message": f"Scenario file not found: {scenario_input}"}
                
                with open(scenario_path, 'r') as f:
                    self.current_scenario_content = f.read()
                    
                cmd = ["ros2", "launch", scenario_path]
                self.current_scenario = scenario_input
                cwd = self.base_directory
            else:
                temp_file = os.path.join(self.base_directory, "temp_custom_scenario.launch.py")
                with open(temp_file, 'w') as f:
                    f.write(scenario_input)
                self.current_scenario_content = scenario_input
                cmd = ["ros2", "launch", temp_file]
                self.current_scenario = "temp_custom_scenario.launch.py"
                cwd = self.base_directory
            
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                cwd=cwd
            )
            
            self.status = "running"
            self.scenario_start_time = time.time()
            self.output_buffer.clear()
            
            threading.Thread(target=self._monitor_output, daemon=True).start()
            
            return {"success": True, "message": "Scenario started successfully"}
            
        except Exception as e:
            self.status = "failed"
            return {"success": False, "message": f"Failed to start scenario: {str(e)}"}

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
            subprocess.run(["pkill", "-f", "ros2"], check=False)
            subprocess.run(["ros2", "daemon", "stop"], check=False)
            
            if self.current_process:
                try:
                    self.current_process.kill()
                except:
                    pass
            
            self.status = "idle"
            self.current_process = None
            return {"success": True, "message": "All scenarios halted"}
            
        except Exception as e:
            return {"success": False, "message": f"Failed to halt scenarios: {str(e)}"}
    
    def restart_scenario(self):
        self.halt_all()
        time.sleep(2)
        
        if self.current_scenario:
            return self.start_scenario(self.current_scenario)
        else:
            return {"success": False, "message": "No scenario to restart"}
    
    def get_output(self, lines=1000):
        with self.output_lock:
            output_lines = list(self.output_buffer)[-lines:]
            return "\n".join(output_lines)
    
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
            "pid": self.current_process.pid if self.current_process else None
        }
    
    def set_loop_mode(self, enabled, delay=0, runtime=60):
        self.loop_mode = enabled
        self.loop_delay = delay
        self.default_runtime = runtime
        
        if enabled:
            self.loop_active = True
            if not self.loop_thread or not self.loop_thread.is_alive():
                self.loop_thread = threading.Thread(target=self._loop_monitor, daemon=True)
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
                if self.current_process and self.current_process.poll() is None:
                    if self.scenario_start_time and (time.time() - self.scenario_start_time) >= self.default_runtime:
                        print(f"Loop: Runtime ({self.default_runtime}s) reached, halting...")
                        self.halt_all()
                        time.sleep(2)
                        
                        if self.loop_mode and self.current_scenario:
                            print(f"Loop: Waiting {self.loop_delay}s before restart...")
                            time.sleep(self.loop_delay)
                            print(f"Loop: Starting scenario: {self.current_scenario}")
                            self.start_scenario(self.current_scenario)
                            
                elif self.current_process and self.current_process.poll() is not None:
                    print(f"Loop: Process ended, restarting after {self.loop_delay}s...")
                    self.halt_all()
                    time.sleep(2)
                    
                    if self.loop_mode and self.current_scenario:
                        time.sleep(self.loop_delay)
                        self.start_scenario(self.current_scenario)
                        
                elif not self.current_process:
                    print(f"Loop: No process running, starting scenario: {self.current_scenario}")
                    self.start_scenario(self.current_scenario)
            
            time.sleep(1)

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
    return jsonify({
        "adore_api": "running",
        "model_checker_available": model_check_blueprint is not None,
        "ros_marshaller_available": ROSMarshaller is not None,
        "bag_recording_available": bag_manager is not None
    })

@app.route('/api/scenario/start', methods=['POST'])
def start_scenario():
    data = request.json
    scenario_input = data.get('scenario')
    is_file = data.get('is_file', True)
    
    if not scenario_input:
        return jsonify({"success": False, "message": "No scenario provided"}), 400
    
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
    
    scenario_manager.set_loop_mode(enabled, delay, runtime)
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
    
    result = bag_manager.start_recording(duration=duration, topics=topics, scenario_name=scenario_name)
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
                        current_messages = list(topic_manager.subscribers[topic]['messages'])
                        if current_messages:
                            messages = current_messages[-limit:] if limit > 0 else current_messages
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
            result = subprocess.run(["ros2", "topic", "list"], capture_output=True, text=True, check=True)
            system_topics = [t.strip() for t in result.stdout.split('\n') if t.strip()]
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
    This is a blocking endpoint that waits for both scenario and model checking to finish.
    
    Parameters:
    - scenario: Launch file name (default: "simulation_test.launch.py")
    - duration: Runtime in seconds (default: 5)
    
    Returns:
    - success: Whether the operation completed successfully
    - scenario: The scenario that was run
    - duration: The duration used
    - scenario_result: Result from starting the scenario
    - model_check_result: Results from model checking (if available)
    - model_check_available: Whether model checking was available
    - error: Error message if something went wrong
    """
    data = request.json or {}
    scenario = data.get('scenario', 'simulation_test.launch.py')
    duration = data.get('duration', 5)
    
    # Validate inputs
    if not isinstance(duration, (int, float)) or duration <= 0:
        return jsonify({
            "success": False,
            "error": "Duration must be a positive number",
            "scenario": scenario,
            "duration": duration
        }), 400
    
    try:
        # Clean up any existing processes
        scenario_manager.halt_all()
        time.sleep(2)
        
        # Start the scenario
        scenario_result = scenario_manager.start_scenario(scenario, is_file=True)
        if not scenario_result["success"]:
            return jsonify({
                "success": False,
                "error": f"Failed to start scenario: {scenario_result['message']}",
                "scenario": scenario,
                "duration": duration,
                "scenario_result": scenario_result
            })
        
        # Check if model checking is available
        if model_check_blueprint is None:
            # Just run scenario for the duration without model checking
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
        
        # Start model checking using internal test client
        with app.test_client() as client:
            model_check_data = {
                'config_file': 'config/default.yaml',
                'duration': duration,
                'vehicle_id': 0
            }
            
            try:
                response = client.post('/api/model_check/online', json=model_check_data)
                model_check_start_result = response.get_json()
                
                if response.status_code != 200 or 'run_id' not in model_check_start_result:
                    # Model checking failed to start, but scenario is running
                    time.sleep(duration)
                    scenario_manager.halt_all()
                    return jsonify({
                        "success": False,
                        "error": f"Failed to start model checking: {model_check_start_result}",
                        "scenario": scenario,
                        "duration": duration,
                        "scenario_result": scenario_result,
                        "model_check_available": True
                    })
                
                run_id = model_check_start_result['run_id']
                
            except Exception as e:
                # Model checking failed to start
                time.sleep(duration)
                scenario_manager.halt_all()
                return jsonify({
                    "success": False,
                    "error": f"Exception starting model checking: {str(e)}",
                    "scenario": scenario,
                    "duration": duration,
                    "scenario_result": scenario_result,
                    "model_check_available": True
                })
            
            # Wait for model checking to complete (blocking)
            max_wait_time = duration + 60  # Add buffer time for model checking overhead
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                try:
                    status_response = client.get(f'/api/model_check/result/{run_id}')
                    
                    if status_response.status_code == 200:
                        status_data = status_response.get_json()
                        
                        if status_data['status'] == 'completed':
                            # Success - both scenario and model checking completed
                            scenario_manager.halt_all()
                            return jsonify({
                                "success": True,
                                "scenario": scenario,
                                "duration": duration,
                                "scenario_result": scenario_result,
                                "model_check_result": status_data,
                                "model_check_available": True
                            })
                        
                        elif status_data['status'] in ['failed', 'cancelled', 'error']:
                            # Model checking failed
                            scenario_manager.halt_all()
                            return jsonify({
                                "success": False,
                                "error": f"Model checking failed with status: {status_data['status']}",
                                "scenario": scenario,
                                "duration": duration,
                                "scenario_result": scenario_result,
                                "model_check_result": status_data,
                                "model_check_available": True
                            })
                        
                        # Still running (pending, running), continue waiting
                        time.sleep(1)
                        
                    elif status_response.status_code == 404:
                        # Run ID not found
                        break
                    else:
                        # Other HTTP error
                        time.sleep(1)
                        
                except Exception as e:
                    print(f"Error checking model check status: {e}")
                    time.sleep(1)
            
            scenario_manager.halt_all()
            return jsonify({
                "success": False,
                "error": "Model checking timed out or failed to complete within expected time",
                "scenario": scenario,
                "duration": duration,
                "scenario_result": scenario_result,
                "model_check_available": True,
                "timeout_seconds": max_wait_time
            })
        
    except Exception as e:
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

def main():
    global LOG_DIRECTORY, bag_manager, model_check_blueprint
    
    parser = argparse.ArgumentParser(description='ADORe API Server')
    parser.add_argument('--log-directory', type=str, help='Directory for logs and bag recordings')
    
    args = parser.parse_args()
    
    LOG_DIRECTORY = args.log_directory or os.environ.get('LOG_DIRECTORY')
    
    if LOG_DIRECTORY:
        os.makedirs(LOG_DIRECTORY, exist_ok=True)
        bag_manager = BagRecordingManager(LOG_DIRECTORY)
        print(f"✓ Bag recording enabled with log directory: {LOG_DIRECTORY}")
    else:
        print("⚠ Warning: No log directory specified. Bag recording will be disabled.")
    
    if model_check_blueprint is None:
        try:
            model_check_blueprint = get_model_check_blueprint()
            app.register_blueprint(model_check_blueprint)
            print("✓ Model checker API blueprint registered successfully")
        except Exception as e:
            print(f"✗ Failed to register model checker blueprint: {e}")
            print("✗ Model checking functionality will not be available")
    else:
        try:
            blueprint = get_model_check_blueprint()
            app.register_blueprint(blueprint)
            print("✓ Model checker API blueprint registered successfully")
        except Exception as e:
            print(f"✗ Failed to register model checker blueprint: {e}")

    try:
        ros2tools_blueprint = get_ros2tools_blueprint()
        app.register_blueprint(ros2tools_blueprint)
        print("✓ ROS2 API blueprint registered successfully")
    except Exception as e:
        print(f"✗ Failed to register ros2tools blueprint: {e}")
        print("✗ ros2tools functionality will not be available")
 



    print(f"\n🚀 Starting ADORe API server on http://0.0.0.0:8888")
    print(f"📊 API status available at: http://localhost:8888/api/status")
    app.run(debug=True, host='0.0.0.0', port=8888)

if __name__ == '__main__':
    main()
