"""
Comprehensive logging configuration for Sprintly MVP.

Provides structured logging for:
- File ingestion and CSV processing
- LLM enrichment (OpenAI API calls)
- Embedding generation
- Database operations
- Neo4j graph operations
- Email generation
- Vector search
- API endpoints
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.config import settings


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{self.BOLD}{levelname}{self.RESET}"
        
        # Format the message
        result = super().format(record)
        
        return result


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_file_logging: bool = True,
) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (default: logs/sprintly_{date}.log)
        enable_file_logging: Whether to enable file logging
    """
    # Convert log level string to constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    if enable_file_logging:
        log_dir.mkdir(exist_ok=True)
    
    # Default log file path
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"sprintly_{timestamp}.log"
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_formatter = ColoredFormatter(
        '%(levelname)s | %(asctime)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (detailed logs)
    if enable_file_logging:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Always DEBUG for files
        file_formatter = logging.Formatter(
            '%(levelname)-8s | %(asctime)s | %(name)-30s | %(funcName)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.INFO)
    logging.getLogger("neo4j").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    root_logger.info("=" * 80)
    root_logger.info("Logging initialized")
    root_logger.info(f"Log level: {log_level}")
    if enable_file_logging:
        root_logger.info(f"Log file: {log_file}")
    root_logger.info("=" * 80)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Module name (usually __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Performance logging helpers
class OperationTimer:
    """Context manager for timing operations."""
    
    def __init__(self, logger: logging.Logger, operation: str, level: int = logging.INFO):
        """Initialize timer."""
        self.logger = logger
        self.operation = operation
        self.level = level
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        """Start timer."""
        import time
        self.start_time = time.time()
        self.logger.log(self.level, f"Starting: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer and log duration."""
        import time
        if self.start_time:
            duration = time.time() - self.start_time
            if exc_type:
                self.logger.error(
                    f"Failed: {self.operation} | Duration: {duration:.2f}s | Error: {exc_val}"
                )
            else:
                self.logger.log(
                    self.level,
                    f"Completed: {self.operation} | Duration: {duration:.2f}s"
                )


def log_api_call(
    logger: logging.Logger,
    service: str,
    operation: str,
    **kwargs
) -> None:
    """
    Log an API call with structured information.
    
    Args:
        logger: Logger instance
        service: Service name (e.g., "OpenAI", "Neo4j")
        operation: Operation name (e.g., "generate_embedding", "enrich_entity")
        **kwargs: Additional context (model, tokens, cost, etc.)
    """
    context = " | ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"API Call: {service}.{operation} | {context}")


def log_processing_progress(
    logger: logging.Logger,
    current: int,
    total: int,
    operation: str,
    **kwargs
) -> None:
    """
    Log processing progress with percentage.
    
    Args:
        logger: Logger instance
        current: Current item number
        total: Total items
        operation: Operation description
        **kwargs: Additional context
    """
    percentage = (current / total * 100) if total > 0 else 0
    context = " | ".join(f"{k}={v}" for k, v in kwargs.items())
    extra = f" | {context}" if context else ""
    logger.info(f"Progress: {operation} | {current}/{total} ({percentage:.1f}%){extra}")


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    operation: str,
    **kwargs
) -> None:
    """
    Log an error with context information.
    
    Args:
        logger: Logger instance
        error: Exception object
        operation: Operation that failed
        **kwargs: Additional context
    """
    context = " | ".join(f"{k}={v}" for k, v in kwargs.items())
    error_type = type(error).__name__
    logger.error(
        f"Error: {operation} | Type: {error_type} | Message: {str(error)} | {context}",
        exc_info=True
    )

