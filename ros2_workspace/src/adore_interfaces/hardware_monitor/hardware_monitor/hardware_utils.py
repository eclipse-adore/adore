import os
import re
import glob
import socket
import subprocess
import platform


def _read(path: str, default: str = '') -> str:
    try:
        with open(path, 'r') as f:
            return f.read().strip()
    except OSError:
        return default


def _readlink_base(path: str) -> str:
    try:
        return os.path.basename(os.readlink(path))
    except OSError:
        return ''


def _run(cmd: list[str], timeout: float = 3.0) -> str:
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            env={**os.environ, 'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'},
        ).stdout.strip()
    except Exception:
        return ''


def _parse_cache_kb(s: str) -> int:
    m = re.match(r'(\d+)([KMG]?)', s.upper())
    if not m:
        return 0
    return int(m.group(1)) * {'K': 1, 'M': 1024, 'G': 1048576}.get(m.group(2), 1)


# ---------------------------------------------------------------------------
# PCI class code decoding
# ---------------------------------------------------------------------------

_PCI_BASE_CLASS = {
    0x00: 'Unclassified',    0x01: 'Mass Storage',
    0x02: 'Network',         0x03: 'Display',
    0x04: 'Multimedia',      0x05: 'Memory Controller',
    0x06: 'Bridge',          0x07: 'Communication',
    0x08: 'System Peripheral', 0x09: 'Input Device',
    0x0A: 'Docking Station', 0x0B: 'Processor',
    0x0C: 'Serial Bus',      0x0D: 'Wireless',
    0x0E: 'Intelligent I/O', 0x0F: 'Satellite',
    0x10: 'Encryption',      0x11: 'Signal Processing',
    0x12: 'Processing Accelerator', 0x40: 'Co-Processor',
    0xFF: 'Unassigned',
}

_PCI_SUBCLASS = {
    (0x01, 0x00): 'SCSI Bus',       (0x01, 0x01): 'IDE',
    (0x01, 0x05): 'ATA',            (0x01, 0x06): 'SATA (AHCI)',
    (0x01, 0x07): 'SAS',            (0x01, 0x08): 'NVMe',
    (0x02, 0x00): 'Ethernet',       (0x02, 0x01): 'Token Ring',
    (0x02, 0x02): 'FDDI',           (0x02, 0x80): 'Network (other)',
    (0x03, 0x00): 'VGA Compatible', (0x03, 0x01): '8514 Compatible',
    (0x03, 0x02): 'XGA',            (0x03, 0x80): 'GPU (other)',
    (0x04, 0x00): 'Video',          (0x04, 0x01): 'Audio',
    (0x04, 0x03): 'Audio Device',   (0x04, 0x80): 'Multimedia (other)',
    (0x06, 0x00): 'Host Bridge',    (0x06, 0x01): 'ISA Bridge',
    (0x06, 0x04): 'PCI-PCIe Bridge',(0x06, 0x09): 'PCI-PCI Bridge',
    (0x07, 0x00): 'Serial (UART)',  (0x07, 0x01): 'Parallel Port',
    (0x07, 0x03): 'Modem',          (0x07, 0x80): 'Communication (other)',
    (0x0B, 0x20): 'GPU (co-processor)',
    (0x0C, 0x00): 'FireWire',       (0x0C, 0x03): 'USB Controller',
    (0x0C, 0x04): 'Fibre Channel',  (0x0C, 0x05): 'SMBus',
    (0x0C, 0x06): 'InfiniBand',     (0x0C, 0x07): 'IPMI',
    (0x0D, 0x00): 'iRDA',           (0x0D, 0x11): 'Bluetooth',
    (0x0D, 0x12): 'Broadband',      (0x0D, 0x20): 'Wi-Fi 802.11a',
    (0x0D, 0x21): 'Wi-Fi 802.11b',  (0x0D, 0x80): 'Wireless (other)',
    (0x12, 0x00): 'Processing Accelerator', (0x12, 0x01): 'AI/ML Accelerator',
}


