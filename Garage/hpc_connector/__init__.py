"""
This module exists for backward compatibility.
The HPC connector functionality has moved to Garage.HPC.hpc_connector.
"""

import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("hpc_connector")

try:
    # Try to import from the correct location
    from Garage.HPC.hpc_connector import HPCJobStatus, HPCJob, HPCConnector, test_connection
    logger.info("Successfully imported HPC connector classes from Garage.HPC.hpc_connector")
except ImportError as e:
    logger.error(f"Failed to import from Garage.HPC.hpc_connector: {e}")
    
    # Try to add the parent directory to sys.path
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
        logger.info(f"Added {parent_dir} to Python path")
    
    try:
        # Try import again
        from Garage.HPC.hpc_connector import HPCJobStatus, HPCJob, HPCConnector, test_connection
        logger.info("Successfully imported HPC connector classes after path adjustment")
    except ImportError as e:
        logger.error(f"Still failed to import after path adjustment: {e}")
        
        # Define placeholder classes for backward compatibility
        class HPCJobStatus:
            """Job status constants"""
            PENDING = "pending"
            RUNNING = "running"
            COMPLETED = "completed"
            FAILED = "failed"
            CANCELLED = "cancelled"
            TIMEOUT = "timeout"
            UNKNOWN = "unknown"
            
        class HPCJob:
            """Placeholder for HPCJob class"""
            pass
            
        class HPCConnector:
            """Placeholder for HPCConnector class"""
            def __init__(self, *args, **kwargs):
                logger.warning("Using placeholder HPCConnector class")
                self.connected = False
                
            def connect(self):
                return False, "Placeholder HPCConnector - Using compatibility layer"
                
            def disconnect(self):
                return False
                
        def test_connection(config):
            """Placeholder for test_connection function"""
            return False, "Placeholder test_connection - Using compatibility layer"
            
        logger.warning("Using placeholder HPC classes for backward compatibility")
