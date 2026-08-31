"""System resource monitoring tool for MCP."""

import asyncio
import os
import platform
import time
from datetime import datetime

import psutil

from fastsearch_mcp.logging_config import get_logger
from fastsearch_mcp.mcp_instance import mcp

# Keep references to background monitor tasks so they are not garbage-collected.
_active_tasks: set[asyncio.Task] = set()

logger = get_logger(__name__)


class SystemMetricsCollector:
    """Collects system metrics including CPU, memory, disk, and network usage."""

    def __init__(self):
        self._last_net_io = psutil.net_io_counters()
        self._last_disk_io = psutil.disk_io_counters()
        self._last_cpu_times = psutil.cpu_times()
        self._last_time = time.time()

    def collect_cpu_usage(self) -> dict[str, float]:
        """Collect CPU usage statistics."""
        try:
            # Get per-core usage
            per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)

            # Get system-wide CPU times
            cpu_times = psutil.cpu_times()

            # Calculate CPU usage percentages
            total_time = sum(cpu_times)
            if hasattr(self, "_last_cpu_times"):
                last_total = sum(self._last_cpu_times)
                delta_total = total_time - last_total

                if delta_total > 0:  # Avoid division by zero
                    cpu_percent = {
                        "user": (cpu_times.user - self._last_cpu_times.user) / delta_total * 100,
                        "system": (cpu_times.system - self._last_cpu_times.system) / delta_total * 100,
                        "idle": (cpu_times.idle - self._last_cpu_times.idle) / delta_total * 100,
                    }
                else:
                    cpu_percent = {"user": 0, "system": 0, "idle": 100}
            else:
                cpu_percent = {"user": 0, "system": 0, "idle": 100}

            self._last_cpu_times = cpu_times

            return {
                "percent": psutil.cpu_percent(interval=None),  # System-wide usage
                "per_cpu": per_cpu,  # Per-core usage
                "times": cpu_percent,  # User/System/Idle breakdown
                "count": psutil.cpu_count(),  # Number of CPU cores
                "freq": {
                    "current": psutil.cpu_freq().current if hasattr(psutil, "cpu_freq") and psutil.cpu_freq() else None,
                    "max": psutil.cpu_freq().max if hasattr(psutil, "cpu_freq") and psutil.cpu_freq() else None,
                }
                if hasattr(psutil, "cpu_freq")
                else None,
                "load_avg": dict(zip(["1min", "5min", "15min"], os.getloadavg(), strict=False))
                if hasattr(os, "getloadavg")
                else None,
            }

        except Exception as e:
            logger.error("Error collecting CPU metrics: %s", e, exc_info=True)
            return {}

    def collect_memory_usage(self) -> dict[str, float | dict]:
        """Collect memory usage statistics."""
        try:
            virtual_mem = psutil.virtual_memory()
            swap_mem = psutil.swap_memory()

            return {
                "virtual": {
                    "total": virtual_mem.total,
                    "available": virtual_mem.available,
                    "used": virtual_mem.used,
                    "free": virtual_mem.free,
                    "percent": virtual_mem.percent,
                    "used_percent": virtual_mem.percent,
                    "free_percent": 100 - virtual_mem.percent,
                },
                "swap": {
                    "total": swap_mem.total,
                    "used": swap_mem.used,
                    "free": swap_mem.free,
                    "percent": swap_mem.percent,
                    "sin": swap_mem.sin if hasattr(swap_mem, "sin") else None,
                    "sout": swap_mem.sout if hasattr(swap_mem, "sout") else None,
                },
            }
        except Exception as e:
            logger.error("Error collecting memory metrics: %s", e, exc_info=True)
            return {}

    def collect_disk_usage(self) -> dict[str, dict]:
        """Collect disk usage and I/O statistics."""
        try:
            # Get disk partitions
            partitions = []
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    partitions.append(
                        {
                            "device": part.device,
                            "mountpoint": part.mountpoint,
                            "fstype": part.fstype,
                            "opts": part.opts,
                            "total": usage.total,
                            "used": usage.used,
                            "free": usage.free,
                            "percent": usage.percent,
                        }
                    )
                except Exception as e:
                    logger.debug("Error getting disk usage for %s: %s", part.mountpoint, e)

            # Get disk I/O counters
            disk_io = psutil.disk_io_counters()
            io_stats = {}

            if hasattr(self, "_last_disk_io") and disk_io:
                time_delta = time.time() - self._last_time
                if time_delta > 0:
                    io_stats = {
                        "read_count": disk_io.read_count,
                        "write_count": disk_io.write_count,
                        "read_bytes": disk_io.read_bytes,
                        "write_bytes": disk_io.write_bytes,
                        "read_time": disk_io.read_time,
                        "write_time": disk_io.write_time,
                        "read_bytes_per_sec": (disk_io.read_bytes - self._last_disk_io.read_bytes) / time_delta,
                        "write_bytes_per_sec": (disk_io.write_bytes - self._last_disk_io.write_bytes) / time_delta,
                        "read_count_per_sec": (disk_io.read_count - self._last_disk_io.read_count) / time_delta,
                        "write_count_per_sec": (disk_io.write_count - self._last_disk_io.write_count) / time_delta,
                    }

            self._last_disk_io = disk_io

            return {"partitions": partitions, "io": io_stats}

        except Exception as e:
            logger.error("Error collecting disk metrics: %s", e, exc_info=True)
            return {}

    def collect_network_usage(self) -> dict[str, dict]:
        """Collect network I/O statistics."""
        try:
            net_io = psutil.net_io_counters()
            net_stats = {}

            if hasattr(self, "_last_net_io"):
                time_delta = time.time() - self._last_time
                if time_delta > 0:
                    net_stats = {
                        "bytes_sent": net_io.bytes_sent,
                        "bytes_recv": net_io.bytes_recv,
                        "packets_sent": net_io.packets_sent,
                        "packets_recv": net_io.packets_recv,
                        "errin": net_io.errin,
                        "errout": net_io.errout,
                        "dropin": net_io.dropin,
                        "dropout": net_io.dropout,
                        "bytes_sent_per_sec": (net_io.bytes_sent - self._last_net_io.bytes_sent) / time_delta,
                        "bytes_recv_per_sec": (net_io.bytes_recv - self._last_net_io.bytes_recv) / time_delta,
                        "packets_sent_per_sec": (net_io.packets_sent - self._last_net_io.packets_sent) / time_delta,
                        "packets_recv_per_sec": (net_io.packets_recv - self._last_net_io.packets_recv) / time_delta,
                    }

            self._last_net_io = net_io

            # Get network connections
            connections = []
            try:
                for conn in psutil.net_connections(kind="inet"):
                    connections.append(
                        {
                            "fd": conn.fd,
                            "family": conn.family.name if hasattr(conn.family, "name") else str(conn.family),
                            "type": conn.type.name if hasattr(conn.type, "name") else str(conn.type),
                            "laddr": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                            "raddr": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                            "status": conn.status,
                            "pid": conn.pid,
                        }
                    )
            except (psutil.AccessDenied, psutil.PermissionError):
                # On some systems, we might not have permission to get all connections
                pass

            return {"io": net_stats, "connections": connections}

        except Exception as e:
            logger.error("Error collecting network metrics: %s", e, exc_info=True)
            return {}

    def collect_processes(self, limit: int = 10, sort_by: str = "cpu_percent") -> dict:
        """Collect information about running processes."""
        try:
            processes = []
            for proc in sorted(
                psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent"]),
                key=lambda p: getattr(p, sort_by, 0),
                reverse=True,
            )[:limit]:
                try:
                    with proc.oneshot():
                        processes.append(
                            {
                                "pid": proc.pid,
                                "name": proc.name(),
                                "username": proc.username(),
                                "cpu_percent": proc.cpu_percent(),
                                "memory_percent": proc.memory_percent(),
                                "status": proc.status(),
                                "create_time": proc.create_time(),
                                "cmdline": " ".join(proc.cmdline()),
                            }
                        )
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            return processes

        except Exception as e:
            logger.error("Error collecting process info: %s", e, exc_info=True)
            return []

    def collect_system_info(self) -> dict:
        """Collect general system information."""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")

            return {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "platform_release": platform.release(),
                "architecture": platform.machine(),
                "hostname": platform.node(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "boot_time": boot_time,
                "uptime": time.time() - psutil.boot_time(),
                "users": [
                    {
                        "name": user.name,
                        "terminal": user.terminal,
                        "host": user.host,
                        "started": user.started,
                        "pid": user.pid,
                    }
                    for user in psutil.users()
                ],
            }
        except Exception as e:
            logger.error("Error collecting system info: %s", e, exc_info=True)
            return {}

    def collect_all_metrics(self, include_processes: bool = True, process_limit: int = 10) -> dict:
        """Collect all system metrics."""
        current_time = time.time()

        metrics = {
            "timestamp": current_time,
            "timestamp_iso": datetime.fromtimestamp(current_time).isoformat(),
            "cpu": self.collect_cpu_usage(),
            "memory": self.collect_memory_usage(),
            "disk": self.collect_disk_usage(),
            "network": self.collect_network_usage(),
            "system": self.collect_system_info(),
        }

        if include_processes:
            metrics["processes"] = self.collect_processes(limit=process_limit)

        # Update last collection time
        self._last_time = current_time

        return metrics


# Global collector instance
_collector = SystemMetricsCollector()
_monitoring = False


@mcp.tool
async def monitor_system_resources(
    interval: float = 1.0,
    duration: float = 0,
    include_processes: bool = True,
    process_limit: int = 10,
    include_cpu: bool = True,
    include_memory: bool = True,
    include_disk: bool = True,
    include_network: bool = True,
    include_system: bool = True,
    callback_url: str | None = None,
) -> dict:
    """MONITOR_SYSTEM_RESOURCES - CPU, memory, disk, network, and optional top processes.

    **Duration semantics:** ``duration <= 0`` (default ``0``) returns **one synchronous
    snapshot** and completes immediately-no blocking loop and no streaming. Use this
    for ad-hoc health checks.

    **When ``duration > 0``:** starts a **background** asyncio task that samples every
    ``interval`` seconds until the window elapses. The tool **returns immediately** with
    ``status`` ``monitoring_started``, ``samples`` initially empty, then fills in the
    background-callers cannot rely on ``samples`` in the same MCP response. This is not
    a blocking "continuous tail"; for long captures, poll with repeated
    ``duration=0`` snapshots or extend the client.

    Args:
        interval: Seconds between samples when ``duration > 0`` (minimum ~0.1 enforced).
        duration: Seconds of background sampling; **0 or negative = single snapshot only.**
        include_processes: Include top-N process rows (by CPU) in the snapshot.
        process_limit: Max processes in snapshot (not paginated; cap raises load).
        include_cpu / include_memory / include_disk / include_network / include_system:
            Toggle metric sections in the returned dict.
        callback_url: **Reserved.** HTTP POST of samples is not implemented; value is ignored.

    Returns:
        Snapshot: ``timestamp``, ``timestamp_iso``, plus requested sections (``cpu``,
        ``memory``, ``disk``, ``network``, ``system``, optional ``processes`` list).

        Timed run: ``status``, ``start_time``, ``end_time``, ``interval``, ``samples``
        (list filled asynchronously), later ``sample_count`` when the loop finishes.

    Recovery: Empty ``cpu``/``memory`` on error-check logs; on Windows without ``getloadavg``,
    ``load_avg`` may be omitted.
    """
    global _monitoring
    if duration > 0:
        return await _monitor_continuous(
            interval,
            duration,
            include_processes,
            process_limit,
            include_cpu,
            include_memory,
            include_disk,
            include_network,
            include_system,
            callback_url,
        )
    return await _get_snapshot(
        include_processes,
        process_limit,
        include_cpu,
        include_memory,
        include_disk,
        include_network,
        include_system,
    )


async def _get_snapshot(
    include_processes: bool = True,
    process_limit: int = 10,
    include_cpu: bool = True,
    include_memory: bool = True,
    include_disk: bool = True,
    include_network: bool = True,
    include_system: bool = True,
) -> dict:
    """Get a single snapshot of system metrics."""
    # Get a single snapshot
    metrics = _collector.collect_all_metrics(include_processes=include_processes, process_limit=process_limit)

    # Filter metrics based on include_* parameters
    filtered_metrics = {
        "timestamp": metrics["timestamp"],
        "timestamp_iso": metrics["timestamp_iso"],
    }

    if include_cpu:
        filtered_metrics["cpu"] = metrics.get("cpu", {})
    if include_memory:
        filtered_metrics["memory"] = metrics.get("memory", {})
    if include_disk:
        filtered_metrics["disk"] = metrics.get("disk", {})
    if include_network:
        filtered_metrics["network"] = metrics.get("network", {})
    if include_system:
        filtered_metrics["system"] = metrics.get("system", {})
    if include_processes and "processes" in metrics:
        filtered_metrics["processes"] = metrics["processes"]

    return filtered_metrics


async def _monitor_continuous(
    interval: float,
    duration: float,
    include_processes: bool,
    process_limit: int,
    include_cpu: bool,
    include_memory: bool,
    include_disk: bool,
    include_network: bool,
    include_system: bool,
    callback_url: str | None,
) -> dict:
    """Monitor system resources continuously for the specified duration."""
    global _monitoring
    interval = max(0.1, float(interval))

    if duration <= 0:
        return await _get_snapshot(
            include_processes,
            process_limit,
            include_cpu,
            include_memory,
            include_disk,
            include_network,
            include_system,
        )

    # Mark that we're monitoring
    _monitoring = True

    # Prepare the result structure
    result = {
        "status": "monitoring_started",
        "start_time": time.time(),
        "end_time": time.time() + duration,
        "interval": interval,
        "samples": [],
    }

    # Start monitoring in the background
    _monitor_task = asyncio.create_task(
        _monitor_loop(
            result,
            interval,
            duration,
            include_processes,
            process_limit,
            include_cpu,
            include_memory,
            include_disk,
            include_network,
            include_system,
            callback_url,
        )
    )
    _active_tasks.add(_monitor_task)

    return result


async def _monitor_loop(
    result: dict,
    interval: float,
    duration: float,
    include_processes: bool,
    process_limit: int,
    include_cpu: bool,
    include_memory: bool,
    include_disk: bool,
    include_network: bool,
    include_system: bool,
    callback_url: str | None,
) -> None:
    """Background monitoring loop."""
    global _monitoring
    try:
        start_time = time.time()
        end_time = start_time + duration

        while _monitoring and time.time() < end_time:
            # Get a snapshot
            snapshot = await _get_snapshot(
                include_processes,
                process_limit,
                include_cpu,
                include_memory,
                include_disk,
                include_network,
                include_system,
            )
            result["samples"].append(snapshot)

            # If we have a callback URL, send the data there
            if callback_url:
                try:
                    # In a real implementation, you would use an HTTP client to send the data
                    # For example: await _send_metrics(callback_url, snapshot)
                    pass
                except Exception as e:
                    logger.error("Error sending metrics to callback URL: %s", e)

            # Sleep for the remaining interval time
            sleep_time = max(0, interval - (time.time() - start_time) % interval)
            await asyncio.sleep(sleep_time)

            # Check if we should stop
            if not _monitoring or time.time() >= end_time:
                break

        # Update the result status
        result["status"] = "monitoring_completed"
        result["end_time"] = time.time()
        result["sample_count"] = len(result["samples"])

    except Exception as e:
        logger.exception("Error in monitoring loop")
        result["status"] = "error"
        result["error"] = str(e)

    finally:
        _monitoring = False


@mcp.tool
async def get_process_info(
    pids: list[int] | None = None,
    name: str | None = None,
    user: str | None = None,
    limit: int = 100,
    sort_by: str = "cpu_percent",
    sort_desc: bool = True,
) -> list[dict]:
    """GET_PROCESS_INFO - Detailed rows for selected or filtered processes (psutil).

    **Pagination:** There is **no cursor**. At most ``limit`` rows are returned after
    sort (default 100). The implementation may briefly consider up to ``limit * 2``
    candidates before sorting-tune ``limit`` if you need a wider net or a smaller response.

    Args:
        pids: If non-empty, only these PIDs are resolved (others ignored). If empty,
            scans all accessible processes then applies ``name`` / ``user`` filters.
        name: Optional ``fnmatch`` pattern (``*``, ``?``) or exact name (case-insensitive).
        user: Exact username filter (``proc.username()``); omit for any user.
        limit: Hard cap on rows **after** sort (default 100).
        sort_by: Dict key to sort by, e.g. ``cpu_percent``, ``memory_percent``, ``name``,
            ``pid``. Must exist on the built row.
        sort_desc: Descending order except ``name`` uses inverted default for readability.

    Returns:
        List of dicts with ``pid``, ``name``, ``exe``, ``cmdline``, ``username``,
        ``cpu_percent``, ``memory_percent``, ``memory_info``, optional ``io_counters``,
        ``connections``, ``children``, etc.

    Recovery: Skips inaccessible or vanished PIDs silently; empty list may mean filters
    matched nothing or permissions denied for all candidates.
    """
    if pids is None:
        pids = []
    name_filter = name
    user_filter = user

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
        processes = list(
            psutil.process_iter(
                [
                    "pid",
                    "name",
                    "username",
                    "cpu_percent",
                    "memory_percent",
                    "status",
                    "create_time",
                ]
            )
        )

    # Filter and format processes
    result = []
    for proc in processes:
        try:
            with proc.oneshot():
                # Apply filters
                if name_filter and not _match_process_name(proc.name(), name_filter):
                    continue

                if user_filter and proc.username() != user_filter:
                    continue

                # Get process info
                pinfo = {
                    "pid": proc.pid,
                    "name": proc.name(),
                    "exe": proc.exe(),
                    "cmdline": proc.cmdline(),
                    "username": proc.username(),
                    "status": proc.status(),
                    "create_time": proc.create_time(),
                    "cpu_percent": proc.cpu_percent(),
                    "memory_percent": proc.memory_percent(),
                    "memory_info": {
                        "rss": proc.memory_info().rss,
                        "vms": proc.memory_info().vms,
                        "shared": proc.memory_info().shared if hasattr(proc.memory_info(), "shared") else None,
                        "text": proc.memory_info().text if hasattr(proc.memory_info(), "text") else None,
                        "lib": proc.memory_info().lib if hasattr(proc.memory_info(), "lib") else None,
                        "data": proc.memory_info().data if hasattr(proc.memory_info(), "data") else None,
                        "dirty": proc.memory_info().dirty if hasattr(proc.memory_info(), "dirty") else None,
                    },
                    "io_counters": {
                        "read_count": proc.io_counters().read_count,
                        "write_count": proc.io_counters().write_count,
                        "read_bytes": proc.io_counters().read_bytes,
                        "write_bytes": proc.io_counters().write_bytes,
                    }
                    if hasattr(proc, "io_counters") and proc.io_counters()
                    else None,
                    "num_threads": proc.num_threads(),
                    "num_fds": proc.num_fds() if hasattr(proc, "num_fds") else None,
                    "cpu_affinity": proc.cpu_affinity() if hasattr(proc, "cpu_affinity") else None,
                    "cpu_num": proc.cpu_num() if hasattr(proc, "cpu_num") else None,
                    "ppid": proc.ppid(),
                    "parent": proc.parent().name() if proc.parent() else None,
                    "children": [
                        {"pid": child.pid, "name": child.name(), "status": child.status()} for child in proc.children()
                    ],
                    "connections": [
                        {
                            "fd": conn.fd,
                            "family": conn.family.name if hasattr(conn.family, "name") else str(conn.family),
                            "type": conn.type.name if hasattr(conn.type, "name") else str(conn.type),
                            "laddr": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                            "raddr": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                            "status": conn.status,
                        }
                        for conn in proc.connections()
                    ]
                    if hasattr(proc, "connections")
                    else [],
                }

                result.append(pinfo)

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

        # Limit the number of results
        if len(result) >= limit * 2:  # Get some extra before sorting
            break

    # Sort the results
    reverse = sort_desc if sort_by != "name" else not sort_desc
    result.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)

    # Apply final limit
    return result[:limit]


def _match_process_name(name: str, pattern: str) -> bool:
    """Check if a process name matches a pattern with wildcards."""
    if not pattern:
        return True

    # Simple wildcard matching
    if "*" in pattern or "?" in pattern:
        import fnmatch

        return fnmatch.fnmatch(name.lower(), pattern.lower())

    # Exact match
    return name.lower() == pattern.lower()