def _pci_class_label(class_hex: str) -> tuple[str, str]:
    """Return (base_label, subclass_label) from a 0xCCSSPP hex string."""
    try:
        v = int(class_hex, 16)
        base = (v >> 16) & 0xFF
        sub = (v >> 8) & 0xFF
        return (
            _PCI_BASE_CLASS.get(base, f'class_0x{base:02x}'),
            _PCI_SUBCLASS.get((base, sub), f'subclass_0x{sub:02x}'),
        )
    except (ValueError, TypeError):
        return ('unknown', 'unknown')


# ---------------------------------------------------------------------------
# System / OS
# ---------------------------------------------------------------------------

def get_system_info() -> dict:
    uname = platform.uname()
    return {
        'hostname': socket.gethostname(),
        'os': f'{uname.system} {uname.release}',
        'kernel': uname.release,
        'machine': uname.machine,
        'python': platform.python_version(),
    }


# ---------------------------------------------------------------------------
# CPU
# ---------------------------------------------------------------------------

def get_cpu_info() -> dict:
    info: dict = {
        'model': 'unknown',
        'architecture': platform.machine(),
        'byte_order': 'little-endian' if platform.processor() else platform.processor(),
        'logical_cores': 0,
        'physical_cores': 0,
        'base_frequency_mhz': 0.0,
        'cache': {},
        'numa_nodes': 1,
        'flags': [],
    }

    raw = _read('/proc/cpuinfo')
    physical_ids: set = set()
    core_ids: set = set()
    flags_seen = False

    for line in raw.splitlines():
        if line.startswith('model name') and info['model'] == 'unknown':
            info['model'] = line.split(':', 1)[-1].strip()
        elif line.startswith('Hardware') and info['model'] == 'unknown':
            info['model'] = line.split(':', 1)[-1].strip()
        elif line.startswith('physical id'):
            physical_ids.add(line.split(':', 1)[-1].strip())
        elif line.startswith('core id'):
            core_ids.add(line.split(':', 1)[-1].strip())
        elif line.startswith('flags') and not flags_seen:
            flags_seen = True
            important = {'avx', 'avx2', 'avx512f', 'sse4_2', 'aes', 'vmx', 'svm',
                         'hypervisor', 'lm', 'nx', 'cx16', 'rdrand', 'rdseed'}
            info['flags'] = sorted(important & set(line.split(':', 1)[-1].split()))
        elif line.startswith('cpu architecture'):
            info['architecture'] = line.split(':', 1)[-1].strip()

    info['logical_cores'] = len([l for l in raw.splitlines() if l.startswith('processor')])
    info['physical_cores'] = (
        len(core_ids) * max(len(physical_ids), 1) if core_ids else info['logical_cores']
    )

    freq = _read('/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq')
    if freq.isdigit():
        info['base_frequency_mhz'] = round(int(freq) / 1000.0, 1)

    cache: dict = {}
    for idx_path in glob.glob('/sys/devices/system/cpu/cpu0/cache/index*'):
        level = _read(os.path.join(idx_path, 'level'))
        ctype = _read(os.path.join(idx_path, 'type'))
        kb = _parse_cache_kb(_read(os.path.join(idx_path, 'size')))
        shared = _read(os.path.join(idx_path, 'shared_cpu_list'))
        if level == '1' and ctype == 'Data':
            cache['l1d_kb'] = kb
        elif level == '1' and ctype == 'Instruction':
            cache['l1i_kb'] = kb
        elif level == '2':
            cache['l2_kb'] = kb
        elif level == '3':
            cache['l3_kb'] = kb
            cache['l3_shared_cpus'] = shared
    info['cache'] = cache

    numa_dirs = glob.glob('/sys/devices/system/node/node[0-9]*')
    if numa_dirs:
        info['numa_nodes'] = len(numa_dirs)

    import struct
    info['byte_order'] = 'little-endian' if struct.pack('H', 1)[0] == 1 else 'big-endian'

    return info


# ---------------------------------------------------------------------------
# RAM
# ---------------------------------------------------------------------------

