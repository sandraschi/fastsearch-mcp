#!/usr/bin/env python3
"""
Run the FastSearch MCP test suite.

This script runs all available tests and reports the results.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_results.log')
    ]
)
logger = logging.getLogger('test_runner')

async def run_test_script(script_path):
    """Run a test script and return True if it passes."""

    logger.info(f"Running test script: {script_path}")
    try:
        # Run the script in a subprocess
        proc = await asyncio.create_subprocess_exec(
            sys.executable, str(script_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Capture output
        stdout, stderr = await proc.communicate()

        # Log output
        if stdout:
            logger.debug(f"{script_path} stdout:\n{stdout.decode().strip()}")
        if stderr:
            logger.error(f"{script_path} stderr:\n{stderr.decode().strip()}")

        # Check return code
        if proc.returncode != 0:
            logger.error(f"Test script {script_path} failed with code {proc.returncode}")
            return False

        logger.info(f"Test script {script_path} passed")
        return True

    except Exception as e:
        logger.error(f"Error running test script {script_path}: {e}", exc_info=True)
        return False

async def run_all_tests():
    """Run all test scripts in the tests directory."""
    test_dir = Path(__file__).parent
    test_scripts = [
        test_file for test_file in test_dir.glob('test_*.py')
        if test_file.is_file() and test_file.name != '__init__.py'
    ]

    if not test_scripts:
        logger.warning("No test scripts found in the tests directory")
        return False

    # Run tests in parallel
    test_tasks = [run_test_script(script) for script in test_scripts]
    results = await asyncio.gather(*test_tasks, return_exceptions=True)

    # Process results
    passed = sum(1 for r in results if r is True)
    total = len(results)

    logger.info(f"\nTest Results: {passed}/{total} tests passed")
    return passed == total

def main():
    """Main entry point for the test runner."""
    logger.info("Starting FastSearch MCP test suite")

    try:
        # Run the main test script
        test_dir = Path(__file__).parent
        main_test = test_dir / 'unit' / 'test_fastsearch.py'
        if not main_test.exists():
            main_test = test_dir / 'test_fastsearch.py'
        success = asyncio.get_event_loop().run_until_complete(
            run_test_script(main_test)
        )

        # Run additional tests if the main test passes
        if success:
            success = asyncio.get_event_loop().run_until_complete(run_all_tests())

        # Return appropriate exit code
        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"Test runner error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
