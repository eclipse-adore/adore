"""
ros_marshaller.py

A dynamic utility for subscribing to, parsing, converting, and publishing ROS 1/2 messages
using YAML and JSON formats. Designed to work in both live and debug (file-based) modes,
this tool supports automated message type detection and stream framing.

Features:
    - Detects ROS 1 or ROS 2 at runtime
    - Subscribes to ROS topics and extracts YAML message streams
    - Converts YAML to JSON, enriched with topic and datatype metadata
    - Republish messages in real-time (optionally re-encoded as std_msgs/String)
    - Tracks transmission and reception metrics over time
    - Provides debug mode using static YAML files for testing without ROS
    - Safely manages subprocesses and threading for I/O operations

Main Class:
    ROSMarshaller

    Key Methods:
        - subscribe(topic, callback)
        - publish(json_string, topic, datatype)
        - get_datatype(topic)
        - callback_json / callback_republish / callback_republish_std_msgs_string_json
        - set_debug_mode(enable, debug_file)
        - start_metrics_reporter()
        - stop()
        - get_metrics(), print_metrics()

Command-line Usage:
    python ros_marshaller.py --topic /your/topic [--debug --debug-file file.yaml --max-lines 50]

Dependencies:
    - ROS 1: `rostopic`, `rospy`
    - ROS 2: `ros2 topic`, `rclpy`
    - External: `yq` (YAML-to-JSON converter), `ujson` (optional fast JSON parsing)

"""

import subprocess
import os
import sys

import pty
import threading
import yaml
import traceback
import time
import concurrent.futures
import shlex
import select
from collections import deque
from datetime import datetime
import json as standard_json
import yq

import yaml
import json
from yaml import CLoader as Loader

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from util.ros_message_importer import ROSMessageImporter
ROSMessageImporter.import_all_messages()

try:
    import ujson as json
    USING_UJSON = True
    JSONDecodeError = standard_json.JSONDecodeError
except ImportError:
    import json
    USING_UJSON = False
    JSONDecodeError = json.JSONDecodeError