def get_ram_info() -> dict:
    info: dict = {'total_mb': 0, 'slots': [], 'numa_nodes': []}

    meminfo = _read('/proc/meminfo')
    for line in meminfo.splitlines():
        if line.startswith('MemTotal:'):
            m = re.search(r'(\d+)', line)
            if m:
                info['total_mb'] = int(m.group(1)) // 1024
            break

    # NUMA topology and per-node memory
    for node_path in sorted(glob.glob('/sys/devices/system/node/node[0-9]*')):
        node_id = re.search(r'node(\d+)', node_path)
        node_meminfo = _read(os.path.join(node_path, 'meminfo'))
        node_total = 0
        for line in node_meminfo.splitlines():
            if 'MemTotal' in line:
                m = re.search(r'(\d+) kB', line)
                if m:
                    node_total = int(m.group(1)) // 1024
        if node_id:
            cpus = _read(os.path.join(node_path, 'cpulist'))
            info['numa_nodes'].append({
                'node': int(node_id.group(1)),
                'total_mb': node_total,
                'cpus': cpus,
            })

    return info


# ---------------------------------------------------------------------------
# GPU / NPU / Accelerators
# ---------------------------------------------------------------------------

def get_accelerator_info() -> list[dict]:
    devices = []

    # NVIDIA via nvidia-smi
    out = _run(['nvidia-smi',
                '--query-gpu=index,name,uuid,memory.total,driver_version,pcie.link.gen.current,pcie.link.width.current',
                '--format=csv,noheader,nounits'])
    if out:
        for line in out.splitlines():
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 7:
                devices.append({
                    'type': 'GPU', 'vendor': 'NVIDIA',
                    'index': parts[0], 'name': parts[1], 'uuid': parts[2],
                    'vram_mb': int(parts[3]) if parts[3].isdigit() else 0,
                    'driver': parts[4],
                    'pcie_gen': parts[5], 'pcie_width': parts[6],
                })

    # AMD via rocm-smi
    if not any(d['vendor'] == 'NVIDIA' for d in devices):
        out = _run(['rocm-smi', '--showproductname', '--showmeminfo', 'vram', '--csv'])
        if out:
            for line in out.splitlines()[1:]:
                parts = [p.strip() for p in line.split(',')]
                if parts:
                    devices.append({'type': 'GPU', 'vendor': 'AMD', 'name': parts[-1],
                                    'vram_mb': 0, 'driver': '', 'uuid': ''})

    # Intel GPU via DRM sysfs
    for vpath in glob.glob('/sys/class/drm/card*/device/vendor'):
        if _read(vpath) == '0x8086':
            card_dir = os.path.dirname(os.path.dirname(vpath))
            uevent = _read(os.path.join(card_dir, 'device/uevent'))
            driver = _readlink_base(os.path.join(card_dir, 'device/driver'))
            name = next((l.split('=', 1)[-1] for l in uevent.splitlines() if 'PCI_ID' in l), 'Intel GPU')
            devices.append({'type': 'GPU', 'vendor': 'Intel', 'name': name,
                            'driver': driver, 'vram_mb': 0, 'uuid': ''})

    # Hailo NPU
    for dev in sorted(glob.glob('/dev/hailo*')):
        devices.append({'type': 'NPU', 'vendor': 'Hailo', 'name': f'Hailo NPU',
                        'device': dev, 'driver': 'hailo', 'vram_mb': 0})

    # Google Coral TPU
    for dev in sorted(glob.glob('/dev/apex_*')):
        devices.append({'type': 'TPU', 'vendor': 'Google', 'name': 'Coral Edge TPU',
                        'device': dev, 'driver': 'gasket', 'vram_mb': 0})

    # OpenCL devices via clinfo if available
    clinfo = _run(['clinfo', '--raw'], timeout=5.0)
    if clinfo and not devices:
        for line in clinfo.splitlines():
            if 'CL_DEVICE_NAME' in line:
                name = line.split('|')[-1].strip()
                devices.append({'type': 'GPU/OpenCL', 'vendor': 'unknown', 'name': name})

    return devices


# ---------------------------------------------------------------------------
# PCI devices
# ---------------------------------------------------------------------------

