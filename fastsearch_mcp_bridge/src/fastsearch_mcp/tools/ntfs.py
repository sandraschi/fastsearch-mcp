"""
NTFS Health Check Tools for FastSearch MCP.

This module provides tools for checking and maintaining the health of NTFS volumes.
"""

import asyncio
import ctypes
import os
import platform
import subprocess
import sys
import win32api
import win32file
import winioctlcon
import win32con
import win32security
from ctypes import wintypes
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

import psutil
import win32wnet

from ..exceptions import McpError
from . import tool, ToolRegistry

# Constants
FSCTL_GET_NTFS_VOLUME_DATA = 0x00090064
FSCTL_GET_NTFS_STATISTICS = 0x00090068
FSCTL_GET_REFS_VOLUME_DATA = 0x000902D8

# NTFS volume data structure
class NTFS_VOLUME_DATA_BUFFER(ctypes.Structure):
    _fields_ = [
        ("VolumeSerialNumber", wintypes.DWORD),
        ("NumberSectors", wintypes.LARGE_INTEGER),
        ("TotalClusters", wintypes.LARGE_INTEGER),
        ("FreeClusters", wintypes.LARGE_INTEGER),
        ("TotalReserved", wintypes.LARGE_INTEGER),
        ("BytesPerSector", wintypes.DWORD),
        ("BytesPerCluster", wintypes.DWORD),
        ("BytesPerFileRecordSegment", wintypes.DWORD),
        ("ClustersPerFileRecordSegment", wintypes.DWORD),
        ("MftValidDataLength", wintypes.LARGE_INTEGER),
        ("MftStartLcn", wintypes.LARGE_INTEGER),
        ("Mft2StartLcn", wintypes.LARGE_INTEGER),
        ("MftZoneStart", wintypes.LARGE_INTEGER),
        ("MftZoneEnd", wintypes.LARGE_INTEGER),
    ]

class NtfsError(McpError):
    """Base class for NTFS-related errors."""
    pass

def _get_volume_handle(volume_path: str) -> int:
    """Get a handle to the specified volume."""
    if not volume_path.endswith("\\"):
        volume_path += "\\"
    
    handle = win32file.CreateFile(
        f"\\\\.\\{volume_path}",
        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
        win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
        None,
        win32file.OPEN_EXISTING,
        0,
        None
    )
    
    if handle == win32file.INVALID_HANDLE_VALUE:
        raise NtfsError(f"Failed to open volume {volume_path}")
    
    return handle

def _get_volume_info(volume_path: str) -> dict:
    """Get NTFS volume information."""
    handle = _get_volume_handle(volume_path)
    try:
        # Get volume data
        out_buf = bytes(ctypes.sizeof(NTFS_VOLUME_DATA_BUFFER))
        bytes_returned = win32file.DeviceIoControl(
            handle,
            FSCTL_GET_NTFS_VOLUME_DATA,
            None,
            out_buf,
            None
        )
        
        if not bytes_returned:
            raise NtfsError("Failed to get NTFS volume data")
        
        # Parse volume data
        vol_data = NTFS_VOLUME_DATA_BUFFER.from_buffer_copy(out_buf[:ctypes.sizeof(NTFS_VOLUME_DATA_BUFFER)])
        
        # Calculate usage
        total_bytes = vol_data.TotalClusters * vol_data.BytesPerCluster
        free_bytes = vol_data.FreeClusters * vol_data.BytesPerCluster
        used_bytes = total_bytes - free_bytes
        
        return {
            "volume_path": volume_path,
            "volume_serial": f"{vol_data.VolumeSerialNumber:08X}",
            "bytes_per_sector": vol_data.BytesPerSector,
            "bytes_per_cluster": vol_data.BytesPerCluster,
            "total_clusters": vol_data.TotalClusters,
            "free_clusters": vol_data.FreeClusters,
            "total_bytes": total_bytes,
            "free_bytes": free_bytes,
            "used_bytes": used_bytes,
            "used_percent": (used_bytes / total_bytes * 100) if total_bytes > 0 else 0,
            "bytes_per_file_record": vol_data.BytesPerFileRecordSegment,
            "clusters_per_file_record": vol_data.ClustersPerFileRecordSegment,
            "mft_valid_data_length": vol_data.MftValidDataLength,
            "mft_zone_start": vol_data.MftZoneStart,
            "mft_zone_end": vol_data.MftZoneEnd,
        }
    finally:
        win32file.CloseHandle(handle)

