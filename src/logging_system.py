"""
Logging System for Text Morph
Configures and provides centralized logging functionality
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
from datetime import datetime
from configure.config_manager import config
from exceptions import LoggingError


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        """Format log record with colors."""
        if config.get('logging.console.colored', True):
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = (
                    f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
                )
        return super().format(record)


class LoggingSystem:
    """Manages application-wide logging configuration."""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        """Singleton pattern for logging system."""
        if cls._instance is None:
            cls._instance = super(LoggingSystem, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the logging system."""
        if self._logger is None:
            self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Set up logging configuration based on config.yaml."""
        try:
            # Get logging configuration
            log_config = config.get_logging_config()
            
            # Create logger
            self._logger = logging.getLogger('TextMorph')
            
            # Set logging level
            level_name = log_config.get('level', 'INFO')
            level = getattr(logging, level_name, logging.INFO)
            self._logger.setLevel(level)
            
            # Remove existing handlers
            self._logger.handlers.clear()
            
            # Set up file logging
            if log_config.get('file', {}).get('enabled', True):
                self._setup_file_handler(log_config)
            
            # Set up console logging
            if log_config.get('console', {}).get('enabled', True):
                self._setup_console_handler(log_config)
            
            # Prevent propagation to root logger
            self._logger.propagate = False
            
            self._logger.info("Logging system initialized successfully")
            
        except Exception as e:
            raise LoggingError(f"Failed to initialize logging system: {str(e)}")
    
    def _setup_file_handler(self, log_config: dict) -> None:
        """
        Set up rotating file handler.
        
        Args:
            log_config: Logging configuration dictionary
        """
        try:
            file_config = log_config.get('file', {})
            
            # Create logs directory
            log_path = Path(file_config.get('path', 'logs'))
            log_path.mkdir(parents=True, exist_ok=True)
            
            # Create log filename with timestamp
            filename = file_config.get('filename', 'text_morph.log')
            log_file = log_path / filename
            
            # Create rotating file handler
            max_bytes = file_config.get('max_bytes', 10485760)  # 10MB
            backup_count = file_config.get('backup_count', 5)
            encoding = file_config.get('encoding', 'utf-8')
            
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding=encoding
            )
            
            # Set formatter
            log_format = log_config.get('format', 
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            date_format = log_config.get('date_format', '%Y-%m-%d %H:%M:%S')
            
            formatter = logging.Formatter(log_format, datefmt=date_format)
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            self._logger.addHandler(file_handler)
            
        except Exception as e:
            print(f"Warning: Failed to set up file logging: {e}", file=sys.stderr)
    
    def _setup_console_handler(self, log_config: dict) -> None:
        """
        Set up console handler with colored output.
        
        Args:
            log_config: Logging configuration dictionary
        """
        try:
            console_handler = logging.StreamHandler(sys.stdout)
            
            # Set formatter
            log_format = log_config.get('format', 
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            date_format = log_config.get('date_format', '%Y-%m-%d %H:%M:%S')
            
            # Use colored formatter if enabled
            if log_config.get('console', {}).get('colored', True):
                formatter = ColoredFormatter(log_format, datefmt=date_format)
            else:
                formatter = logging.Formatter(log_format, datefmt=date_format)
            
            console_handler.setFormatter(formatter)
            
            # Add handler to logger
            self._logger.addHandler(console_handler)
            
        except Exception as e:
            print(f"Warning: Failed to set up console logging: {e}", file=sys.stderr)
    
    @property
    def logger(self) -> logging.Logger:
        """Get the logger instance."""
        return self._logger
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """
        Get a logger instance.
        
        Args:
            name: Optional name for the logger (creates child logger)
            
        Returns:
            Logger instance
        """
        if name:
            return self._logger.getChild(name)
        return self._logger
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self._logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self._logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._logger.warning(message, **kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """
        Log error message.
        
        Args:
            message: Error message
            exc_info: Include exception information
        """
        self._logger.error(message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """
        Log critical message.
        
        Args:
            message: Critical message
            exc_info: Include exception information
        """
        self._logger.critical(message, exc_info=exc_info, **kwargs)
    
    def exception(self, message: str, **kwargs) -> None:
        """Log exception with traceback."""
        self._logger.exception(message, **kwargs)
    
    def log_api_call(self, service: str, endpoint: str, status: str, duration: float = None) -> None:
        """
        Log API call information.
        
        Args:
            service: API service name
            endpoint: API endpoint
            status: Call status (success/failure)
            duration: Call duration in seconds
        """
        duration_str = f" ({duration:.2f}s)" if duration else ""
        self._logger.info(f"API Call - {service} | {endpoint} | {status}{duration_str}")
    
    def log_user_action(self, action: str, details: dict = None) -> None:
        """
        Log user action.
        
        Args:
            action: Action performed
            details: Additional details
        """
        detail_str = f" | {details}" if details else ""
        self._logger.info(f"User Action - {action}{detail_str}")
    
    def log_performance(self, operation: str, duration: float, details: dict = None) -> None:
        """
        Log performance metrics.
        
        Args:
            operation: Operation name
            duration: Duration in seconds
            details: Additional details
        """
        detail_str = f" | {details}" if details else ""
        self._logger.info(f"Performance - {operation} | {duration:.2f}s{detail_str}")
    
    def log_error_with_context(self, error: Exception, context: dict = None) -> None:
        """
        Log error with contextual information.
        
        Args:
            error: Exception object
            context: Additional context dictionary
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        log_message = f"Error - {error_type}: {error_msg}"
        
        if context:
            context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
            log_message += f" | Context: {context_str}"
        
        self._logger.error(log_message, exc_info=True)
    
    def set_level(self, level: str) -> None:
        """
        Change logging level dynamically.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        level_obj = getattr(logging, level.upper(), logging.INFO)
        self._logger.setLevel(level_obj)
        self._logger.info(f"Logging level changed to {level.upper()}")
    
    def get_log_file_path(self) -> Optional[Path]:
        """
        Get the path to the log file.
        
        Returns:
            Path to log file or None if file logging disabled
        """
        for handler in self._logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                return Path(handler.baseFilename)
        return None
    
    def clear_logs(self) -> None:
        """Clear all log files."""
        log_file = self.get_log_file_path()
        if log_file and log_file.exists():
            try:
                log_file.write_text('')
                self._logger.info("Log file cleared")
            except Exception as e:
                self._logger.error(f"Failed to clear log file: {e}")
    
    def get_recent_logs(self, lines: int = 50) -> list:
        """
        Get recent log entries.
        
        Args:
            lines: Number of recent lines to retrieve
            
        Returns:
            List of log lines
        """
        log_file = self.get_log_file_path()
        if not log_file or not log_file.exists():
            return []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            self._logger.error(f"Failed to read log file: {e}")
            return []


# Create global logging system instance
logging_system = LoggingSystem()


# Convenience functions for easy logging
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Optional logger name
        
    Returns:
        Logger instance
    """
    return logging_system.get_logger(name)


