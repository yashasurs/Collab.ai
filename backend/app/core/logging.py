"""
Structured logging configuration.

Formats application logs as JSON for ingestion into centralized
logging systems (e.g., Elasticsearch, Datadog, CloudWatch).
"""

import logging
import os
from pythonjsonlogger import jsonlogger


def setup_logging():
    """Configure structured JSON logging for the application."""
    
    # Check if structured logging is enabled
    use_json = os.getenv("LOG_FORMAT", "json").lower() == "json"
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Map string to logging level, default to INFO
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    handler = logging.StreamHandler()
    
    if use_json:
        # JSON format for production
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(module)s %(lineno)d",
            rename_fields={
                "levelname": "level",
                "asctime": "timestamp",
            }
        )
    else:
        # Human readable for local dev
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    logging.getLogger("engineio").setLevel(logging.WARNING)
    logging.getLogger("socketio").setLevel(logging.WARNING)