class ROSMarshaller:
    ROSCMD = ["", "rostopic echo", "ros2 topic echo"]
    ROSPUBCMD = ["", "rostopic pub", "ros2 topic pub -t 1 -w 0 --keep-alive 10"]
    ROS_VERSION = None
    STD_MSGS_STRING_DATATYPE = None
    _stop_event = threading.Event()
    threads = []
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
    _command_cache = {}
    _process_pool = {}
    _process_lock = threading.RLock()
    MAX_YAML_LINES = 0  # Default limit for YAML lines collection (0 means unlimited)
    YQ_BINARY = "./yq"  # Path to yq binary for YAML to JSON conversion
    DEBUG_MODE = False  # When True, use file reading instead of ROS commands
    DEBUG_FILE = "data/monster.yaml"  # File to read in debug mode
    
    # Metrics tracking
    _metrics_lock = threading.RLock()
    _tx_timestamps = deque(maxlen=1000) 
    _rx_timestamps = deque(maxlen=1000)
    _last_metrics_report = 0
    _metrics_report_interval = 5.0  # Report metrics every 5 seconds
    
    _yaml_buffer_cache = {}
    _yaml_buffer_lock = threading.RLock()
    
    @staticmethod
    def set_debug_mode(enable=True, debug_file="data/monster.yaml"):
        """Enable or disable debug mode with optional debug file path"""
        ROSMarshaller.DEBUG_MODE = enable
        if debug_file:
            ROSMarshaller.DEBUG_FILE = debug_file
        print(f"Debug mode {'enabled' if enable else 'disabled'}" + 
              (f", using file: {debug_file}" if enable and debug_file else ""))
    
    @staticmethod
    def _increment_tx_counter():
        """Increment the transmitted messages counter"""
        with ROSMarshaller._metrics_lock:
            ROSMarshaller._tx_timestamps.append(time.time())
            
    @staticmethod
    def _increment_rx_counter():
        """Increment the received messages counter"""
        with ROSMarshaller._metrics_lock:
            ROSMarshaller._rx_timestamps.append(time.time())
    
    @staticmethod
    def _calculate_message_rate(timestamps):
        """Calculate messages per second from a deque of timestamps"""
        if not timestamps:
            return 0.0
            
        now = time.time()
        recent = [ts for ts in timestamps if now - ts <= 1.0]
        
        if not recent and len(timestamps) >= 2:
            time_span = timestamps[-1] - timestamps[0]
            if time_span > 0:
                return (len(timestamps) - 1) / time_span
            return 0.0
            
        return len(recent)
    
    @staticmethod
    def get_metrics():
        """Get current message rates"""
        with ROSMarshaller._metrics_lock:
            tx_rate = ROSMarshaller._calculate_message_rate(ROSMarshaller._tx_timestamps)
            rx_rate = ROSMarshaller._calculate_message_rate(ROSMarshaller._rx_timestamps)
            
        return {
            "tx_rate": tx_rate,
            "rx_rate": rx_rate,
            "timestamp": time.time()
        }
    
    @staticmethod
    def print_metrics():
        """Print current metrics to console"""
        metrics = ROSMarshaller.get_metrics()
        timestamp = datetime.fromtimestamp(metrics["timestamp"]).strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Metrics - TX: {metrics['tx_rate']:.2f} msg/s, RX: {metrics['rx_rate']:.2f} msg/s")
    
    @staticmethod
    def start_metrics_reporter():
        """Start a background thread to periodically report metrics"""
        def report_metrics():
            while not ROSMarshaller._stop_event.is_set():
                now = time.time()
                if now - ROSMarshaller._last_metrics_report >= ROSMarshaller._metrics_report_interval:
                    ROSMarshaller.print_metrics()
                    ROSMarshaller._last_metrics_report = now
                time.sleep(1.0)
                
        reporter = threading.Thread(target=report_metrics, daemon=True)
        reporter.start()
        ROSMarshaller.threads.append(reporter)
        return reporter

    @staticmethod
    def _detect_ros_version():
        if ROSMarshaller.ROS_VERSION is None:
            try:
                subprocess.run(['rostopic', '--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                ROSMarshaller.ROS_VERSION = 1
                ROSMarshaller.STD_MSGS_STRING_DATATYPE = "std_msgs/String"
            except FileNotFoundError:
                ROSMarshaller.ROS_VERSION = 2
                ROSMarshaller.STD_MSGS_STRING_DATATYPE = "std_msgs/msg/String" 
        return ROSMarshaller.ROS_VERSION

    @staticmethod
    def get_datatype(topic):
        if ROSMarshaller.DEBUG_MODE:
            return "std_msgs/msg/String"
            
        ros_version = ROSMarshaller._detect_ros_version()
        try:
            if ros_version == 1:
                result = subprocess.run(["rostopic", "type", topic], capture_output=True, text=True, check=True)
            else:
                result = subprocess.run(["ros2", "topic", "type", topic], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None



    def yaml_to_json(yaml_string, topic, datatype):
        obj = yaml.load(yaml_string, Loader=Loader)
        obj['topic'] = topic 
        obj['datatype'] = datatype 
        json_string = json.dumps(obj)

        return json_string

    @staticmethod
    def to_dict(raw_json, topic, datatype):
        """Process JSON input and output as JSON with topic and datatype metadata"""
        obj = raw_json 
        try:
            obj = json.loads(raw_json)
        except (ValueError, JSONDecodeError) as e:
            print(f"JSON parsing error in callback_json: {str(e)}")
            obj = {"raw_content": raw_json, "error": str(e)}
        
        # Add topic metadata to data structure
        obj['topic'] = topic 
        obj['datatype'] = datatype 
        return obj 

    @staticmethod
    def to_json(raw_json, topic, datatype):
        return json.dumps(ROSMarshaller.to_dict(raw_json, topic, datatype))

    @staticmethod
    def callback_json(raw_json, topic, datatype):
        """Process JSON input and output as JSON with topic and datatype metadata"""
        data = ROSMarshaller.to_dict(raw_json, topic, datatype)
        import sys
        with open(f"{topic.replace("/", "_")}.json", "w") as f:
            f.write(json.dumps(data, indent=4))
        print(json.dumps(data, indent=4))

    @staticmethod
    def callback_republish_std_msgs_string_json(raw_json, topic, datatype):
        """Process JSON input and republish as std_msgs/String"""
        try:
            obj = json.loads(raw_json)
        except (ValueError, JSONDecodeError) as e:
            print(f"JSON parsing error in callback_republish_std_msgs_string_json: {str(e)}")
            obj = {"raw_content": raw_json, "error": str(e)}
        
        # Add topic metadata to data structure
        obj['topic'] = topic 
        obj['datatype'] = datatype 
        
        # Republish as std_msgs/String on a new topic
        new_topic = f"{topic}_json"
        new_datatype = ROSMarshaller.STD_MSGS_STRING_DATATYPE
        json_string = f"data: {json.dumps(obj)}"
        ROSMarshaller.publish(json_string, new_topic, new_datatype)

    @staticmethod
    def callback_republish(raw_json, topic, datatype):
        """Process JSON input and republish on a new topic"""
        try:
            obj = json.loads(raw_json)
        except (ValueError, JSONDecodeError) as e:
            print(f"JSON parsing error in callback_republish: {str(e)}")
            obj = {"raw_content": raw_json, "error": str(e)}
        
        # Republish on a new topic
        new_topic = f"{topic}_republish"
        ROSMarshaller.publish(obj, new_topic, datatype)

    @staticmethod
    def _process_yaml_document(yaml_data, topic, datatype, callback):
        """Process a complete YAML document in one go"""
        if not yaml_data.strip():
            return
          
        json_str = ROSMarshaller.yaml_to_json(yaml_data, topic, datatype)
        ROSMarshaller._increment_rx_counter()

        callback(json_str, topic, datatype)

    @staticmethod
    def _direct_read_thread(process, topic, datatype, callback, stop_event):
        """stdout yaml document framer, extracts yaml documents from the stdout stream"""
        try:
            buffer = ""
            
            while not stop_event.is_set() and process.poll() is None:
                read_ready, _, _ = select.select([process.stdout], [], [], 0.1)
                if not read_ready:
                    continue
                    
                chunk = process.stdout.read1(4096).decode('utf-8')
                if not chunk:
                    break
                    
                buffer += chunk
                
                while '---' in buffer:
                    doc, buffer = buffer.split('---', 1)
                    if doc.strip():
                        ROSMarshaller._process_yaml_document(doc, topic, datatype, callback)
            
            if buffer.strip() and not stop_event.is_set():
                ROSMarshaller._process_yaml_document(buffer, topic, datatype, callback)
                
        except Exception as e:
            print(f"Error in direct reader thread for topic {topic}: {e}")
            traceback.print_exc()

    @staticmethod
    def _debug_reader_thread(topic, datatype, callback, stop_event):
        """file yaml document framer, extracts yaml documents from the stdout stream"""
        try:
            while not stop_event.is_set():
                try:
                    with open(ROSMarshaller.DEBUG_FILE, 'r') as f:
                        content = f.read()
                    
                    docs = content.split('---')
                    for doc in docs:
                        if doc.strip() and not stop_event.is_set():
                            ROSMarshaller._process_yaml_document(doc, topic, datatype, callback)
                except IOError as e:
                    print(f"I/O error in debug reader: {e}")
                    
        except Exception as e:
            print(f"Error in debug reader thread for topic {topic}: {e}")
            traceback.print_exc()

    @staticmethod
    def stop():
        print("Stopping ROSMarshaller threads...")
        ROSMarshaller._stop_event.set()
        
        ROSMarshaller.print_metrics()
        
        ROSMarshaller.executor.shutdown(wait=False)
        
        threads_to_join = ROSMarshaller.threads.copy()
        
        ROSMarshaller.threads = []
        
        for thread in threads_to_join:
            try:
                thread.join(timeout=1.0)
            except Exception as e:
                print(f"Error joining thread: {e}")
        
        with ROSMarshaller._process_lock:
            for cmd, process in ROSMarshaller._process_pool.items():
                try:
                    process.terminate()
                except:
                    pass
            ROSMarshaller._process_pool.clear()

    @staticmethod
    def yaml_to_dict(raw_yaml):
        """Convert YAML to dict, compatible with the original method but using the new converter"""
        try:
            json_str = ROSMarshaller.yaml_to_json(raw_yaml)
            return json.loads(json_str)
        except Exception as e:
            return {"error": str(e), "raw_content": raw_yaml}
    
    @staticmethod
    def _get_or_create_process(command_str):
        with ROSMarshaller._process_lock:
            if command_str in ROSMarshaller._process_pool:
                process = ROSMarshaller._process_pool[command_str]
                if process.poll() is None:
                    return process
            
            command = shlex.split(command_str)
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            ROSMarshaller._process_pool[command_str] = process
            return process
    
    @staticmethod
    def subscribe(topic, callback=None):
        if callback is None:
            callback = ROSMarshaller.callback_json

        datatype = ROSMarshaller.get_datatype(topic)
        
        if ROSMarshaller.DEBUG_MODE:
            if not os.path.exists(ROSMarshaller.DEBUG_FILE):
                with open(ROSMarshaller.DEBUG_FILE, 'w') as f:
                    f.write("test: debug\n---\n")
                print(f"Created debug file: {ROSMarshaller.DEBUG_FILE}")
                
            def run_debug():
                print(f"Starting debug reader for topic: {topic}")
                ROSMarshaller._debug_reader_thread(topic, datatype, callback, ROSMarshaller._stop_event)
                
            debug_thread = threading.Thread(target=run_debug, daemon=True)
            debug_thread.start()
            ROSMarshaller.threads.append(debug_thread)
            print(f"Debug subscription thread started for topic: {topic}")
            return debug_thread
        else:
            ros_version = ROSMarshaller._detect_ros_version()
            base_command = (ROSMarshaller.ROSCMD[ros_version]).split()
            base_command.append(topic)
            command_str = ' '.join(base_command)
            print(f"ROS command: {command_str}")
            
            def run():
                retry_delay = 0.1
                max_delay = 5.0
                
                while not ROSMarshaller._stop_event.is_set():
                    process = None
                    
                    try:
                        process = subprocess.Popen(
                            base_command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            stdin=subprocess.DEVNULL,
                            bufsize=4096,
                            universal_newlines=False
                        )
                        print(f"Started process for {topic} (PID: {process.pid})")
                        
                        ROSMarshaller._direct_read_thread(
                            process, topic, datatype, callback, ROSMarshaller._stop_event
                        )
                        
                        retry_delay = 0.1
                        
                    except Exception as e:
                        print(f"Error in subscription to {topic}: {e}")
                        traceback.print_exc()
                    
                    if process is not None and process.poll() is None:
                        try:
                            process.terminate()
                            print(f"Terminated process for {topic} (PID: {process.pid})")
                        except:
                            pass
                    
                    if not ROSMarshaller._stop_event.is_set():
                        print(f"Retrying subscription to {topic} in {retry_delay}s")
                        time.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, max_delay)

            sub_thread = threading.Thread(target=run, daemon=True)
            sub_thread.start()
            ROSMarshaller.threads.append(sub_thread)
            print(f"Subscription thread started for topic: {topic}")
            return sub_thread

    @staticmethod
    def shell_escape(input_string):
        return shlex.quote(input_string)

    @staticmethod
    def publish(json_string, topic=None, datatype=None):
        try:
            if isinstance(json_string, str) and json_string.startswith("data: "):
                data_content = json_string[6:]
                obj = {"data": data_content}
            else:
                obj = json_string if isinstance(json_string, dict) else json.loads(json_string)
            
            if topic is None or datatype is None:
                topic = obj.get('topic')
                datatype = obj.get('datatype')
                if topic is None or datatype is None:
                    raise ValueError("Topic and datatype must be provided either in the JSON or as arguments")
            
            if ROSMarshaller.DEBUG_MODE:
                print(f"DEBUG PUBLISH to {topic} ({datatype}): {json.dumps(obj)}")
                ROSMarshaller._increment_tx_counter()
                return
            
            publish_obj = obj.copy() if isinstance(obj, dict) else obj
            if isinstance(publish_obj, dict):
                publish_obj.pop('datatype', None)
                publish_obj.pop('topic', None)
            
            json_payload = json.dumps(publish_obj)
            json_escaped = ROSMarshaller.shell_escape(json_payload)
            
            ros_version = ROSMarshaller._detect_ros_version()
            cache_key = f"{ros_version}:{topic}:{datatype}"
            if cache_key not in ROSMarshaller._command_cache:
                command = (ROSMarshaller.ROSPUBCMD[ros_version]).split()
                command.extend([topic, datatype])
                ROSMarshaller._command_cache[cache_key] = command
            
            command = ROSMarshaller._command_cache[cache_key].copy()
            command.append(json_escaped)
            
            subprocess.run(
                command, 
                check=True, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.PIPE
            )
            
            ROSMarshaller._increment_tx_counter()
            
        except Exception as e:
            print(f"Failed to publish message to {topic}: {e}")
            traceback.print_exc()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='ROSMarshaller - ROS message processor')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--debug-file', default='data/monster.yaml', help='File to read in debug mode')
    parser.add_argument('--max-lines', type=int, default=0, help='Maximum YAML lines to collect (0 for unlimited)')
    parser.add_argument('--topic', default='/dummy', help='Topic to subscribe to')
    
    args = parser.parse_args()
    
    ROSMarshaller.MAX_YAML_LINES = args.max_lines
    if args.debug:
        ROSMarshaller.set_debug_mode(True, args.debug_file)
        
    topic = args.topic
    
    print(f"Starting ROSMarshaller with topic: {topic}")
    print(f"Debug mode: {ROSMarshaller.DEBUG_MODE}")
    print(f"Max YAML lines: {ROSMarshaller.MAX_YAML_LINES}")
    
    metrics_thread = ROSMarshaller.start_metrics_reporter()
    
    # Subscribe to topics
    #repub_json_thread = ROSMarshaller.subscribe(topic, ROSMarshaller.callback_republish_std_msgs_string_json)
    echo_thread = ROSMarshaller.subscribe(topic, ROSMarshaller.callback_json)
    #repub_thread = ROSMarshaller.subscribe(topic, ROSMarshaller.callback_republish)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
        ROSMarshaller.stop()

