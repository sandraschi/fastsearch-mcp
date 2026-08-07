#!/usr/bin/env python3
"""Test NTFS tools with admin check - run this after UAC elevation."""

import asyncio
import ctypes
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastsearch_mcp.tools.ntfs import ntfs_check_health, ntfs_volume_info


def is_admin():
    """Check if running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        return False


async def main():
    print("=" * 80)
    print("NTFS TOOLS TEST (Admin Check)")
    print("=" * 80)
    print(f"Running as admin: {is_admin()}")
    print()

    if not is_admin():
        print("ERROR: Not running as administrator!")
        print("Please run this script from an elevated PowerShell/Command Prompt")
        return

    print("Testing NTFS Volume Info for C:...")
    try:
        result = await (ntfs_volume_info.fn if hasattr(ntfs_volume_info, "fn") else ntfs_volume_info)("C:")
        total_gb = result.get("total_bytes", 0) / (1024**3)
        free_gb = result.get("free_bytes", 0) / (1024**3)
        used_pct = result.get("used_percent", 0)
        print(f"✓ SUCCESS: Total: {total_gb:.1f}GB, Free: {free_gb:.1f}GB, Used: {used_pct:.1f}%")
    except Exception as e:
        print(f"✗ FAILED: {e}")

    print()
    print("Testing NTFS Check Health for C:...")
    try:
        result = await (ntfs_check_health.fn if hasattr(ntfs_check_health, "fn") else ntfs_check_health)("C:")
        health_score = result.get("health_score", 0)
        health_status = result.get("health_status", "unknown")
        print(f"✓ SUCCESS: Health score: {health_score}/100 ({health_status})")
    except Exception as e:
        print(f"✗ FAILED: {e}")


if __name__ == "__main__":
    asyncio.run(main())
