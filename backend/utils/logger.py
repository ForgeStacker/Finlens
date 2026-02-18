"""
FinLens Logger Utility
Provides centralized logging configuration following CMMI Level 5 standards
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class FinLensLogger:
    """Centralized logger for FinLens application"""
    
    _instance: Optional[logging.Logger] = None
    
    @classmethod
    def get_logger(cls, name: str = "finlens") -> logging.Logger:
        """
        Get or create logger instance
        
        Args:
            name: Logger name (default: finlens)
            
        Returns:
            Configured logger instance
        """
        if cls._instance is None:
            cls._instance = cls._setup_logger(name)
        return cls._instance
    
    @classmethod
    def _setup_logger(cls, name: str) -> logging.Logger:
        """
        Setup logger with console and file handlers
        
        Args:
            name: Logger name
            
        Returns:
            Configured logger
        """
        logger = logging.getLogger(name)
        
        # Get log level from environment or default to INFO
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        # File handler (if LOG_FILE is specified)
        log_file = os.getenv("LOG_FILE", "finlens.log")
        if log_file:
            try:
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(logging.DEBUG)
                file_format = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(file_format)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.warning(f"Could not create log file: {e}")
        
        return logger


def log_operation(operation: str, status: str, details: Optional[str] = None):
    """
    Log standardized operation messages
    
    Args:
        operation: Operation name
        status: Status (START, SUCCESS, FAILED, etc.)
        details: Additional details
    """
    logger = FinLensLogger.get_logger()
    message = f"[{operation}] {status}"
    if details:
        message += f" - {details}"
    
    if status == "FAILED":
        logger.error(message)
    elif status == "START":
        logger.info(message)
    elif status == "SUCCESS":
        logger.info(message)
    else:
        logger.debug(message)


# Convenience function
def get_logger(name: str = "finlens") -> logging.Logger:
    """Get logger instance"""
    return FinLensLogger.get_logger(name)