def get_pci_devices() -> list[dict]:
    devices = []
    for d in sorted(glob.glob('/sys/bus/pci/devices/*/')):
        slot = os.path.basename(d.rstrip('/'))
        vendor = _read(os.path.join(d, 'vendor'))
        device_id = _read(os.path.join(d, 'device'))
        class_hex = _read(os.path.join(d, 'class'))
        sub_vendor = _read(os.path.join(d, 'subsystem_vendor'))
        sub_device = _read(os.path.join(d, 'subsystem_device'))
        revision = _read(os.path.join(d, 'revision'))
        driver = _readlink_base(os.path.join(d, 'driver'))
        numa = _read(os.path.join(d, 'numa_node'))
        base_label, sub_label = _pci_class_label(class_hex)
        devices.append({
            'slot': slot,
            'vendor_id': vendor,
            'device_id': device_id,
            'subsystem_vendor_id': sub_vendor,
            'subsystem_device_id': sub_device,
            'class': class_hex,
            'class_label': base_label,
            'subclass_label': sub_label,
            'revision': revision,
            'driver': driver,
            'numa_node': int(numa) if numa.lstrip('-').isdigit() else None,
        })
    return devices


# ---------------------------------------------------------------------------
# USB devices  (sysfs - no lsusb required)
# ---------------------------------------------------------------------------

_USB_CLASS = {
    '00': 'Per-Interface',   '01': 'Audio',       '02': 'CDC/Serial',
    '03': 'HID',             '05': 'Physical',    '06': 'Image',
    '07': 'Printer',         '08': 'Mass Storage','09': 'Hub',
    '0a': 'CDC-Data',        '0b': 'Smart Card',  '0d': 'Content Security',
    '0e': 'Video',           '0f': 'PHDC',        '10': 'AV',
    'dc': 'Diagnostic',      'e0': 'Wireless',    'ef': 'Miscellaneous',
    'fe': 'App Specific',    'ff': 'Vendor Specific',
}


def get_usb_devices() -> list[dict]:
    devices = []
    for d in sorted(glob.glob('/sys/bus/usb/devices/*/')):
        # Only real devices have idVendor (not hubs/ports that lack it)
        id_vendor = _read(os.path.join(d, 'idVendor'))
        id_product = _read(os.path.join(d, 'idProduct'))
        if not id_vendor:
            continue

        dev_class = _read(os.path.join(d, 'bDeviceClass')).lower()
        speed = _read(os.path.join(d, 'speed'))
        manufacturer = _read(os.path.join(d, 'manufacturer'))
        product = _read(os.path.join(d, 'product'))
        serial = _read(os.path.join(d, 'serial'))
        bus = _read(os.path.join(d, 'busnum'))
        devnum = _read(os.path.join(d, 'devnum'))
        version = _read(os.path.join(d, 'version')).strip()

        # Collect bound interface drivers
        drivers = list({
            _readlink_base(os.path.join(d, iface, 'driver'))
            for iface in os.listdir(d)
            if re.match(r'\d+-[\d.]+:\d+\.\d+', iface)
            and os.path.exists(os.path.join(d, iface, 'driver'))
        } - {''})

        devices.append({
            'bus': bus,
            'device': devnum,
            'id': f'{id_vendor}:{id_product}',
            'vendor_id': id_vendor,
            'product_id': id_product,
            'manufacturer': manufacturer,
            'product': product,
            'serial': serial,
            'usb_version': version,
            'speed_mbps': speed,
            'class': dev_class,
            'class_label': _USB_CLASS.get(dev_class, f'0x{dev_class}'),
            'drivers': drivers,
        })
    return devices


# ---------------------------------------------------------------------------
# Serial / UART devices
# ---------------------------------------------------------------------------

_UART_TYPES = {
    '0': 'unknown', '1': '8250',   '2': '16450', '3': '16550',
    '4': '16550A',  '5': 'Cirrus', '6': '16650V2','7': '16750',
    '12': '16950/954', '14': 'RSA',
}


