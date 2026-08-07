"""Drive inventory tool for MCP."""

import logging
from typing import Any

try:
    import psutil
except ImportError:
    psutil = None

from fastsearch_mcp.mcp_instance import mcp

logger = logging.getLogger(__name__)


@mcp.tool
async def drive_inventory(
    filesystem_type: str = "",
    include_unmounted: bool = False,
) -> dict[str, Any]:
    """List all connected drives and partitions with their basic information.

    Provides filesystem type, size, usage, and other details for all
    connected drives and partitions.

    Args:
        filesystem_type: Filter by filesystem type (e.g., 'NTFS', 'FAT32', 'exFAT').
            Leave empty for all.
        include_unmounted: Include unmounted partitions

    Returns:
        Drive inventory with all connected drives and their information
    """
    filesystem_type = filesystem_type.strip()

    try:
        drives = []

        if psutil:
            try:
                for partition in psutil.disk_partitions(all=include_unmounted):
                    # Filter by filesystem type if specified
                    if filesystem_type and partition.fstype:
                        if filesystem_type.upper() not in partition.fstype.upper():
                            continue

                    drive_info = {
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "filesystem": partition.fstype or "Unknown",
                        "options": partition.opts,
                    }

                    # Try to get usage information (only for mounted drives)
                    if partition.mountpoint:
                        try:
                            usage = psutil.disk_usage(partition.mountpoint)
                            drive_info.update(
                                {
                                    "total_bytes": usage.total,
                                    "used_bytes": usage.used,
                                    "free_bytes": usage.free,
                                    "used_percent": usage.percent,
                                    "total_gb": round(usage.total / (1024**3), 2),
                                    "used_gb": round(usage.used / (1024**3), 2),
                                    "free_gb": round(usage.free / (1024**3), 2),
                                }
                            )
                        except (PermissionError, OSError) as e:
                            logger.debug(f"Could not get usage for {partition.mountpoint}: {e}")
                            drive_info["usage_error"] = str(e)
                    else:
                        drive_info["mounted"] = False

                    drives.append(drive_info)

            except Exception as e:
                logger.exception(f"Error getting drive inventory: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "drives": [],
                    "count": 0,
                }
        else:
            # Fallback: try to detect drives manually
            logger.warning("psutil not available, using basic drive detection")
            import string
            from pathlib import Path

            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                try:
                    if Path(drive).exists():
                        drives.append(
                            {
                                "device": drive,
                                "mountpoint": drive,
                                "filesystem": "Unknown",
                                "options": "",
                            }
                        )
                except Exception:
                    pass

        # Sort drives by device letter
        drives.sort(key=lambda x: x["device"])

        # Count by filesystem type
        filesystem_counts = {}
        for drive in drives:
            fs = drive.get("filesystem", "Unknown")
            filesystem_counts[fs] = filesystem_counts.get(fs, 0) + 1

        return {
            "success": True,
            "drives": drives,
            "count": len(drives),
            "filesystem_summary": filesystem_counts,
            "filter_applied": filesystem_type if filesystem_type else None,
        }

    except Exception as e:
        logger.exception(f"Drive inventory failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "drives": [],
            "count": 0,
        }