def _check_disk_errors(volume_path: str) -> dict:
    """Check for disk errors using chkdsk."""
    try:
        # Run chkdsk in read-only mode
        result = subprocess.run(
            ["chkdsk", volume_path[0] + ":"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        output = result.stdout.lower()
        
        # Check for common issues in chkdsk output
        issues = []
        if "corrupt" in output:
            issues.append("corrupt_files")
        if "bad clusters" in output or "bad sectors" in output:
            issues.append("bad_sectors")
        if "index entry" in output and "not found" in output:
            issues.append("index_issues")
        if "security descriptor" in output and "incorrect" in output:
            issues.append("security_descriptor_issues")
        if "file record segment" in output and "unreadable" in output:
            issues.append("unreadable_file_records")
            
        return {
            "volume_path": volume_path,
            "has_errors": len(issues) > 0,
            "issues_found": issues,
            "chkdsk_output": result.stdout,
            "chkdsk_return_code": result.returncode
        }
    except Exception as e:
        raise NtfsError(f"Failed to run chkdsk: {e}")

def _get_ntfs_permissions(volume_path: str) -> dict:
    """Check NTFS permissions and security settings."""
    try:
        # Get security descriptor for the root of the volume
        sd = win32security.GetFileSecurity(
            volume_path,
            win32security.OWNER_SECURITY_INFORMATION |
            win32security.GROUP_SECURITY_INFORMATION |
            win32security.DACL_SECURITY_INFORMATION
        )
        
        # Get owner and group
        owner_sid = sd.GetSecurityDescriptorOwner()
        group_sid = sd.GetSecurityDescriptorGroup()
        
        # Convert SIDs to names
        try:
            owner_name, domain, _ = win32security.LookupAccountSid(None, owner_sid)
            owner = f"{domain}\\{owner_name}"
        except:
            owner = str(owner_sid)
            
        try:
            group_name, domain, _ = win32security.LookupAccountSid(None, group_sid)
            group = f"{domain}\\{group_name}"
        except:
            group = str(group_sid)
        
        # Check for common permission issues
        dacl = sd.GetSecurityDescriptorDacl()
        everyone_denied = False
        users_denied = False
        
        for i in range(dacl.GetAceCount()):
            ace = dacl.GetAce(i)
            ace_type, ace_flags, ace_mask, ace_sid = ace
            
            # Check for Everyone or Authenticated Users with deny ACEs
            if ace_type == win32security.ACCESS_DENIED_ACE_TYPE:
                try:
                    name, domain, _ = win32security.LookupAccountSid(None, ace_sid)
                    sid_str = f"{domain}\\{name}".lower()
                    if "everyone" in sid_str:
                        everyone_denied = True
                    if "users" in sid_str or "authenticated users" in sid_str:
                        users_denied = True
                except:
                    pass
        
        return {
            "volume_path": volume_path,
            "owner": owner,
            "group": group,
            "security_issues": {
                "everyone_denied": everyone_denied,
                "users_denied": users_denied,
                "recommendation": "Ensure proper permissions are set for required users and groups"
            }
        }
    except Exception as e:
        raise NtfsError(f"Failed to check NTFS permissions: {e}")

@tool("ntfs.volume_info", "Get information about an NTFS volume")
async def get_volume_info(volume_path: str) -> dict:
    """
    Get detailed information about an NTFS volume.
    
    Args:
        volume_path: The volume path (e.g., 'C:' or 'C:\\')
        
    Returns:
        Dictionary containing volume information
    """
    try:
        return _get_volume_info(volume_path)
    except Exception as e:
        raise NtfsError(f"Failed to get volume info: {e}")

@tool("ntfs.check_health", "Check the health of an NTFS volume")
async def check_volume_health(volume_path: str) -> dict:
    """
    Check the health of an NTFS volume.
    
    Args:
        volume_path: The volume path (e.g., 'C:' or 'C:\\')
        
    Returns:
        Dictionary containing health check results
    """
    try:
        volume_info = _get_volume_info(volume_path)
        disk_errors = _check_disk_errors(volume_path)
        permissions = _get_ntfs_permissions(volume_path)
        
        # Calculate overall health score (0-100)
        health_score = 100
        
        # Deduct for disk space issues
        if volume_info["used_percent"] > 90:
            health_score -= 20
        elif volume_info["used_percent"] > 80:
            health_score -= 10
            
        # Deduct for disk errors
        if disk_errors["has_errors"]:
            health_score -= 30
            
        # Deduct for permission issues
        if any(permissions["security_issues"].values()):
            health_score -= 10
        
        health_score = max(0, health_score)
        
        return {
            "volume_path": volume_path,
            "health_score": health_score,
            "health_status": (
                "healthy" if health_score >= 80 else
                "warning" if health_score >= 50 else
                "critical"
            ),
            "volume_info": volume_info,
            "disk_errors": disk_errors,
            "permissions": permissions,
            "recommendations": [
                "Run chkdsk /f to fix file system errors" if disk_errors["has_errors"] else None,
                "Free up disk space" if volume_info["used_percent"] > 80 else None,
                "Review NTFS permissions" if any(permissions["security_issues"].values()) else None
            ],
        }
    except Exception as e:
        raise NtfsError(f"Failed to check volume health: {e}")

@tool("ntfs.list_volumes", "List all NTFS volumes on the system")
async def list_ntfs_volumes() -> List[dict]:
    """
    List all NTFS volumes on the system.
    
    Returns:
        List of dictionaries containing volume information
    """
    try:
        volumes = []
        for partition in psutil.disk_partitions():
            if partition.fstype and 'ntfs' in partition.fstype.lower():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    volumes.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_gb": usage.total / (1024**3),
                        "used_gb": usage.used / (1024**3),
                        "free_gb": usage.free / (1024**3),
                        "used_percent": usage.percent
                    })
                except Exception as e:
                    print(f"Error getting info for {partition.mountpoint}: {e}")
        return volumes
    except Exception as e:
        raise NtfsError(f"Failed to list NTFS volumes: {e}")

# Register all tools
def register_tools(registry: ToolRegistry) -> None:
    """Register all NTFS health check tools."""
    registry.register(get_volume_info)
    registry.register(check_volume_health)
    registry.register(list_ntfs_volumes)
