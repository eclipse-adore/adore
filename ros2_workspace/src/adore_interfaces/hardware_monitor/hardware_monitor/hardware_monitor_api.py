"""
hardware_monitor_api.py

Flask blueprint for the hardware monitor cluster API.

Nodes are launched in-process in threads rather than via `ros2 run`, so they
work regardless of whether `ros2` is on PATH or the workspace is sourced in
the shell that started the Flask server.
"""

import json
import logging
import os
import sys
import threading
import time
from datetime import datetime, timezone

from flask import Blueprint, jsonify, Response

logger = logging.getLogger(__name__)

_PKG_DIR    = os.path.dirname(os.path.abspath(__file__))
_PKG_PARENT = os.path.dirname(_PKG_DIR)

# ---------------------------------------------------------------------------
# Per-host cache
# ---------------------------------------------------------------------------

_hosts: dict = {}
_hosts_lock = threading.Lock()


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def _store(host: str, kind: str, data: dict):
    ts = _ts()
    with _hosts_lock:
        if host not in _hosts:
            _hosts[host] = {
                'status': None, 'status_ts': None,
                'inventory': None, 'inventory_ts': None,
            }
        _hosts[host][kind] = data
        _hosts[host][f'{kind}_ts'] = ts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_path():
    if _PKG_PARENT not in sys.path:
        sys.path.insert(0, _PKG_PARENT)


def _make_executor(ctx):
    """Return a SingleThreadedExecutor bound to ctx."""
    from rclpy.executors import SingleThreadedExecutor
    return SingleThreadedExecutor(context=ctx)


def _spin_node(node, ctx):
    """Spin a node using an executor tied to its context."""
    executor = _make_executor(ctx)
    executor.add_node(node)
    executor.spin()


# ---------------------------------------------------------------------------
# In-process node supervisor
# ---------------------------------------------------------------------------

_node_threads: dict = {}
_node_status: dict  = {}
_node_lock = threading.Lock()
_supervisor_started = False


def _run_node_thread(node_name: str):
    _ensure_path()
    restarts = 0
    while True:
        with _node_lock:
            _node_status[node_name] = {
                'running': False, 'restarts': restarts, 'last_error': None,
            }
        ctx = None
        try:
            import rclpy
            from rclpy.context import Context

            ctx = Context()
            rclpy.init(context=ctx)

            if node_name == 'hardware_discovery_node':
                from hardware_monitor.hardware_discovery_node import HardwareDiscoveryNode
                node = HardwareDiscoveryNode(context=ctx)
            elif node_name == 'hardware_status_node':
                from hardware_monitor.hardware_status_node import HardwareStatusNode
                node = HardwareStatusNode(context=ctx)
            else:
                raise ValueError(f'Unknown node: {node_name}')

            with _node_lock:
                _node_status[node_name]['running'] = True

            logger.info(f'hardware_monitor: {node_name} running')
            _spin_node(node, ctx)

        except Exception as e:
            err = str(e)
            logger.error(f'hardware_monitor: {node_name} crashed: {err}', exc_info=True)
            with _node_lock:
                _node_status[node_name] = {
                    'running': False, 'restarts': restarts, 'last_error': err,
                }
        finally:
            if ctx is not None:
                try:
                    import rclpy
                    rclpy.shutdown(context=ctx)
                except Exception:
                    pass

        restarts += 1
        logger.info(f'hardware_monitor: restarting {node_name} in 5s (restart #{restarts})')
        time.sleep(5.0)


def _start_node_supervisor():
    global _supervisor_started
    if _supervisor_started:
        return
    _supervisor_started = True
    for node_name in ('hardware_discovery_node', 'hardware_status_node'):
        t = threading.Thread(
            target=_run_node_thread, args=(node_name,),
            daemon=True, name=f'hw-node-{node_name}',
        )
        t.start()
        with _node_lock:
            _node_threads[node_name] = t
        logger.info(f'hardware_monitor: supervisor thread started for {node_name}')


# ---------------------------------------------------------------------------
# ROS subscriber thread
# ---------------------------------------------------------------------------

_ros_subscriber_started = False