def get_serial_devices() -> list[dict]:
    devices = []

    # Registered serial drivers from /proc/tty/drivers
    registered: dict[str, str] = {}
    for line in _read('/proc/tty/drivers').splitlines():
        parts = line.split()
        if len(parts) >= 2:
            registered[parts[1]] = parts[0]  # /dev/ttyX -> driver name

    for d in sorted(glob.glob('/sys/class/tty/*/')):
        name = os.path.basename(d.rstrip('/'))
        dev_node = f'/dev/{name}'

        # Must have a real device link (excludes virtual ttys, pts, etc.)
        dev_link = None
        try:
            dev_link = os.readlink(os.path.join(d, 'device'))
        except OSError:
            pass
        if dev_link is None:
            continue

        driver = _readlink_base(os.path.join(d, 'device', 'driver'))
        subsystem = _readlink_base(os.path.join(d, 'device', 'subsystem'))

        # Categorise by subsystem/driver
        if subsystem == 'usb-serial' or 'USB' in name:
            port_type = 'USB-Serial'
        elif subsystem == 'usb':
            port_type = 'USB-Serial'
        elif 'ACM' in name:
            port_type = 'USB-CDC-ACM'
        elif 'AMA' in name or 'serial8250' in driver:
            port_type = 'UART (SoC/ARM)'
        elif name.startswith('ttyS'):
            port_type = 'UART (16550)'
        else:
            port_type = 'Serial'

        entry: dict = {
            'device': dev_node,
            'name': name,
            'type': port_type,
            'driver': driver,
            'subsystem': subsystem,
        }

        # Extra fields for native UARTs
        if name.startswith('ttyS'):
            uart_type_num = _read(os.path.join(d, 'type'))
            entry['uart_type'] = _UART_TYPES.get(uart_type_num, uart_type_num)
            entry['port_address'] = _read(os.path.join(d, 'port'))
            entry['irq'] = _read(os.path.join(d, 'irq'))
            entry['uartclk_hz'] = _read(os.path.join(d, 'uartclk'))
            entry['is_console'] = _read(os.path.join(d, 'console')) == 'Y'

        # USB-serial: gather parent USB device info
        if port_type in ('USB-Serial', 'USB-CDC-ACM'):
            usb_dir = dev_link
            for _ in range(4):
                usb_dir = os.path.join(os.path.dirname(usb_dir), '')
                mfr = _read(os.path.join('/sys/bus/usb/devices',
                                          os.path.normpath(usb_dir), 'manufacturer'))
                if mfr:
                    entry['usb_manufacturer'] = mfr
                    entry['usb_product'] = _read(os.path.join(
                        '/sys/bus/usb/devices', os.path.normpath(usb_dir), 'product'))
                    entry['usb_serial'] = _read(os.path.join(
                        '/sys/bus/usb/devices', os.path.normpath(usb_dir), 'serial'))
                    break

        devices.append(entry)

    return devices


# ---------------------------------------------------------------------------
# Network interfaces
# ---------------------------------------------------------------------------

def get_network_interfaces() -> list[dict]:
    ifaces = []
    try:
        import psutil
        AF_INET = socket.AF_INET
        AF_INET6 = socket.AF_INET6
        AF_PACKET = getattr(socket, 'AF_PACKET', 17)

        addrs_map = psutil.net_if_addrs()
        stats_map = psutil.net_if_stats()

        for name, addrs in addrs_map.items():
            stats = stats_map.get(name)
            mac, ipv4, ipv6 = '', [], []
            for a in addrs:
                fam = a.family if isinstance(a.family, int) else a.family.value
                if fam == AF_PACKET:
                    mac = a.address
                elif fam == AF_INET:
                    ipv4.append(a.address + (f'/{a.netmask}' if a.netmask else ''))
                elif fam == AF_INET6:
                    ipv6.append(a.address.split('%')[0])

            sys_path = f'/sys/class/net/{name}/'
            driver = _readlink_base(os.path.join(sys_path, 'device', 'driver'))
            iface_type_raw = _read(os.path.join(sys_path, 'type'))
            duplex = _read(os.path.join(sys_path, 'duplex'))
            operstate = _read(os.path.join(sys_path, 'operstate'))
            tx_queue = _read(os.path.join(sys_path, 'tx_queue_len'))

            # Ethernet=1, loopback=772, WiFi=801, tunnel/tun=65534
            iface_type_map = {
                '1': 'ethernet', '772': 'loopback', '801': 'wifi',
                '65534': 'tunnel', '65535': 'unknown',
            }
            iface_type = iface_type_map.get(iface_type_raw, f'type_{iface_type_raw}')

            # WiFi: check /sys/class/net/<if>/wireless or /proc/net/wireless
            if os.path.isdir(os.path.join(sys_path, 'wireless')):
                iface_type = 'wifi'
                phy = _readlink_base(os.path.join(sys_path, 'phy80211'))
                ssid = _run(['iwgetid', name, '-r'], timeout=1.0)
            else:
                phy = ''
                ssid = ''

            ifaces.append({
                'name': name,
                'type': iface_type,
                'operstate': operstate,
                'is_up': stats.isup if stats else False,
                'mac': mac,
                'ipv4': ipv4,
                'ipv6': ipv6,
                'speed_mbps': stats.speed if stats else 0,
                'mtu': stats.mtu if stats else 0,
                'duplex': duplex,
                'tx_queue_len': int(tx_queue) if tx_queue.isdigit() else 0,
                'driver': driver,
                **({'phy': phy, 'ssid': ssid} if iface_type == 'wifi' else {}),
            })
    except ImportError:
        pass
    return ifaces


