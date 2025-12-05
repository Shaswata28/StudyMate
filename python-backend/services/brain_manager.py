"""
Brain Process Manager - Manages the AI Brain Service as a subprocess.

This service handles:
- Starting the brain service as a subprocess on backend startup
- Health checking the brain service
- Gracefully terminating the brain service on shutdown
- Restarting the brain service on failure
"""

import os
import sys
import logging
import subprocess
import asyncio
import httpx
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class BrainManagerError(Exception):
    """Base exception for Brain Manager errors."""
    pass


class BrainStartupError(BrainManagerError):
    """Exception for brain service startup failures."""
    pass


class BrainProcessManager:
    """
    Manages the AI Brain Service as a subprocess.
    Handles startup, shutdown, health checks, and recovery.
    """
    
    def __init__(self, brain_url: str = "http://localhost:8001"):
        """
        Initialize the Brain Process Manager.
        
        Args:
            brain_url: URL where the brain service will be accessible
        """
        self.process: Optional[subprocess.Popen] = None
        self.brain_url = brain_url
        self.brain_script_path = self._find_brain_script()
        self.health_check_timeout = 5.0
        self.startup_wait_timeout = 60.0  # Wait up to 60 seconds for startup
        
        logger.info(f"Brain Process Manager initialized (URL: {self.brain_url})")
    
    def _find_brain_script(self) -> Path:
        """
        Locate the brain.py script in the project structure.
        
        Returns:
            Path to brain.py
        
        Raises:
            BrainManagerError: If brain.py cannot be found
        """
        # Get the project root (parent of python-backend)
        backend_dir = Path(__file__).parent.parent
        project_root = backend_dir.parent
        brain_script = project_root / "ai-brain" / "brain.py"
        
        if not brain_script.exists():
            error_msg = f"Brain script not found at {brain_script}"
            logger.error(error_msg)
            raise BrainManagerError(error_msg)
        
        logger.info(f"Found brain script at: {brain_script}")
        return brain_script
    
    async def start_brain(self) -> bool:
        """
        Start the AI brain service as a subprocess.
        Waits for the service to be healthy before returning.
        
        Returns:
            True if startup successful, False otherwise
        
        Raises:
            BrainStartupError: If startup fails critically
        """
        if self.process and self.process.poll() is None:
            logger.warning("Brain service is already running")
            return True
        
        try:
            logger.info("Starting AI Brain Service...")
            
            # Determine Python executable (use same Python as current process)
            python_executable = sys.executable
            
            # Start the brain service as a subprocess
            self.process = subprocess.Popen(
                [python_executable, str(self.brain_script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                cwd=str(self.brain_script_path.parent)
            )
            
            logger.info(f"Brain service process started (PID: {self.process.pid})")
            
            # Wait for the service to become healthy
            logger.info("Waiting for brain service to be ready...")
            start_time = asyncio.get_event_loop().time()
            
            while True:
                # Check if process has died
                if self.process.poll() is not None:
                    # Process has terminated
                    stdout, stderr = self.process.communicate()
                    error_msg = f"Brain service process terminated during startup. "
                    error_msg += f"Exit code: {self.process.returncode}\n"
                    error_msg += f"STDERR: {stderr[:500]}"
                    logger.error(error_msg)
                    raise BrainStartupError(error_msg)
                
                # Check if healthy
                if await self.is_healthy():
                    logger.info("Brain service is healthy and ready")
                    return True
                
                # Check timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > self.startup_wait_timeout:
                    error_msg = f"Brain service failed to become healthy within {self.startup_wait_timeout}s"
                    logger.error(error_msg)
                    await self.stop_brain()
                    raise BrainStartupError(error_msg)
                
                # Wait before next check
                await asyncio.sleep(1)
            
        except BrainStartupError:
            raise
        except Exception as e:
            error_msg = f"Failed to start brain service: {str(e)}"
            logger.error(error_msg)
            raise BrainStartupError(error_msg) from e
    
    async def stop_brain(self) -> None:
        """
        Gracefully terminate the brain service subprocess.
        Attempts graceful shutdown first, then forces termination if needed.
        """
        if not self.process:
            logger.info("No brain service process to stop")
            return
        
        try:
            # Check if process is still running
            if self.process.poll() is not None:
                logger.info(f"Brain service already terminated (exit code: {self.process.returncode})")
                self.process = None
                return
            
            logger.info(f"Stopping brain service (PID: {self.process.pid})...")
            
            # Try graceful termination first
            self.process.terminate()
            
            # Wait up to 10 seconds for graceful shutdown
            try:
                self.process.wait(timeout=10)
                logger.info("Brain service terminated gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                logger.warning("Brain service did not terminate gracefully, forcing kill...")
                self.process.kill()
                self.process.wait()
                logger.info("Brain service killed forcefully")
            
            self.process = None
            
        except Exception as e:
            logger.error(f"Error stopping brain service: {str(e)}")
            # Try to kill anyway
            if self.process:
                try:
                    self.process.kill()
                    self.process = None
                except:
                    pass
    
    async def is_healthy(self) -> bool:
        """
        Check if the brain service is responding to health checks.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=self.health_check_timeout) as client:
                response = await client.get(f"{self.brain_url}/")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "Active":
                        return True
                
                return False
                
        except (httpx.RequestError, httpx.TimeoutException) as e:
            logger.debug(f"Health check failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during health check: {str(e)}")
            return False
    
    async def restart_brain(self) -> bool:
        """
        Restart the brain service.
        Stops the current process and starts a new one.
        
        Returns:
            True if restart successful, False otherwise
        """
        logger.info("Restarting brain service...")
        
        try:
            # Stop current process
            await self.stop_brain()
            
            # Wait a moment before restarting
            await asyncio.sleep(2)
            
            # Start new process
            success = await self.start_brain()
            
            if success:
                logger.info("Brain service restarted successfully")
            else:
                logger.error("Brain service restart failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Error during brain service restart: {str(e)}")
            return False


# Global brain manager instance
brain_manager = BrainProcessManager()
