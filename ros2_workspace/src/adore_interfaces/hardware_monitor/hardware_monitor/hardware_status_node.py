import glob
import json
import re
import socket
import subprocess

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

STATUS_TOPIC = '/cluster/hardware_status'


class HardwareStatusNode(Node):
    def __init__(self, context=None):
        super().__init__('hardware_status_node', context=context)

        self.declare_parameter('publish_rate_hz', 0.1)
        self.declare_parameter('node_name', '')
        self.declare_parameter('cpu_warn_percent', 85.0)
        self.declare_parameter('ram_warn_percent', 85.0)
        self.declare_parameter('disk_warn_percent', 85.0)
        self.declare_parameter('temp_warn_celsius', 80.0)

        rate = self.get_parameter('publish_rate_hz').get_parameter_value().double_value
        param_name = self.get_parameter('node_name').get_parameter_value().string_value.strip()
        self._node_name = param_name if param_name else socket.gethostname()
        self._topic_host = re.sub(r'[^a-zA-Z0-9_]', '_', self._node_name)
        self.get_logger().info(f'hardware_id resolved to: {self._node_name} (topic key: {self._topic_host})')

        # Per-host topic: /cluster/<hostname>/hardware_status
        status_topic = f'/cluster/{self._topic_host}/hardware_status'

        self._cpu_warn = self.get_parameter('cpu_warn_percent').get_parameter_value().double_value
        self._ram_warn = self.get_parameter('ram_warn_percent').get_parameter_value().double_value
        self._disk_warn = self.get_parameter('disk_warn_percent').get_parameter_value().double_value
        self._temp_warn = self.get_parameter('temp_warn_celsius').get_parameter_value().double_value

        self._pub = self.create_publisher(String, status_topic, 10)
        self._timer = self.create_timer(1.0 / rate, self._publish_status)

        try:
            import psutil
            self._psutil = psutil
            psutil.cpu_percent(interval=None, percpu=True)
        except ImportError:
            self._psutil = None
            self.get_logger().warning('psutil not available; some metrics will be missing')

        self.get_logger().info(f'HardwareStatusNode started on {self._node_name} @ {rate} Hz → {status_topic}')

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _warn_level(self, value: float, warn: float, error: float = 95.0) -> str:
        if value >= error:
            return 'error'
        if value >= warn:
            return 'warn'
        return 'ok'

    def _run_cmd(self, cmd: list[str], timeout: float = 2.0) -> str:
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout.strip()
        except Exception:
            return ''

    def _read_file(self, path: str) -> str:
        try:
            with open(path, 'r') as f:
                return f.read().strip()
        except OSError:
            return ''

    # ------------------------------------------------------------------
    # Collectors
    # ------------------------------------------------------------------

    def _collect_cpu(self) -> dict:
        if not self._psutil:
            return {'status': 'unavailable'}

        per_cpu = self._psutil.cpu_percent(interval=None, percpu=True)
        overall = round(sum(per_cpu) / len(per_cpu), 1) if per_cpu else 0.0
        freq = self._psutil.cpu_freq()
        load1, load5, load15 = self._psutil.getloadavg()

        result = {
            'overall_percent': overall,
            'status': self._warn_level(overall, self._cpu_warn),
            'load_avg': {'1m': round(load1, 2), '5m': round(load5, 2), '15m': round(load15, 2)},
            'per_core_percent': [round(p, 1) for p in per_cpu],
        }
        if freq:
            result['freq_mhz'] = round(freq.current, 1)
        return result

    def _collect_ram(self) -> dict:
        if not self._psutil:
            return {'status': 'unavailable'}

        mem = self._psutil.virtual_memory()
        swap = self._psutil.swap_memory()
        return {
            'status': self._warn_level(mem.percent, self._ram_warn),
            'total_mb': mem.total // (1024 ** 2),
            'used_mb': mem.used // (1024 ** 2),
            'available_mb': mem.available // (1024 ** 2),
            'used_percent': round(mem.percent, 1),
            'swap': {
                'total_mb': swap.total // (1024 ** 2),
                'used_mb': swap.used // (1024 ** 2),
                'used_percent': round(swap.percent, 1),
            },
        }

    def _collect_gpu(self) -> list[dict]:
        gpus = []

        nvidia_out = self._run_cmd([
            'nvidia-smi',
            '--query-gpu=name,utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu,power.draw',
            '--format=csv,noheader,nounits',
        ])
        for line in nvidia_out.splitlines():
            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 7:
                continue
            name, gpu_util, mem_util, mem_used, mem_total, temp, power = parts[:7]
            gpu_pct = float(gpu_util) if gpu_util.replace('.', '').isdigit() else 0.0
            temp_f = float(temp) if temp.replace('.', '').isdigit() else 0.0
            gpus.append({
                'type': 'GPU',
                'vendor': 'NVIDIA',
                'name': name,
                'status': self._warn_level(max(gpu_pct, temp_f), 85.0),
                'utilization_percent': gpu_pct,
                'memory_utilization_percent': float(mem_util) if mem_util.replace('.', '').isdigit() else 0.0,
                'memory_used_mb': int(mem_used) if mem_used.isdigit() else 0,
                'memory_total_mb': int(mem_total) if mem_total.isdigit() else 0,
                'temperature_celsius': temp_f,
                'power_draw_w': float(power) if power.replace('.', '').isdigit() else 0.0,
            })

        hailo_out = self._run_cmd(['hailortcli', 'monitor', '--json', '--count', '1'])
        if hailo_out:
            try:
                data = json.loads(hailo_out)
                for dev in data.get('devices', []):
                    util = float(dev.get('nn_core_utilization', 0))
                    gpus.append({
                        'type': 'NPU',
                        'vendor': 'Hailo',
                        'name': dev.get('device_id', 'hailo'),
                        'status': self._warn_level(util, 85.0),
                        'utilization_percent': util,
                        'temperature_celsius': dev.get('temperature', None),
                    })
            except Exception:
                pass

        return gpus

    def _collect_disk(self) -> dict:
        if not self._psutil:
            return {'status': 'unavailable'}

        mounts = {}
        worst = 'ok'
        for part in self._psutil.disk_partitions(all=False):
            try:
                usage = self._psutil.disk_usage(part.mountpoint)
                lvl = self._warn_level(usage.percent, self._disk_warn)
                if lvl == 'error' or (lvl == 'warn' and worst == 'ok'):
                    worst = lvl
                mounts[part.mountpoint] = {
                    'status': lvl,
                    'total_gb': round(usage.total / 1e9, 1),
                    'used_gb': round(usage.used / 1e9, 1),
                    'free_gb': round(usage.free / 1e9, 1),
                    'used_percent': round(usage.percent, 1),
                    'fstype': part.fstype,
                }
            except PermissionError:
                pass

        result: dict = {'status': worst, 'mounts': mounts}
        io = self._psutil.disk_io_counters()
        if io:
            result['io'] = {
                'total_read_mb': round(io.read_bytes / 1e6, 1),
                'total_write_mb': round(io.write_bytes / 1e6, 1),
                'read_count': io.read_count,
                'write_count': io.write_count,
            }
        return result

    def _collect_temperatures(self) -> dict:
        sensors: dict = {}
        worst = 'ok'

        if self._psutil and hasattr(self._psutil, 'sensors_temperatures'):
            for chip, readings in (self._psutil.sensors_temperatures() or {}).items():
                chip_data = {}
                for r in readings:
                    crit = r.critical if r.critical else 100.0
                    lvl = self._warn_level(r.current, self._temp_warn, crit)
                    if lvl == 'error' or (lvl == 'warn' and worst == 'ok'):
                        worst = lvl
                    label = r.label or chip
                    chip_data[label] = {
                        'celsius': round(r.current, 1),
                        'high': r.high,
                        'critical': r.critical,
                        'status': lvl,
                    }
                sensors[chip] = chip_data
        else:
            for temp_file in glob.glob('/sys/class/hwmon/hwmon*/temp*_input'):
                raw = self._read_file(temp_file)
                if raw.isdigit():
                    celsius = int(raw) / 1000.0
                    lvl = self._warn_level(celsius, self._temp_warn)
                    if lvl == 'error' or (lvl == 'warn' and worst == 'ok'):
                        worst = lvl
                    sensors[temp_file] = {'celsius': round(celsius, 1), 'status': lvl}

        return {'status': worst, 'sensors': sensors}

    def _collect_network(self) -> dict:
        if not self._psutil:
            return {'status': 'unavailable'}

        import socket as _socket
        AF_INET = _socket.AF_INET
        AF_INET6 = _socket.AF_INET6
        AF_PACKET = getattr(_socket, 'AF_PACKET', 17)

        addrs_map = self._psutil.net_if_addrs()
        stats_map = self._psutil.net_if_stats()
        counters_map = self._psutil.net_io_counters(pernic=True)

        interfaces = {}
        any_up = False

        for name, addrs in addrs_map.items():
            stats = stats_map.get(name)
            io = counters_map.get(name)
            is_up = stats.isup if stats else False
            if is_up:
                any_up = True

            mac = ''
            ipv4 = []
            ipv6 = []
            for a in addrs:
                fam = a.family if isinstance(a.family, int) else a.family.value
                if fam == AF_PACKET:
                    mac = a.address
                elif fam == AF_INET:
                    ipv4.append(a.address + (f'/{a.netmask}' if a.netmask else ''))
                elif fam == AF_INET6:
                    ipv6.append(a.address.split('%')[0])

            iface: dict = {
                'is_up': is_up,
                'mac': mac,
                'ipv4': ipv4,
                'ipv6': ipv6,
                'speed_mbps': stats.speed if stats else 0,
                'mtu': stats.mtu if stats else 0,
            }
            if io:
                iface['io'] = {
                    'bytes_sent_mb': round(io.bytes_sent / 1e6, 2),
                    'bytes_recv_mb': round(io.bytes_recv / 1e6, 2),
                    'packets_sent': io.packets_sent,
                    'packets_recv': io.packets_recv,
                    'errors_in': io.errin,
                    'errors_out': io.errout,
                    'drops_in': io.dropin,
                    'drops_out': io.dropout,
                }
            interfaces[name] = iface

        return {'status': 'ok' if any_up else 'warn', 'interfaces': interfaces}

    def _collect_ntp(self) -> dict:
        chrony = self._run_cmd(['chronyc', 'tracking'])
        if chrony and 'Reference ID' in chrony:
            data: dict = {'source': 'chrony', 'synchronized': True}
            for line in chrony.splitlines():
                if ':' in line:
                    key, _, val = line.partition(':')
                    data[key.strip().lower().replace(' ', '_')] = val.strip()
                    if key.strip() == 'System time':
                        m = re.search(r'([\d.]+)\s+seconds', val)
                        if m and float(m.group(1)) > 1.0:
                            data['synchronized'] = False
            data['status'] = 'ok' if data['synchronized'] else 'warn'
            return data

        timedatectl = self._run_cmd(['timedatectl', 'show'])
        if timedatectl:
            kv_map = {}
            for line in timedatectl.splitlines():
                if '=' in line:
                    k, _, v = line.partition('=')
                    kv_map[k.strip()] = v.strip()
            synced = kv_map.get('NTPSynchronized', '').lower() == 'yes'
            return {
                'source': 'systemd-timesyncd',
                'status': 'ok' if synced else 'warn',
                'synchronized': synced,
                **kv_map,
            }

        # Kernel adjtimex fallback - STA_UNSYNC bit 0x40
        timex_raw = self._read_file('/proc/timex')
        for line in timex_raw.splitlines():
            if line.startswith('status'):
                m = re.search(r'(\d+)', line)
                if m:
                    bits = int(m.group(1))
                    synced = not bool(bits & 0x40)
                    return {
                        'source': 'kernel',
                        'status': 'ok' if synced else 'warn',
                        'synchronized': synced,
                        'kernel_status_bits': hex(bits),
                    }

        return {'source': 'unknown', 'status': 'warn', 'synchronized': False}

    def _collect_processes(self) -> dict:
        if not self._psutil:
            return {'status': 'unavailable'}

        procs = list(self._psutil.process_iter(['status']))
        total = len(procs)
        sleeping = sum(1 for p in procs if p.info['status'] == self._psutil.STATUS_SLEEPING)
        running = sum(1 for p in procs if p.info['status'] == self._psutil.STATUS_RUNNING)
        zombie = sum(1 for p in procs if p.info['status'] == self._psutil.STATUS_ZOMBIE)

        return {
            'status': 'warn' if zombie > 5 else 'ok',
            'total': total,
            'running': running,
            'sleeping': sleeping,
            'zombie': zombie,
        }

    # ------------------------------------------------------------------

    def _publish_status(self):
        cpu = self._collect_cpu()
        ram = self._collect_ram()
        gpu = self._collect_gpu()
        disk = self._collect_disk()
        temperatures = self._collect_temperatures()
        network = self._collect_network()
        ntp = self._collect_ntp()
        processes = self._collect_processes()

        subsystem_statuses = [
            cpu.get('status', 'ok'),
            ram.get('status', 'ok'),
            disk.get('status', 'ok'),
            temperatures.get('status', 'ok'),
            network.get('status', 'ok'),
            ntp.get('status', 'ok'),
            processes.get('status', 'ok'),
        ]
        overall = 'error' if 'error' in subsystem_statuses else ('warn' if 'warn' in subsystem_statuses else 'ok')

        payload = {
            'hostname': self._node_name,
            'status': overall,
            'cpu': cpu,
            'ram': ram,
            'gpu': gpu,
            'disk': disk,
            'temperatures': temperatures,
            'network': network,
            'ntp': ntp,
            'processes': processes,
        }

        self._pub.publish(String(data=json.dumps(payload, indent=2)))
        self.get_logger().debug(f'Published hardware status (overall={overall})')


def main(args=None):
    rclpy.init(args=args)
    node = HardwareStatusNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
