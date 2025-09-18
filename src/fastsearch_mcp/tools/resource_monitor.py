"""System resource monitoring tool for MCP."""
import asyncio
import platform
import psutil
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

from fastsearch_mcp.tools.base import BaseTool, ToolCategory, ToolParameter, tool
from fastsearch_mcp.logging_config import get_logger

logger = get_logger(__name__)

class SystemMetricsCollector:
    """Collects system metrics including CPU, memory, disk, and network usage."""
    
    def __init__(self):
        self._last_net_io = psutil.net_io_counters()
        self._last_disk_io = psutil.disk_io_counters()
        self._last_cpu_times = psutil.cpu_times()
        self._last_time = time.time()
    
    def collect_cpu_usage(self) -> Dict[str, float]:
        """Collect CPU usage statistics."""
        try:
            # Get per-core usage
            per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
            
            # Get system-wide CPU times
            cpu_times = psutil.cpu_times()
            
            # Calculate CPU usage percentages
            total_time = sum(cpu_times)
            if hasattr(self, '_last_cpu_times'):
                last_total = sum(self._last_cpu_times)
                delta_total = total_time - last_total
                
                if delta_total > 0:  # Avoid division by zero
                    cpu_percent = {
                        'user': (cpu_times.user - self._last_cpu_times.user) / delta_total * 100,
                        'system': (cpu_times.system - self._last_cpu_times.system) / delta_total * 100,
                        'idle': (cpu_times.idle - self._last_cpu_times.idle) / delta_total * 100,
                    }
                else:
                    cpu_percent = {'user': 0, 'system': 0, 'idle': 100}
            else:
                cpu_percent = {'user': 0, 'system': 0, 'idle': 100}
            
            self._last_cpu_times = cpu_times
            
            return {
                'percent': psutil.cpu_percent(interval=None),  # System-wide usage
                'per_cpu': per_cpu,  # Per-core usage
                'times': cpu_percent,  # User/System/Idle breakdown
                'count': psutil.cpu_count(),  # Number of CPU cores
                'freq': {
                    'current': psutil.cpu_freq().current if hasattr(psutil, 'cpu_freq') and psutil.cpu_freq() else None,
                    'max': psutil.cpu_freq().max if hasattr(psutil, 'cpu_freq') and psutil.cpu_freq() else None
                } if hasattr(psutil, 'cpu_freq') else None,
                'load_avg': dict(zip(['1min', '5min', '15min'], os.getloadavg())) if hasattr(os, 'getloadavg') else None
            }
            
        except Exception as e:
            logger.error("Error collecting CPU metrics: %s", e, exc_info=True)
            return {}
    
    def collect_memory_usage(self) -> Dict[str, Union[float, Dict]]:
        """Collect memory usage statistics."""
        try:
            virtual_mem = psutil.virtual_memory()
            swap_mem = psutil.swap_memory()
            
            return {
                'virtual': {
                    'total': virtual_mem.total,
                    'available': virtual_mem.available,
                    'used': virtual_mem.used,
                    'free': virtual_mem.free,
                    'percent': virtual_mem.percent,
                    'used_percent': virtual_mem.percent,
                    'free_percent': 100 - virtual_mem.percent
                },
                'swap': {
                    'total': swap_mem.total,
                    'used': swap_mem.used,
                    'free': swap_mem.free,
                    'percent': swap_mem.percent,
                    'sin': swap_mem.sin if hasattr(swap_mem, 'sin') else None,
                    'sout': swap_mem.sout if hasattr(swap_mem, 'sout') else None
                }
            }
        except Exception as e:
            logger.error("Error collecting memory metrics: %s", e, exc_info=True)
            return {}
    
    def collect_disk_usage(self) -> Dict[str, Dict]:
        """Collect disk usage and I/O statistics."""
        try:
            # Get disk partitions
            partitions = []
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    partitions.append({
                        'device': part.device,
                        'mountpoint': part.mountpoint,
                        'fstype': part.fstype,
                        'opts': part.opts,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent
                    })
                except Exception as e:
                    logger.debug("Error getting disk usage for %s: %s", part.mountpoint, e)
            
            # Get disk I/O counters
            disk_io = psutil.disk_io_counters()
            io_stats = {}
            
            if hasattr(self, '_last_disk_io') and disk_io:
                time_delta = time.time() - self._last_time
                if time_delta > 0:
                    io_stats = {
                        'read_count': disk_io.read_count,
                        'write_count': disk_io.write_count,
                        'read_bytes': disk_io.read_bytes,
                        'write_bytes': disk_io.write_bytes,
                        'read_time': disk_io.read_time,
                        'write_time': disk_io.write_time,
                        'read_bytes_per_sec': (disk_io.read_bytes - self._last_disk_io.read_bytes) / time_delta,
                        'write_bytes_per_sec': (disk_io.write_bytes - self._last_disk_io.write_bytes) / time_delta,
                        'read_count_per_sec': (disk_io.read_count - self._last_disk_io.read_count) / time_delta,
                        'write_count_per_sec': (disk_io.write_count - self._last_disk_io.write_count) / time_delta
                    }
            
            self._last_disk_io = disk_io
            
            return {
                'partitions': partitions,
                'io': io_stats
            }
            
        except Exception as e:
            logger.error("Error collecting disk metrics: %s", e, exc_info=True)
            return {}
    
    def collect_network_usage(self) -> Dict[str, Dict]:
        """Collect network I/O statistics."""
        try:
            net_io = psutil.net_io_counters()
            net_stats = {}
            
            if hasattr(self, '_last_net_io'):
                time_delta = time.time() - self._last_time
                if time_delta > 0:
                    net_stats = {
                        'bytes_sent': net_io.bytes_sent,
                        'bytes_recv': net_io.bytes_recv,
                        'packets_sent': net_io.packets_sent,
                        'packets_recv': net_io.packets_recv,
                        'errin': net_io.errin,
                        'errout': net_io.errout,
                        'dropin': net_io.dropin,
                        'dropout': net_io.dropout,
                        'bytes_sent_per_sec': (net_io.bytes_sent - self._last_net_io.bytes_sent) / time_delta,
                        'bytes_recv_per_sec': (net_io.bytes_recv - self._last_net_io.bytes_recv) / time_delta,
                        'packets_sent_per_sec': (net_io.packets_sent - self._last_net_io.packets_sent) / time_delta,
                        'packets_recv_per_sec': (net_io.packets_recv - self._last_net_io.packets_recv) / time_delta
                    }
            
            self._last_net_io = net_io
            
            # Get network connections
            connections = []
            try:
                for conn in psutil.net_connections(kind='inet'):
                    connections.append({
                        'fd': conn.fd,
                        'family': conn.family.name if hasattr(conn.family, 'name') else str(conn.family),
                        'type': conn.type.name if hasattr(conn.type, 'name') else str(conn.type),
                        'laddr': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                        'raddr': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                        'status': conn.status,
                        'pid': conn.pid
                    })
            except (psutil.AccessDenied, psutil.PermissionError):
                # On some systems, we might not have permission to get all connections
                pass
            
            return {
                'io': net_stats,
                'connections': connections
            }
            
        except Exception as e:
            logger.error("Error collecting network metrics: %s", e, exc_info=True)
            return {}
    
    def collect_processes(self, limit: int = 10, sort_by: str = 'cpu_percent') -> Dict:
        """Collect information about running processes."""
        try:
            processes = []
            for proc in sorted(
                psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']),
                key=lambda p: getattr(p, sort_by, 0),
                reverse=True
            )[:limit]:
                try:
                    with proc.oneshot():
                        processes.append({
                            'pid': proc.pid,
                            'name': proc.name(),
                            'username': proc.username(),
                            'cpu_percent': proc.cpu_percent(),
                            'memory_percent': proc.memory_percent(),
                            'status': proc.status(),
                            'create_time': proc.create_time(),
                            'cmdline': ' '.join(proc.cmdline())
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            return processes
            
        except Exception as e:
            logger.error("Error collecting process info: %s", e, exc_info=True)
            return []
    
    def collect_system_info(self) -> Dict:
        """Collect general system information."""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
            
            return {
                'platform': platform.system(),
                'platform_version': platform.version(),
                'platform_release': platform.release(),
                'architecture': platform.machine(),
                'hostname': platform.node(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'boot_time': boot_time,
                'uptime': time.time() - psutil.boot_time(),
                'users': [{
                    'name': user.name,
                    'terminal': user.terminal,
                    'host': user.host,
                    'started': user.started,
                    'pid': user.pid
                } for user in psutil.users()]
            }
        except Exception as e:
            logger.error("Error collecting system info: %s", e, exc_info=True)
            {}
    
    def collect_all_metrics(self, include_processes: bool = True, process_limit: int = 10) -> Dict:
        """Collect all system metrics."""
        current_time = time.time()
        
        metrics = {
            'timestamp': current_time,
            'timestamp_iso': datetime.fromtimestamp(current_time).isoformat(),
            'cpu': self.collect_cpu_usage(),
            'memory': self.collect_memory_usage(),
            'disk': self.collect_disk_usage(),
            'network': self.collect_network_usage(),
            'system': self.collect_system_info()
        }
        
        if include_processes:
            metrics['processes'] = self.collect_processes(limit=process_limit)
        
        # Update last collection time
        self._last_time = current_time
        
        return metrics


@tool(
    name="monitor_system_resources",
    description="Monitor system resources including CPU, memory, disk, and network usage",
    category=ToolCategory.SYSTEM,
    parameters=[
        ToolParameter(
            name="interval",
            type=float,
            description="Sampling interval in seconds",
            default=1.0,
            min=0.1,
            max=60.0
        ),
        ToolParameter(
            name="duration",
            type=float,
            description="Duration to monitor in seconds (0 for single snapshot)",
            default=0,
            min=0
        ),
        ToolParameter(
            name="include_processes",
            type=bool,
            description="Include process information",
            default=True
        ),
        ToolParameter(
            name="process_limit",
            type=int,
            description="Maximum number of processes to include",
            default=10,
            min=1,
            max=100
        ),
        ToolParameter(
            name="include_cpu",
            type=bool,
            description="Include CPU metrics",
            default=True
        ),
        ToolParameter(
            name="include_memory",
            type=bool,
            description="Include memory metrics",
            default=True
        ),
        ToolParameter(
            name="include_disk",
            type=bool,
            description="Include disk metrics",
            default=True
        ),
        ToolParameter(
            name="include_network",
            type=bool,
            description="Include network metrics",
            default=True
        ),
        ToolParameter(
            name="include_system",
            type=bool,
            description="Include system information",
            default=True
        ),
        ToolParameter(
            name="callback_url",
            type=str,
            description="URL to send metrics to (for continuous monitoring)",
            required=False
        )
    ],
    return_type=Dict,
    return_description="System resource metrics"
)
class SystemResourceMonitorTool(BaseTool):
    """Tool for monitoring system resources."""
    
    def __init__(self):
        self._collector = SystemMetricsCollector()
        self._monitoring = False
    
    async def execute(self, **kwargs) -> Dict:
        """Execute the system resource monitoring."""
        if kwargs.get('duration', 0) > 0:
            return await self._monitor_continuous(**kwargs)
        return await self._get_snapshot(**kwargs)
    
    async def _get_snapshot(self, **kwargs) -> Dict:
        """Get a single snapshot of system metrics."""
        include_processes = kwargs.get('include_processes', True)
        process_limit = kwargs.get('process_limit', 10)
        
        # Get a single snapshot
        metrics = self._collector.collect_all_metrics(
            include_processes=include_processes,
            process_limit=process_limit
        )
        
        # Filter metrics based on include_* parameters
        filtered_metrics = {'timestamp': metrics['timestamp'], 'timestamp_iso': metrics['timestamp_iso']}
        
        if kwargs.get('include_cpu', True):
            filtered_metrics['cpu'] = metrics.get('cpu', {})
        if kwargs.get('include_memory', True):
            filtered_metrics['memory'] = metrics.get('memory', {})
        if kwargs.get('include_disk', True):
            filtered_metrics['disk'] = metrics.get('disk', {})
        if kwargs.get('include_network', True):
            filtered_metrics['network'] = metrics.get('network', {})
        if kwargs.get('include_system', True):
            filtered_metrics['system'] = metrics.get('system', {})
        if kwargs.get('include_processes', True) and 'processes' in metrics:
            filtered_metrics['processes'] = metrics['processes']
        
        return filtered_metrics
    
    async def _monitor_continuous(self, **kwargs) -> Dict:
        """Monitor system resources continuously for the specified duration."""
        interval = max(0.1, float(kwargs.get('interval', 1.0)))
        duration = float(kwargs.get('duration', 0))
        callback_url = kwargs.get('callback_url')
        
        if duration <= 0:
            return await self._get_snapshot(**kwargs)
        
        # Mark that we're monitoring
        self._monitoring = True
        
        # Prepare the result structure
        result = {
            'status': 'monitoring_started',
            'start_time': time.time(),
            'end_time': time.time() + duration,
            'interval': interval,
            'samples': []
        }
        
        # Start monitoring in the background
        asyncio.create_task(self._monitor_loop(result, **kwargs))
        
        return result
    
    async def _monitor_loop(self, result: Dict, **kwargs) -> None:
        """Background monitoring loop."""
        interval = float(kwargs.get('interval', 1.0))
        duration = float(kwargs.get('duration', 0))
        callback_url = kwargs.get('callback_url')
        
        try:
            start_time = time.time()
            end_time = start_time + duration
            
            while self._monitoring and time.time() < end_time:
                # Get a snapshot
                snapshot = await self._get_snapshot(**kwargs)
                result['samples'].append(snapshot)
                
                # If we have a callback URL, send the data there
                if callback_url:
                    try:
                        # In a real implementation, you would use an HTTP client to send the data
                        # For example: await self._send_metrics(callback_url, snapshot)
                        pass
                    except Exception as e:
                        logger.error("Error sending metrics to callback URL: %s", e)
                
                # Sleep for the remaining interval time
                sleep_time = max(0, interval - (time.time() - start_time) % interval)
                await asyncio.sleep(sleep_time)
                
                # Check if we should stop
                if not self._monitoring or time.time() >= end_time:
                    break
            
            # Update the result status
            result['status'] = 'monitoring_completed'
            result['end_time'] = time.time()
            result['sample_count'] = len(result['samples'])
            
        except Exception as e:
            logger.exception("Error in monitoring loop")
            result['status'] = 'error'
            result['error'] = str(e)
            
        finally:
            self._monitoring = False
    
    def stop_monitoring(self) -> None:
        """Stop continuous monitoring."""
        self._monitoring = False


@tool(
    name="get_process_info",
    description="Get detailed information about running processes",
    category=ToolCategory.SYSTEM,
    parameters=[
        ToolParameter(
            name="pids",
            type=list,
            description="List of process IDs to get info for (empty for all)",
            default=[]
        ),
        ToolParameter(
            name="name",
            type=str,
            description="Filter processes by name (supports wildcards)",
            required=False
        ),
        ToolParameter(
            name="user",
            type=str,
            description="Filter processes by username",
            required=False
        ),
        ToolParameter(
            name="limit",
            type=int,
            description="Maximum number of processes to return",
            default=100,
            min=1,
            max=1000
        ),
        ToolParameter(
            name="sort_by",
            type=str,
            description="Sort processes by this field",
            default="cpu_percent",
            choices=["cpu_percent", "memory_percent", "name", "pid", "username", "create_time"]
        ),
        ToolParameter(
            name="sort_desc",
            type=bool,
            description="Sort in descending order",
            default=True
        )
    ],
    return_type=List[Dict],
    return_description="List of process information dictionaries"
)
class ProcessInfoTool(BaseTool):
    """Tool for getting information about running processes."""
    
    async def execute(self, **kwargs) -> List[Dict]:
        """Get information about running processes."""
        pids = kwargs.get('pids', [])
        name_filter = kwargs.get('name')
        user_filter = kwargs.get('user')
        limit = int(kwargs.get('limit', 100))
        sort_by = kwargs.get('sort_by', 'cpu_percent')
        sort_desc = bool(kwargs.get('sort_desc', True))
        
        processes = []
        
        # If specific PIDs are provided, only get those processes
        if pids:
            for pid in pids:
                try:
                    proc = psutil.Process(pid)
                    processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
                    continue
        else:
            # Get all processes
            processes = list(psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status', 'create_time']))
        
        # Filter and format processes
        result = []
        for proc in processes:
            try:
                with proc.oneshot():
                    # Apply filters
                    if name_filter and not self._match_name(proc.name(), name_filter):
                        continue
                        
                    if user_filter and proc.username() != user_filter:
                        continue
                    
                    # Get process info
                    pinfo = {
                        'pid': proc.pid,
                        'name': proc.name(),
                        'exe': proc.exe(),
                        'cmdline': proc.cmdline(),
                        'username': proc.username(),
                        'status': proc.status(),
                        'create_time': proc.create_time(),
                        'cpu_percent': proc.cpu_percent(),
                        'memory_percent': proc.memory_percent(),
                        'memory_info': {
                            'rss': proc.memory_info().rss,
                            'vms': proc.memory_info().vms,
                            'shared': proc.memory_info().shared if hasattr(proc.memory_info(), 'shared') else None,
                            'text': proc.memory_info().text if hasattr(proc.memory_info(), 'text') else None,
                            'lib': proc.memory_info().lib if hasattr(proc.memory_info(), 'lib') else None,
                            'data': proc.memory_info().data if hasattr(proc.memory_info(), 'data') else None,
                            'dirty': proc.memory_info().dirty if hasattr(proc.memory_info(), 'dirty') else None,
                        },
                        'io_counters': {
                            'read_count': proc.io_counters().read_count,
                            'write_count': proc.io_counters().write_count,
                            'read_bytes': proc.io_counters().read_bytes,
                            'write_bytes': proc.io_counters().write_bytes,
                        } if hasattr(proc, 'io_counters') and proc.io_counters() else None,
                        'num_threads': proc.num_threads(),
                        'num_fds': proc.num_fds() if hasattr(proc, 'num_fds') else None,
                        'cpu_affinity': proc.cpu_affinity() if hasattr(proc, 'cpu_affinity') else None,
                        'cpu_num': proc.cpu_num() if hasattr(proc, 'cpu_num') else None,
                        'ppid': proc.ppid(),
                        'parent': proc.parent().name() if proc.parent() else None,
                        'children': [{
                            'pid': child.pid,
                            'name': child.name(),
                            'status': child.status()
                        } for child in proc.children()],
                        'connections': [{
                            'fd': conn.fd,
                            'family': conn.family.name if hasattr(conn.family, 'name') else str(conn.family),
                            'type': conn.type.name if hasattr(conn.type, 'name') else str(conn.type),
                            'laddr': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                            'raddr': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                            'status': conn.status,
                        } for conn in proc.connections()] if hasattr(proc, 'connections') else []
                    }
                    
                    result.append(pinfo)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            
            # Limit the number of results
            if len(result) >= limit * 2:  # Get some extra before sorting
                break
        
        # Sort the results
        reverse = sort_desc if sort_by != 'name' else not sort_desc
        result.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
        
        # Apply final limit
        return result[:limit]
    
    def _match_name(self, name: str, pattern: str) -> bool:
        """Check if a process name matches a pattern with wildcards."""
        if not pattern:
            return True
            
        # Simple wildcard matching
        if '*' in pattern or '?' in pattern:
            import fnmatch
            return fnmatch.fnmatch(name.lower(), pattern.lower())
        
        # Exact match
        return name.lower() == pattern.lower()
