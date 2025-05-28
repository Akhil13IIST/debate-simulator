"""
Error Handling Utilities Module

This module provides utilities for error handling throughout
the debate simulator application.
"""

import os
import sys
import logging
import traceback
from typing import Dict, Any, Optional, Callable, Type, Union

logger = logging.getLogger(__name__)

class DebateSimulatorError(Exception):
    """Base exception class for debate simulator errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the error.
        
        Args:
            message: Error message
            details: Optional dictionary with additional error details
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)
    
    def __str__(self):
        """String representation of the error."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message

class ConfigurationError(DebateSimulatorError):
    """Error raised when there is a problem with configuration."""
    pass

class AgentError(DebateSimulatorError):
    """Error raised when there is a problem with an agent."""
    pass

class ApiError(DebateSimulatorError):
    """Error raised when there is a problem with an API call."""
    pass

class DebateEngineError(DebateSimulatorError):
    """Error raised when there is a problem with the debate engine."""
    pass

def handle_error(
    error: Exception,
    log_error: bool = True,
    raise_error: bool = False,
    default_return: Any = None,
    error_callback: Optional[Callable[[Exception], None]] = None
) -> Any:
    """
    Handle an error gracefully.
    
    Args:
        error: The exception that was raised
        log_error: Whether to log the error
        raise_error: Whether to re-raise the error
        default_return: Value to return if the error is not re-raised
        error_callback: Optional function to call with the error
        
    Returns:
        The default_return value if not raising
        
    Raises:
        The original exception if raise_error is True
    """
    if log_error:
        logger.error(f"Error: {str(error)}")
        logger.debug(f"Error details: {traceback.format_exc()}")
    
    if error_callback:
        try:
            error_callback(error)
        except Exception as callback_error:
            logger.error(f"Error in error callback: {str(callback_error)}")
    
    if raise_error:
        raise error
    
    return default_return

def check_api_key(
    key_name: str = "GROQ_API_KEY",
    error_message: Optional[str] = None
) -> bool:
    """
    Check if a required API key is set.
    
    Args:
        key_name: Name of the environment variable for the API key
        error_message: Custom error message if the key is missing
        
    Returns:
        True if the key is set, False otherwise
        
    Raises:
        ConfigurationError if the API key is not set
    """
    if not os.environ.get(key_name):
        message = error_message or f"Missing required API key: {key_name}"
        logger.error(message)
        raise ConfigurationError(message, {"key_name": key_name})
    
    return True

def safe_api_call(
    api_func: Callable,
    *args,
    retry_count: int = 3,
    error_handler: Optional[Callable[[Exception, int], bool]] = None,
    **kwargs
) -> Any:
    """
    Make an API call with error handling and retries.
    
    Args:
        api_func: The API function to call
        *args: Positional arguments for the API function
        retry_count: Number of times to retry on failure
        error_handler: Optional function that takes (error, attempt_number)
                      and returns a boolean indicating whether to retry
        **kwargs: Keyword arguments for the API function
        
    Returns:
        The result of the API call
        
    Raises:
        ApiError if all retries fail
    """
    attempt = 0
    last_error = None
    
    while attempt < retry_count:
        try:
            return api_func(*args, **kwargs)
        except Exception as e:
            attempt += 1
            last_error = e
            
            logger.warning(f"API call failed (attempt {attempt}/{retry_count}): {str(e)}")
            
            if error_handler and not error_handler(e, attempt):
                break
            
            # Only retry if we haven't reached the retry count
            if attempt >= retry_count:
                break
            
            # Wait a bit before retrying, increasing with each attempt
            import time
            time.sleep(1 * attempt)
    
    # If we get here, all retries failed
    error_details = {
        "function": api_func.__name__,
        "attempts": attempt
    }
    
    raise ApiError(
        f"API call to {api_func.__name__} failed after {attempt} attempts: {str(last_error)}",
        error_details
    ) from last_error