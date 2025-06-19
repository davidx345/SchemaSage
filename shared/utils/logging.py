"""Logging utilities."""

import logging
import sys
from typing import Optional


def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    log_format: Optional[str] = None
) -> logging.Logger:
    """Setup logging for a service."""
    
    if log_format is None:
        log_format = f"%(asctime)s - {service_name} - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(service_name)
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
