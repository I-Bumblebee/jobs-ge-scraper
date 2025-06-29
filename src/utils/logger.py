import logging
import sys
from typing import Optional
from pathlib import Path
from datetime import datetime


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: str = "logs",
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration for the job scraping system.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file name (will be created in log_dir)
        log_dir: Directory for log files
        format_string: Custom format string
        
    Returns:
        Configured logger instance
    """
    # Create log directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Default format
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=[]
    )
    
    logger = logging.getLogger("JobScraper")
    logger.handlers.clear()  # Clear any existing handlers
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_formatter = logging.Formatter(format_string)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        if not log_file.endswith('.log'):
            log_file += '.log'
        
        file_path = log_path / log_file
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))
        file_formatter = logging.Formatter(format_string)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"Logging to file: {file_path}")
    
    logger.info(f"Logging initialized at level: {level}")
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"JobScraper.{name}")


class ScrapingLogger:
    """
    Specialized logger for scraping operations with additional context.
    """
    
    def __init__(self, platform: str, operation: str = "scraping"):
        """
        Initialize the scraping logger.
        
        Args:
            platform: Platform name (e.g., "jobs_ge", "indeed")
            operation: Operation type (e.g., "scraping", "parsing", "processing")
        """
        self.platform = platform
        self.operation = operation
        self.logger = get_logger(f"{platform}.{operation}")
        self.start_time = datetime.now()
        
        # Counters for tracking
        self.success_count = 0
        self.error_count = 0
        self.warning_count = 0
    
    def log_start(self, message: str = None):
        """Log the start of an operation."""
        if message is None:
            message = f"Starting {self.operation} for {self.platform}"
        self.logger.info(f"[START] {message}")
        self.start_time = datetime.now()
    
    def log_success(self, message: str, **kwargs):
        """Log a successful operation."""
        self.success_count += 1
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        log_message = f"[SUCCESS] {message}"
        if extra_info:
            log_message += f" | {extra_info}"
        self.logger.info(log_message)
    
    def log_error(self, message: str, exception: Exception = None, **kwargs):
        """Log an error."""
        self.error_count += 1
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        log_message = f"[ERROR] {message}"
        if extra_info:
            log_message += f" | {extra_info}"
        if exception:
            log_message += f" | Exception: {str(exception)}"
        self.logger.error(log_message)
    
    def log_warning(self, message: str, **kwargs):
        """Log a warning."""
        self.warning_count += 1
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        log_message = f"[WARNING] {message}"
        if extra_info:
            log_message += f" | {extra_info}"
        self.logger.warning(log_message)
    
    def log_progress(self, current: int, total: int, message: str = None):
        """Log progress information."""
        percentage = (current / total) * 100 if total > 0 else 0
        if message is None:
            message = f"Progress: {current}/{total} ({percentage:.1f}%)"
        else:
            message = f"{message} | Progress: {current}/{total} ({percentage:.1f}%)"
        self.logger.info(f"[PROGRESS] {message}")
    
    def log_completion(self, message: str = None):
        """Log the completion of an operation with summary."""
        duration = datetime.now() - self.start_time
        
        if message is None:
            message = f"Completed {self.operation} for {self.platform}"
        
        summary = (
            f"{message} | "
            f"Duration: {duration.total_seconds():.2f}s | "
            f"Success: {self.success_count} | "
            f"Errors: {self.error_count} | "
            f"Warnings: {self.warning_count}"
        )
        
        self.logger.info(f"[COMPLETION] {summary}")
        
        return {
            'duration_seconds': duration.total_seconds(),
            'success_count': self.success_count,
            'error_count': self.error_count,
            'warning_count': self.warning_count
        } 