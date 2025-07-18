import os
import subprocess
import threading
import time
import json
from datetime import datetime
from collections import deque
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import signal
import psutil

app = Flask(__name__)
CORS(app)

# Global storage for positions
stored_positions = {
    'start': None,
    'goal': None
}

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
        
        # Ensure base directory exists
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
            
            # Create directory if it doesn't exist
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
                # Save custom scenario in the same directory as other scenarios
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
                cwd=cwd  # Set working directory to scenario directory
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
        """Restart with halt first"""
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
                # Check if we have a running process
                if self.current_process and self.current_process.poll() is None:
                    # Check if scenario has been running for the default runtime
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
                    # Process has ended unexpectedly, restart it
                    print(f"Loop: Process ended, restarting after {self.loop_delay}s...")
                    self.halt_all()
                    time.sleep(2)
                    
                    if self.loop_mode and self.current_scenario:
                        time.sleep(self.loop_delay)
                        self.start_scenario(self.current_scenario)
                        
                elif not self.current_process:
                    # No process running, start one
                    print(f"Loop: No process running, starting scenario: {self.current_scenario}")
                    self.start_scenario(self.current_scenario)
            
            time.sleep(1)

scenario_manager = ScenarioManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/goal_picker')
def goal_picker():
    return render_template('goal_picker.html')

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8888)
