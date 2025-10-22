"""Memory monitoring and management for batch processing."""

import os
import psutil
import platform
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass, field


@dataclass
class MemoryConfig:
    """Configuration for memory management."""

    total_memory_gb: float = field(default_factory=lambda: psutil.virtual_memory().total / (1024**3))
    max_memory_usage: float = 0.85  # Use up to 85% of available memory
    min_batch_size: int = 1
    max_batch_size: int = 1024
    safety_buffer_gb: float = 2.0  # Keep 2GB free

    # M4 Max specific settings
    mps_overhead_factor: float = 1.2  # MPS requires extra memory overhead

    # Aggressive mode settings
    aggressive_mode: bool = False
    aggressive_max_memory_gb: float = 40.0  # For M4 Max with 48GB
    aggressive_target_gb: float = 35.0  # Target sustained usage
    aggressive_pressure_threshold: float = 0.85  # Warn at 85% in aggressive mode
    
    
class MemoryMonitor:
    """Monitor and manage memory for batch processing optimization."""
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        """Initialize memory monitor.

        Args:
            config: Memory configuration settings
        """
        self.config = config or MemoryConfig()
        self._is_m4_max = self._detect_m4_max()
        self._base_memory_usage = self._get_current_memory_gb()

        # Log aggressive mode if enabled
        if self.config.aggressive_mode:
            logger = __import__('logging').getLogger(__name__)
            logger.info(
                f"Memory monitor initialized in AGGRESSIVE mode: "
                f"target={self.config.aggressive_target_gb}GB, "
                f"max={self.config.aggressive_max_memory_gb}GB"
            )
        
    def _detect_m4_max(self) -> bool:
        """Detect if running on M4 Max or similar Apple Silicon."""
        if platform.system() != "Darwin":
            return False
        
        try:
            import subprocess
            result = subprocess.run(
                ["sysctl", "-n", "hw.optional.arm64"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0 and result.stdout.strip() == "1"
        except Exception:
            return False
            
    def _get_current_memory_gb(self) -> float:
        """Get current memory usage in GB."""
        return psutil.virtual_memory().used / (1024**3)
        
    def get_available_memory_gb(self) -> float:
        """Get available memory in GB, considering safety buffer."""
        total_available = psutil.virtual_memory().available / (1024**3)
        return max(0, total_available - self.config.safety_buffer_gb)
        
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get detailed memory statistics."""
        mem = psutil.virtual_memory()
        
        stats: Dict[str, Any] = {
            "total_gb": mem.total / (1024**3),
            "available_gb": mem.available / (1024**3),
            "used_gb": mem.used / (1024**3),
            "percent_used": mem.percent,
            "process_used_gb": self._get_process_memory_gb(),
            "available_for_batch_gb": self.get_available_memory_gb(),
        }
        
        if self._is_m4_max:
            stats["platform"] = "M4 Max (Apple Silicon)"
            stats["mps_overhead_factor"] = self.config.mps_overhead_factor
            
        return stats
        
    def _get_process_memory_gb(self) -> float:
        """Get current process memory usage in GB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024**3)
        
    def calculate_optimal_batch_size(
        self, 
        item_size_mb: float,
        processing_overhead: float = 1.5
    ) -> int:
        """Calculate optimal batch size based on available memory.
        
        Args:
            item_size_mb: Estimated size of each item in MB
            processing_overhead: Multiplier for processing overhead
            
        Returns:
            Optimal batch size
        """
        available_gb = self.get_available_memory_gb()
        
        # Apply MPS overhead if on M4 Max
        if self._is_m4_max:
            available_gb /= self.config.mps_overhead_factor
            
        # Calculate items that fit in available memory
        available_mb = available_gb * 1024
        items_per_batch = int(available_mb / (item_size_mb * processing_overhead))
        
        # Clamp to configured limits
        batch_size = max(
            self.config.min_batch_size,
            min(items_per_batch, self.config.max_batch_size)
        )
        
        return batch_size
        
    def check_memory_pressure(self) -> Tuple[bool, str]:
        """Check if system is under memory pressure.

        Returns:
            Tuple of (is_under_pressure, message)
        """
        mem = psutil.virtual_memory()

        # Adjust thresholds for aggressive mode
        if self.config.aggressive_mode:
            critical_threshold = 95
            high_threshold = int(self.config.aggressive_pressure_threshold * 100)
            min_available = max(self.config.safety_buffer_gb, 4.0)  # At least 4GB free
        else:
            critical_threshold = 95
            high_threshold = 90
            min_available = self.config.safety_buffer_gb

        if mem.percent > critical_threshold:
            return True, f"Critical memory usage: {mem.percent:.1f}%"
        elif mem.percent > high_threshold:
            return True, f"High memory usage: {mem.percent:.1f}%"
        elif mem.available / (1024**3) < min_available:
            return True, f"Low available memory: {mem.available/(1024**3):.1f}GB"

        return False, f"Memory usage normal: {mem.percent:.1f}%"
        
    def wait_for_memory(self, required_gb: float, timeout: int = 60) -> bool:
        """Wait for required memory to become available.
        
        Args:
            required_gb: Required memory in GB
            timeout: Maximum wait time in seconds
            
        Returns:
            True if memory became available, False if timeout
        """
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.get_available_memory_gb() >= required_gb:
                return True
            time.sleep(1)
            
        return False