# util/ros_marshaller.py
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

"""
ros_marshaller.py

A dynamic utility for subscribing to, parsing, converting, and publishing ROS 1/2 messages
using command-line tools.
"""

import subprocess
import os
import sys
import threading
import yaml
import traceback
import time
import shlex
import select
from collections import deque
from datetime import datetime
import json
import logging

# Local import for message class loading
from .ros_message_importer import ROSMessageImporter

# Initialize logging for the marshaller
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Ensure ROS messages are loaded before use
try:
    ROSMessageImporter.import_all_messages()
    MESSAGES_LOADED = True
except Exception as e:
    logging.warning(
        f"Failed to import ROS messages: {e}. ROS functionality will be limited.")
    MESSAGES_LOADED = False


class ROSMarshaller:
    # --- Static Configuration ---
    ROSCMD = ["", "rostopic echo --no-arr", "ros2 topic echo --no-arr"]
    ROSPUBCMD = ["", "rostopic pub -1",
                 "ros2 topic pub -t 1 -w 0 --keep-alive 10"]
    ROS_VERSION = 0  # 1 for ROS 1, 2 for ROS 2, 0 for not detected/unknown
    STD_MSGS_STRING_DATATYPE = None

    DEBUG_MODE = False
    DEBUG_FILE = "data/debug_sample.yaml"

    # --- Runtime State ---
    _stop_event = threading.Event()
    _threads = []
    _command_cache = {}
    _process_pool = {}  # Currently unused, but kept for future command management
    _process_lock = threading.RLock()

    # Metrics tracking (simplified)
    _metrics_lock = threading.RLock()
    _tx_count = 0
    _rx_count = 0

    # --- Initialization and Detection ---

    @staticmethod
    def initialize():
        """Detect ROS version and configure command strings."""
        if ROSMarshaller.ROS_VERSION == 0:
            try:
                subprocess.run(
                    ['rostopic', '--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                ROSMarshaller.ROS_VERSION = 1
                ROSMarshaller.STD_MSGS_STRING_DATATYPE = "std_msgs/String"
                logging.info("ROS 1 detected.")
            except (FileNotFoundError, subprocess.CalledProcessError):
                try:
                    subprocess.run(
                        ['ros2', 'topic', '--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    ROSMarshaller.ROS_VERSION = 2
                    ROSMarshaller.STD_MSGS_STRING_DATATYPE = "std_msgs/msg/String"
                    logging.info("ROS 2 detected.")
                except (FileNotFoundError, subprocess.CalledProcessError):
                    logging.error(
                        "Could not detect ROS 1 or ROS 2. Command-line tools not available.")
                    ROSMarshaller.ROS_VERSION = 0
        return ROSMarshaller.ROS_VERSION > 0

    @staticmethod
    def set_debug_mode(enable=True, debug_file=None):
        """Enable or disable debug mode with optional debug file path"""
        ROSMarshaller.DEBUG_MODE = enable
        if debug_file:
            ROSMarshaller.DEBUG_FILE = debug_file

        if enable and not os.path.exists(ROSMarshaller.DEBUG_FILE):
            with open(ROSMarshaller.DEBUG_FILE, 'w') as f:
                f.write("test: debug\n---\n")

        logging.info(f"Debug mode {'enabled' if enable else 'disabled'}" +
                     (f", using file: {ROSMarshaller.DEBUG_FILE}" if enable and debug_file else ""))

    # --- Utilities ---
    @staticmethod
    def get_datatype(topic):
        """Get the ROS message datatype for a topic using ROS command-line tools."""
        if ROSMarshaller.DEBUG_MODE:
            # Return a default type in debug mode
            return ROSMarshaller.STD_MSGS_STRING_DATATYPE or "std_msgs/msg/String"

        if ROSMarshaller.ROS_VERSION == 0 and not ROSMarshaller.initialize():
            return None

        try:
            if ROSMarshaller.ROS_VERSION == 1:
                result = subprocess.run(
                    ["rostopic", "type", topic], capture_output=True, text=True, check=True, timeout=5)
            else:
                result = subprocess.run(
                    ["ros2", "topic", "type", topic], capture_output=True, text=True, check=True, timeout=5)
            return result.stdout.strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return None

    # Keys emitted by ros2 topic echo that are not part of the message payload
    _ECHO_NOISE_KEYS = frozenset({'WARNING', 'WARN', 'ERROR', 'INFO', 'DEBUG'})

    @staticmethod
    def _strip_echo_noise(yaml_string):
        """Remove WARNING/INFO lines ros2 topic echo writes to stdout before real YAML."""
        lines = yaml_string.splitlines()
        clean = [l for l in lines if not any(l.startswith(k) for k in ('WARNING', 'WARN:', 'ERROR', 'INFO:', 'DEBUG:'))]
        return '\n'.join(clean)

    @staticmethod
    def _yaml_to_json(yaml_string, topic, datatype):
        """Convert YAML message string to JSON, adding metadata."""
        try:
            clean = ROSMarshaller._strip_echo_noise(yaml_string)
            if not clean.strip():
                return None

            obj = yaml.safe_load(clean)
            if not isinstance(obj, dict):
                obj = {"data": obj}

            # Drop any echo-injected noise keys that survived YAML parsing
            for k in list(obj.keys()):
                if k in ROSMarshaller._ECHO_NOISE_KEYS:
                    del obj[k]

            if not obj:
                return None

            obj['topic'] = topic
            obj['datatype'] = datatype

            return json.dumps(obj)

        except yaml.YAMLError as ye:
            logging.error(f"YAML parsing error for topic {topic}: {ye}")
            return json.dumps({"error": "YAML_PARSE_ERROR", "raw_content": yaml_string, "topic": topic, "datatype": datatype})
        except Exception as e:
            logging.error(f"Conversion error for topic {topic}: {e}")
            return json.dumps({"error": "CONVERSION_ERROR", "raw_content": yaml_string, "topic": topic, "datatype": datatype})

    @staticmethod
    def shell_escape(input_string):
        """Escapes a string for safe use in a shell command."""
        return shlex.quote(input_string)

    # --- Metrics ---
    @staticmethod
    def _increment_tx_counter():
        """Increment the transmitted messages counter"""
        with ROSMarshaller._metrics_lock:
            ROSMarshaller._tx_count += 1

    @staticmethod
    def _increment_rx_counter():
        """Increment the received messages counter"""
        with ROSMarshaller._metrics_lock:
            ROSMarshaller._rx_count += 1

    @staticmethod
    def get_metrics():
        """Get current message counts"""
        with ROSMarshaller._metrics_lock:
            return {
                "tx_count": ROSMarshaller._tx_count,
                "rx_count": ROSMarshaller._rx_count,
                "timestamp": time.time()
            }

    # --- Subscriber Core ---

    @staticmethod
    def _process_yaml_document(yaml_data, topic, datatype, callback):
        """Process a complete YAML document and send to callback."""
        if not yaml_data.strip():
            return

        json_str = ROSMarshaller._yaml_to_json(yaml_data, topic, datatype)
        if json_str is None:
            return

        ROSMarshaller._increment_rx_counter()
        callback(json_str, topic, datatype)

    @staticmethod
    def _direct_read_thread(process, topic, datatype, callback, stop_event):
        """Monitors the stdout of the ROS topic echo process and frames YAML documents."""
        try:
            buffer = ""

            # Use process.stdout.read1() for efficient reading of binary data
            # and then decode it. Using `universal_newlines=True` is often less
            # efficient with streaming subprocesses.
            while not stop_event.is_set() and process.poll() is None:
                # Wait for data to be available on stdout
                read_ready, _, _ = select.select(
                    [process.stdout], [], [], 0.05)
                if not read_ready:
                    continue

                # Read a chunk (e.g., 4KB)
                chunk = process.stdout.read(4096).decode(
                    'utf-8', errors='ignore')
                if not chunk:
                    break  # EOF

                buffer += chunk

                # Split buffer by YAML document separator '---'
                while '---' in buffer:
                    doc, buffer = buffer.split('---', 1)
                    if doc.strip():
                        ROSMarshaller._process_yaml_document(
                            doc, topic, datatype, callback)

            # Process any remaining data in the buffer after the process terminates
            if buffer.strip() and not stop_event.is_set():
                ROSMarshaller._process_yaml_document(
                    buffer, topic, datatype, callback)

        except Exception as e:
            logging.error(
                f"Error in direct reader thread for topic {topic}: {e}")
            traceback.print_exc()

    @staticmethod
    def _debug_reader_thread(topic, datatype, callback, stop_event):
        """Reads a static YAML file in a loop for debug mode."""
        try:
            while not stop_event.is_set():
                time.sleep(1.0)  # Reduce CPU usage in the loop
                try:
                    with open(ROSMarshaller.DEBUG_FILE, 'r') as f:
                        content = f.read()

                    docs = content.split('---')
                    for doc in docs:
                        if doc.strip() and not stop_event.is_set():
                            ROSMarshaller._process_yaml_document(
                                doc, topic, datatype, callback)
                except IOError as e:
                    logging.error(f"I/O error in debug reader: {e}")

        except Exception as e:
            logging.error(
                f"Error in debug reader thread for topic {topic}: {e}")
            traceback.print_exc()

    @staticmethod
    def subscribe(topic, callback):
        """
        Starts a subscription thread for a given ROS topic.
        Callback signature: (json_data_str, topic_name, datatype_str)
        """
        if not ROSMarshaller.DEBUG_MODE and not ROSMarshaller.initialize():
            raise RuntimeError("ROS environment not initialized or detected.")

        datatype = ROSMarshaller.get_datatype(topic)
        if datatype is None and not ROSMarshaller.DEBUG_MODE:
            logging.warning(
                f"Could not determine datatype for topic: {topic}. Subscription may fail.")

        if ROSMarshaller.DEBUG_MODE:
            thread = threading.Thread(
                target=ROSMarshaller._debug_reader_thread,
                args=(topic, datatype, callback, ROSMarshaller._stop_event),
                daemon=True
            )
            thread.start()
            ROSMarshaller._threads.append(thread)
            logging.info(
                f"Debug subscription thread started for topic: {topic}")
            return thread
        else:
            ros_version = ROSMarshaller.ROS_VERSION
            # Command: 'ros2 topic echo /topic --no-arr'
            base_command = (ROSMarshaller.ROSCMD[ros_version]).split()
            base_command.append(topic)

            def run():
                retry_delay = 0.5
                max_delay = 5.0
                resolved_datatype = datatype

                while not ROSMarshaller._stop_event.is_set():
                    # Re-try datatype lookup each iteration if still unknown
                    if resolved_datatype is None:
                        resolved_datatype = ROSMarshaller.get_datatype(topic)

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
                        logging.info(
                            f"Started process for {topic} (PID: {process.pid})")

                        ROSMarshaller._direct_read_thread(
                            process, topic, resolved_datatype, callback, ROSMarshaller._stop_event
                        )

                        retry_delay = 0.5  # Reset delay after a successful run/termination

                    except Exception as e:
                        logging.error(
                            f"Error in subscription loop for {topic}: {e}")

                    finally:
                        if process is not None and process.poll() is None:
                            try:
                                # Ensure process is terminated if it crashed
                                process.terminate()
                                process.wait(timeout=2)
                                if process.poll() is None:
                                    process.kill()
                                logging.info(
                                    f"Terminated process for {topic} (PID: {process.pid})")
                            except Exception as term_e:
                                logging.error(
                                    f"Error terminating process for {topic}: {term_e}")

                    if not ROSMarshaller._stop_event.is_set():
                        logging.info(
                            f"Retrying subscription to {topic} in {retry_delay:.1f}s")
                        time.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, max_delay)

            thread = threading.Thread(target=run, daemon=True)
            thread.start()
            ROSMarshaller._threads.append(thread)
            logging.info(f"Subscription thread started for topic: {topic}")
            return thread

    # --- Publisher Core ---

    @staticmethod
    def _clean_payload(json_data):
        """Parse and clean a message payload, stripping ROS/capture metadata keys."""
        _STRIP = frozenset(('topic', 'datatype', 'WARNING', 'WARN', 'ERROR', 'INFO', 'DEBUG'))
        if isinstance(json_data, str):
            if json_data.startswith("data: "):
                payload_data = json_data[6:].strip()
                try:
                    obj = json.loads(payload_data)
                except json.JSONDecodeError:
                    obj = {"data": payload_data}
            else:
                obj = json.loads(json_data)
        elif isinstance(json_data, dict):
            obj = json_data.copy()
        else:
            raise ValueError("json_data must be a dict or string")
        if isinstance(obj, dict):
            for k in _STRIP:
                obj.pop(k, None)
        return obj

    @staticmethod
    def publish(json_data, topic=None, datatype=None):
        """Single-shot publish. Spawns ros2 topic pub -1 and exits immediately."""
        if not ROSMarshaller.DEBUG_MODE and not ROSMarshaller.initialize():
            logging.error("ROS environment not initialized or detected. Cannot publish.")
            return
        try:
            obj = ROSMarshaller._clean_payload(json_data)
            pub_topic = topic or (obj.get('topic') if isinstance(obj, dict) else None)
            pub_datatype = datatype or (obj.get('datatype') if isinstance(obj, dict) else None)
            if not pub_topic or not pub_datatype:
                raise ValueError("topic and datatype required")
            if isinstance(obj, dict):
                obj.pop('topic', None)
                obj.pop('datatype', None)

            if ROSMarshaller.DEBUG_MODE:
                logging.debug(f"DEBUG PUBLISH to {pub_topic} ({pub_datatype}): {json.dumps(obj)}")
                ROSMarshaller._increment_tx_counter()
                return

            cmd = ['ros2', 'topic', 'pub', '-1', pub_topic, pub_datatype,
                   ROSMarshaller.shell_escape(json.dumps(obj))]
            subprocess.run(' '.join(cmd), shell=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=10)
            ROSMarshaller._increment_tx_counter()
        except Exception as e:
            logging.error(f"Failed to publish to {topic}: {e}")
            logging.debug(traceback.format_exc())

    @staticmethod
    def publish_persistent(topic, datatype, msg_dict, hz):
        """
        Start a persistent ros2 topic pub -r <hz> process.
        The topic stays visible in ros2 topic list for the lifetime of the process.
        Returns the Popen handle — caller must call stop_persistent() when done.
        """
        if not ROSMarshaller.DEBUG_MODE and not ROSMarshaller.initialize():
            raise RuntimeError("ROS environment not initialized")
        obj = ROSMarshaller._clean_payload(msg_dict)
        cmd = ['ros2', 'topic', 'pub', '-r', str(float(hz)),
               topic, datatype, ROSMarshaller.shell_escape(json.dumps(obj))]
        proc = subprocess.Popen(
            ' '.join(cmd), shell=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        logging.info(f"Persistent publisher started: {topic} @ {hz} Hz (PID {proc.pid})")
        return proc

    @staticmethod
    def stop_persistent(proc):
        """Terminate a persistent publisher process started by publish_persistent."""
        if proc is None or proc.poll() is not None:
            return
        try:
            os.killpg(os.getpgid(proc.pid), __import__('signal').SIGTERM)
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass
        try:
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        logging.info(f"Persistent publisher stopped (PID {proc.pid})")

    # --- Shutdown ---
    @staticmethod
    def stop():
        """Stops all running threads and processes."""
        logging.info("Stopping ROSMarshaller threads and processes...")
        ROSMarshaller._stop_event.set()

        # Stop all running subprocesses
        with ROSMarshaller._process_lock:
            for process in ROSMarshaller._process_pool.values():
                try:
                    if process.poll() is None:
                        process.terminate()
                except:
                    pass
            ROSMarshaller._process_pool.clear()

        # Wait for all custom threads to finish
        for thread in ROSMarshaller._threads:
            try:
                thread.join(timeout=1.0)
            except Exception as e:
                logging.error(f"Error joining thread: {e}")

        ROSMarshaller._threads = []
        logging.info(
            f"Final Metrics - TX Count: {ROSMarshaller._tx_count}, RX Count: {ROSMarshaller._rx_count}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='ROSMarshaller - ROS message processor')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')
    parser.add_argument(
        '--debug-file', default='data/debug_sample.yaml', help='File to read in debug mode')
    parser.add_argument('--topic', default='/chatter',
                        help='Topic to subscribe to')

    args = parser.parse_args()

    ROSMarshaller.initialize()
    if args.debug:
        ROSMarshaller.set_debug_mode(True, args.debug_file)

    topic = args.topic

    # Example callback function
    def print_json_callback(json_str, topic_name, datatype_str):
        data = json.loads(json_str)
        print(
            f"[{datetime.now().strftime('%H:%M:%S.%f')}] RCV on {topic_name}: {data['datatype']}")

    logging.info(f"Starting ROSMarshaller with topic: {topic}")

    # Start subscription
    sub_thread = ROSMarshaller.subscribe(topic, print_json_callback)

    try:
        # Simple publish example (assuming std_msgs/String for simplicity)
        if ROSMarshaller.initialize():
            time.sleep(5)
            logging.info("Testing publish...")
            publish_data = {"data": "Hello World from ROSMarshaller!"}
            ROSMarshaller.publish(publish_data, topic='/test_publish',
                                  datatype=ROSMarshaller.STD_MSGS_STRING_DATATYPE)

        while sub_thread.is_alive():
            time.sleep(1)
            metrics = ROSMarshaller.get_metrics()
            logging.info(
                f"Loop Metrics - TX: {metrics['tx_count']}, RX: {metrics['rx_count']}")
    except KeyboardInterrupt:
        logging.info("Stopping...")
    except Exception as e:
        logging.error(f"Main loop error: {e}")
    finally:
        ROSMarshaller.stop()
