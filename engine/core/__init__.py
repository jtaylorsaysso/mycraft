# MyCraft Engine - Core Module

"""Core utilities for the MyCraft engine.

This module provides foundational utilities including configuration
management, logging, and metrics.
"""

__version__ = "0.1.0"

from .logger import get_logger, time_block, log_metric
from .hot_config import HotConfig, init_config

__all__ = [
    'get_logger', 
    'time_block', 
    'log_metric',
    'HotConfig', 
    'init_config'
]