# ---------------------------------------------------------------------------
# Storage devices
# ---------------------------------------------------------------------------

def get_storage_devices() -> list[dict]:
    devices = []
    out = _run(['lsblk', '-d', '-o', 'NAME,SIZE,MODEL,ROTA,TYPE,TRAN,VENDOR,REV,SERIAL,LOG-SEC,PHY-SEC', '--json'])
    if not out:
        out = _run(['lsblk', '-d', '-o', 'NAME,SIZE,MODEL,ROTA,TYPE,TRAN,VENDOR', '--json'])
    if out:
        import json
        try:
            for dev in json.loads(out).get('blockdevices', []):
                name = dev.get('name', '')
                rota = dev.get('rota', '0')
                tran = dev.get('tran') or ''
                if tran == 'nvme' or name.startswith('nvme'):
                    storage_type = 'NVMe SSD'
                elif str(rota) in ('0', 'false', 'False'):
                    storage_type = 'SSD'
                elif tran in ('usb',):
                    storage_type = 'USB Storage'
                else:
                    storage_type = 'HDD'

                entry: dict = {
                    'name': name,
                    'device': f'/dev/{name}',
                    'size': dev.get('size', ''),
                    'model': (dev.get('model') or '').strip(),
                    'vendor': (dev.get('vendor') or '').strip(),
                    'revision': (dev.get('rev') or '').strip(),
                    'serial': (dev.get('serial') or '').strip(),
                    'type': storage_type,
                    'transport': tran,
                    'rotational': str(rota) not in ('0', 'false', 'False'),
                }

                # Partition count
                partitions = glob.glob(f'/sys/block/{name}/{name}[0-9]*')
                entry['partitions'] = len(partitions)

                # Logical/physical sector size
                for field, sysfs in [('logical_sector_bytes', 'queue/logical_block_size'),
                                      ('physical_sector_bytes', 'queue/physical_block_size')]:
                    val = _read(f'/sys/block/{name}/{sysfs}')
                    if val.isdigit():
                        entry[field] = int(val)

                # Rotational speed for HDDs
                rpm = _read(f'/sys/block/{name}/queue/rotational')
                if rpm.isdigit() and int(rpm) == 1:
                    entry['rpm'] = 'rotational'

                devices.append(entry)
        except Exception:
            pass
    return devices


# ---------------------------------------------------------------------------
# Sensors (IIO, V4L2, LIDAR patterns)
# ---------------------------------------------------------------------------

def get_sensor_devices() -> list[dict]:
    sensors = []

    for dev_path in sorted(glob.glob('/sys/bus/iio/devices/iio:device*')):
        name = _read(os.path.join(dev_path, 'name'), default='unknown_iio')
        attrs = set(os.listdir(dev_path))
        if any('accel' in a for a in attrs):
            stype = 'IMU/Accelerometer'
        elif any('anglvel' in a for a in attrs):
            stype = 'IMU/Gyroscope'
        elif any('magn' in a for a in attrs):
            stype = 'Magnetometer'
        elif any('pressure' in a for a in attrs):
            stype = 'Barometer'
        elif any('illuminance' in a for a in attrs):
            stype = 'Ambient Light'
        elif any('proximity' in a for a in attrs):
            stype = 'Proximity'
        elif any('temp' in a for a in attrs):
            stype = 'Temperature Sensor'
        else:
            stype = 'IIO'
        dev_node = _read(os.path.join(dev_path, 'dev'))
        sensors.append({
            'name': name, 'type': stype, 'interface': 'IIO',
            'sysfs_path': dev_path, 'dev': dev_node,
        })

    for dev in sorted(glob.glob('/dev/video*')):
        sys_name = f'/sys/class/video4linux/{os.path.basename(dev)}'
        name = _read(os.path.join(sys_name, 'name'), default=dev)
        driver = _readlink_base(os.path.join(sys_name, 'device', 'driver'))
        sensors.append({
            'name': name, 'type': 'Camera/V4L2', 'interface': 'V4L2',
            'device': dev, 'driver': driver,
        })

    return sensors