def _start_ros_subscribers():
    global _ros_subscriber_started
    if _ros_subscriber_started:
        return
    _ros_subscriber_started = True

    def _spin():
        _ensure_path()
        ctx = None
        try:
            import rclpy
            from rclpy.context import Context
            from rclpy.node import Node
            from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
            from std_msgs.msg import String

            ctx = Context()
            rclpy.init(context=ctx)

            latched_qos = QoSProfile(
                depth=1,
                durability=DurabilityPolicy.TRANSIENT_LOCAL,
                reliability=ReliabilityPolicy.RELIABLE,
            )

            class _CacheNode(Node):
                def __init__(self):
                    super().__init__('hardware_monitor_api', context=ctx)
                    self._subs: dict = {}
                    self._latched = latched_qos
                    self.create_timer(5.0, self._discover)
                    self._discover()

                def _discover(self):
                    for name, types in self.get_topic_names_and_types():
                        if 'std_msgs/msg/String' not in types:
                            continue
                        if name in self._subs:
                            continue
                        parts = name.split('/')
                        # Expect: ['', 'cluster', '<host>', 'hardware_inventory|hardware_status']
                        if len(parts) != 4 or parts[1] != 'cluster':
                            continue
                        kind = parts[3]
                        if kind not in ('hardware_inventory', 'hardware_status'):
                            continue
                        host = parts[2]
                        qos = self._latched if kind == 'hardware_inventory' else 10
                        self._subs[name] = self.create_subscription(
                            String, name,
                            lambda msg, h=host, k=kind: self._on_msg(msg, h, k),
                            qos,
                        )
                        logger.info(f'hardware_monitor: subscribed to {name}')

                def _on_msg(self, msg, host: str, kind: str):
                    try:
                        data = json.loads(msg.data)
                        # Prefer the real hostname from the payload over the
                        # sanitized topic segment (e.g. 'ADORe-CLI' vs 'ADORe_CLI')
                        cache_key = data.get('hostname') or host
                        _store(cache_key, kind.replace('hardware_', ''), data)
                    except Exception as e:
                        logger.warning(f'hardware_monitor parse error ({host}/{kind}): {e}')

            node = _CacheNode()
            _spin_node(node, ctx)

        except Exception as e:
            logger.error(f'hardware_monitor: ROS subscriber crashed: {e}', exc_info=True)
        finally:
            if ctx is not None:
                try:
                    import rclpy
                    rclpy.shutdown(context=ctx)
                except Exception:
                    pass

    threading.Thread(target=_spin, daemon=True, name='hw-monitor-ros').start()
    logger.info('hardware_monitor: ROS subscriber thread started')


# ---------------------------------------------------------------------------
# Blueprint factory
# ---------------------------------------------------------------------------

def get_hardware_monitor_blueprint(url_prefix: str = '/api/hardware') -> Blueprint:
    _start_node_supervisor()
    _start_ros_subscribers()

    bp = Blueprint('hardware_monitor', __name__, url_prefix=url_prefix)

    @bp.route('/hosts')
    def hosts():
        with _hosts_lock:
            result = {
                host: {
                    'status_available':    e['status'] is not None,
                    'status_ts':           e['status_ts'],
                    'inventory_available': e['inventory'] is not None,
                    'inventory_ts':        e['inventory_ts'],
                }
                for host, e in _hosts.items()
            }
        return jsonify({'hosts': result, 'count': len(result)})

    @bp.route('/hosts/<host>/status')
    def host_status(host):
        with _hosts_lock:
            entry = _hosts.get(host)
        if not entry or entry['status'] is None:
            return jsonify({'available': False, 'host': host,
                            'message': f'No status data for {host}'}), 202
        return jsonify({'available': True, 'host': host,
                        'received_at': entry['status_ts'],
                        'data': entry['status']})

    @bp.route('/hosts/<host>/inventory')
    def host_inventory(host):
        with _hosts_lock:
            entry = _hosts.get(host)
        if not entry or entry['inventory'] is None:
            return jsonify({'available': False, 'host': host,
                            'message': f'No inventory data for {host}'}), 202
        return jsonify({'available': True, 'host': host,
                        'received_at': entry['inventory_ts'],
                        'data': entry['inventory']})

    @bp.route('/hosts/<host>/stream')
    def host_stream(host):
        def generate():
            last_ts = None
            yield 'retry: 3000\n\n'
            while True:
                with _hosts_lock:
                    entry = _hosts.get(host, {})
                    data = entry.get('status')
                    ts   = entry.get('status_ts')
                if data is not None and ts != last_ts:
                    last_ts = ts
                    yield f'data: {json.dumps({"host": host, "received_at": ts, "data": data})}\n\n'
                else:
                    yield ': keepalive\n\n'
                time.sleep(1.0)
        return Response(generate(), mimetype='text/event-stream',
                        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

    @bp.route('/stream')
    def stream_all():
        def generate():
            last_seen: dict = {}
            yield 'retry: 3000\n\n'
            while True:
                with _hosts_lock:
                    snapshot = {
                        h: (e['status'], e['status_ts']) for h, e in _hosts.items()
                    }
                for host, (data, ts) in snapshot.items():
                    if data is not None and ts != last_seen.get(host):
                        last_seen[host] = ts
                        yield f'data: {json.dumps({"host": host, "received_at": ts, "data": data})}\n\n'
                yield ': keepalive\n\n'
                time.sleep(1.0)
        return Response(generate(), mimetype='text/event-stream',
                        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

    @bp.route('/nodes/status')
    def nodes_status():
        with _node_lock:
            status  = dict(_node_status)
            threads = {n: t.is_alive() for n, t in _node_threads.items()}
        return jsonify({'nodes': status, 'threads_alive': threads})

    @bp.route('/cache/status')
    def cache_status():
        with _hosts_lock:
            return jsonify({
                'host_count': len(_hosts),
                'hosts': {
                    host: {
                        'inventory_available': e['inventory'] is not None,
                        'inventory_ts':        e['inventory_ts'],
                        'status_available':    e['status'] is not None,
                        'status_ts':           e['status_ts'],
                    }
                    for host, e in _hosts.items()
                },
            })

    return bp
