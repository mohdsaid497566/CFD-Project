#!/usr/bin/env python3
"""
GUI Mode Testing Wrapper for Intake CFD Project
Tests both demo and actual modes using the existing test_gui_modes.py
"""

import os
import sys
import time
import subprocess
import argparse
import logging
from datetime import datetime

# Configure logging
log_file = f"gui_test_wrapper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_mode_test(mode):
    """Run the test_gui_modes.py test with the specified mode"""
    logger.info(f"Running GUI test in {mode} mode")
    
    try:
        # Use the existing test_gui_modes.py script
        cmd = [sys.executable, "test_gui_modes.py", "--mode", mode]
        
        # Run the process and capture output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Stream and log output in real-time
        stdout, stderr = process.communicate()
        
        # Log the output
        for line in stdout.splitlines():
            logger.info(f"[{mode}] {line}")
        
        # Log any errors
        if stderr:
            for line in stderr.splitlines():
                logger.error(f"[{mode}] {line}")
        
        # Check the return code
        if process.returncode == 0:
            logger.info(f"✅ GUI test in {mode} mode completed successfully")
            return True
        else:
            logger.error(f"❌ GUI test in {mode} mode failed with return code {process.returncode}")
            return False
            
    except Exception as e:
        logger.error(f"Error running GUI test in {mode} mode: {str(e)}")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run GUI tests in different modes")
    parser.add_argument("--mode", choices=["demo", "actual", "both"], default="both",
                       help="Test mode: demo, actual, or both")
    args = parser.parse_args()
    
    success = True
    
    if args.mode in ["demo", "both"]:
        logger.info("=" * 60)
        logger.info("Running tests in DEMO mode")
        logger.info("=" * 60)
        demo_success = run_mode_test("demo")
        success = success and demo_success
    
    if args.mode in ["actual", "both"]:
        logger.info("=" * 60)
        logger.info("Running tests in ACTUAL mode")
        logger.info("=" * 60)
        actual_success = run_mode_test("actual")
        success = success and actual_success
    
    if success:
        logger.info("✅ All GUI tests completed successfully")
        return 0
    else:
        logger.error("❌ Some GUI tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())