# ---------------------------------------------------------------------------
# Sound / Audio
# ---------------------------------------------------------------------------

def get_audio_devices() -> list[dict]:
    devices = []
    cards_raw = _read('/proc/asound/cards')
    for line in cards_raw.splitlines():
        m = re.match(r'\s*(\d+)\s+\[(\S+)\s*\]:\s+(.+)', line)
        if m:
            idx, short_name, description = m.groups()
            devices.append({
                'card_index': int(idx),
                'name': short_name,
                'description': description.strip(),
            })

    # Enrich with driver info from sysfs
    for d in glob.glob('/sys/class/sound/card*/'):
        card_num = re.search(r'card(\d+)', d)
        if not card_num:
            continue
        driver = _readlink_base(os.path.join(d, 'device', 'driver'))
        for dev in devices:
            if dev['card_index'] == int(card_num.group(1)):
                dev['driver'] = driver
                break

    return devices


# ---------------------------------------------------------------------------
# Input devices (keyboard, mouse, joystick, etc.)
# ---------------------------------------------------------------------------

def get_input_devices() -> list[dict]:
    devices = []
    for d in sorted(glob.glob('/sys/class/input/input*/')):
        name = _read(os.path.join(d, 'name'))
        if not name:
            continue
        phys = _read(os.path.join(d, 'phys'))
        uniq = _read(os.path.join(d, 'uniq'))
        # Guess type from name/phys
        name_lower = name.lower()
        if any(k in name_lower for k in ('keyboard', 'kbd')):
            itype = 'Keyboard'
        elif any(k in name_lower for k in ('mouse', 'trackpad', 'touchpad')):
            itype = 'Mouse/Touchpad'
        elif any(k in name_lower for k in ('joystick', 'gamepad', 'controller')):
            itype = 'Gamepad/Joystick'
        elif 'touch' in name_lower:
            itype = 'Touchscreen'
        elif any(k in name_lower for k in ('power', 'button', 'acpi')):
            itype = 'System Button'
        else:
            itype = 'Input Device'

        # Find associated /dev/input/eventX
        event_nodes = [
            f'/dev/input/{e}'
            for e in os.listdir(d)
            if e.startswith('event')
        ]
        devices.append({
            'name': name, 'type': itype,
            'phys': phys, 'uniq': uniq,
            'event_nodes': event_nodes,
        })
    return devices


# ---------------------------------------------------------------------------
# Power supply / Battery
# ---------------------------------------------------------------------------

def get_power_info() -> list[dict]:
    supplies = []
    for d in sorted(glob.glob('/sys/class/power_supply/*/')):
        name = os.path.basename(d.rstrip('/'))
        ptype = _read(os.path.join(d, 'type'))
        status = _read(os.path.join(d, 'status'))
        entry: dict = {'name': name, 'type': ptype, 'status': status}
        if ptype == 'Battery':
            for field, sysfs in [
                ('capacity_percent', 'capacity'),
                ('capacity_level', 'capacity_level'),
                ('voltage_mv', 'voltage_now'),
                ('energy_full_wh', 'energy_full'),
                ('energy_now_wh', 'energy_now'),
                ('power_now_w', 'power_now'),
                ('cycle_count', 'cycle_count'),
                ('technology', 'technology'),
                ('manufacturer', 'manufacturer'),
                ('model', 'model_name'),
            ]:
                val = _read(os.path.join(d, sysfs))
                if val:
                    if field.endswith('_mv') or field.endswith('_wh') or field.endswith('_w'):
                        try:
                            entry[field] = round(int(val) / 1_000_000, 3)
                        except ValueError:
                            entry[field] = val
                    elif field == 'capacity_percent':
                        entry[field] = int(val) if val.isdigit() else val
                    else:
                        entry[field] = val
        elif ptype == 'Mains':
            entry['online'] = _read(os.path.join(d, 'online')) == '1'
        supplies.append(entry)
    return supplies