def log_debug(message: str, **kwargs) -> None:
    """Log debug message."""
    logging_system.debug(message, **kwargs)


def log_info(message: str, **kwargs) -> None:
    """Log info message."""
    logging_system.info(message, **kwargs)


def log_warning(message: str, **kwargs) -> None:
    """Log warning message."""
    logging_system.warning(message, **kwargs)


def log_error(message: str, exc_info: bool = False, **kwargs) -> None:
    """Log error message."""
    logging_system.error(message, exc_info=exc_info, **kwargs)


def log_critical(message: str, exc_info: bool = False, **kwargs) -> None:
    """Log critical message."""
    logging_system.critical(message, exc_info=exc_info, **kwargs)


def log_exception(message: str, **kwargs) -> None:
    """Log exception with traceback."""
    logging_system.exception(message, **kwargs)


def log_api_call(service: str, endpoint: str, status: str, duration: float = None) -> None:
    """Log API call."""
    logging_system.log_api_call(service, endpoint, status, duration)


def log_user_action(action: str, details: dict = None) -> None:
    """Log user action."""
    logging_system.log_user_action(action, details)


def log_performance(operation: str, duration: float, details: dict = None) -> None:
    """Log performance metrics."""
    logging_system.log_performance(operation, duration, details)


def log_error_with_context(error: Exception, context: dict = None) -> None:
    """Log error with context."""
    logging_system.log_error_with_context(error, context)


# Decorator for logging function execution
def log_execution(func):
    """
    Decorator to log function execution.
    
    Usage:
        @log_execution
        def my_function():
            pass
    """
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger = get_logger(func.__module__)
        
        logger.debug(f"Executing {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(f"Completed {func.__name__} in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Error in {func.__name__} after {duration:.2f}s: {str(e)}",
                exc_info=True
            )
            raise
    
    return wrapper


if __name__ == "__main__":
    # Test logging system
    logger = get_logger("test")
    
    log_info("Testing logging system")
    log_debug("This is a debug message")
    log_warning("This is a warning")
    log_error("This is an error")
    
    # Test API call logging
    log_api_call("HuggingFace", "/summarize", "success", 2.5)
    
    # Test user action logging
    log_user_action("summarize_text", {"method": "abstractive", "length": "medium"})
    
    # Test performance logging
    log_performance("text_processing", 3.14, {"words": 500})
    
    # Test error with context
    try:
        raise ValueError("Test error")
    except Exception as e:
        log_error_with_context(e, {"user_input": "test", "action": "summarize"})
    
    print("\n✅ Logging system test completed!")
    print(f"📁 Log file location: {logging_system.get_log_file_path()}")