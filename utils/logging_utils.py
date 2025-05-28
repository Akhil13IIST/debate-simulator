"""
Logging Utilities Module

This module provides utility functions for logging setup and management
throughout the debate simulator.
"""

import os
import sys
import logging
import datetime
from typing import Optional, Dict, Any

def setup_logging(
    log_dir: str = "logs",
    log_level: int = logging.INFO,
    log_to_console: bool = True,
    log_to_file: bool = True,
    app_name: str = "debate_simulator"
) -> logging.Logger:
    """
    Set up logging for the application.
    
    Args:
        log_dir: Directory to store log files
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_to_console: Whether to log to console
        log_to_file: Whether to log to file
        app_name: Name of the application for the logger
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(log_level)
    logger.handlers = []  # Clear any existing handlers
    
    # Log formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d) - %(message)s'
    )
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{app_name}_{timestamp}.log"
        log_filepath = os.path.join(log_dir, log_filename)
        
        file_handler = logging.FileHandler(log_filepath)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    logger.info(f"Logging initialized for {app_name}")
    return logger

def get_debate_logger(debate_id: str, log_dir: str = "logs/debates") -> logging.Logger:
    """
    Get a logger for a specific debate.
    
    Args:
        debate_id: Unique identifier for the debate
        log_dir: Directory to store debate logs
        
    Returns:
        Logger configured for the specific debate
    """
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger_name = f"debate_simulator.debate.{debate_id}"
    logger = logging.getLogger(logger_name)
    
    # Check if this logger has already been configured
    if logger.handlers:
        return logger
    
    # Configure logger
    logger.setLevel(logging.DEBUG)
    
    # Create log filename
    log_filename = f"debate_{debate_id}.log"
    log_filepath = os.path.join(log_dir, log_filename)
    
    # Log formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_filepath)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Add a console handler as well
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)  # Only INFO and above for console
    logger.addHandler(console_handler)
    
    logger.info(f"Debate logger initialized for debate {debate_id}")
    return logger

class DebateLogger:
    """
    Logger class for debates with additional context and utilities.
    """
    
    def __init__(self, debate_id: str, log_dir: str = "logs/debates"):
        """
        Initialize a debate logger.
        
        Args:
            debate_id: Unique identifier for the debate
            log_dir: Directory to store debate logs
        """
        self.debate_id = debate_id
        self.log_dir = log_dir
        self.logger = get_debate_logger(debate_id, log_dir)
        self.turn_logs = []
    
    def log_config(self, config: Dict[str, Any]) -> None:
        """
        Log debate configuration.
        
        Args:
            config: Debate configuration dictionary
        """
        self.logger.info(f"Debate configuration: topic='{config.get('topic')}', turns={config.get('num_turns')}")
        self.logger.debug(f"Full config: {config}")
    
    def log_turn(self, turn_num: int, speaker: str, message_type: str, content: str) -> None:
        """
        Log a debate turn.
        
        Args:
            turn_num: Turn number
            speaker: Speaker name
            message_type: Message type (e.g., "opening", "argument", "rebuttal")
            content: Message content
        """
        self.logger.info(f"Turn {turn_num} - {speaker} ({message_type}): {content[:50]}...")
        
        # Store in turn logs
        self.turn_logs.append({
            "turn": turn_num,
            "speaker": speaker,
            "type": message_type,
            "content": content,
            "timestamp": datetime.datetime.now().isoformat()
        })
    
    def log_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        Log a debate event.
        
        Args:
            event_type: Type of event (e.g., "start", "pause", "resume", "end")
            details: Event details
        """
        self.logger.info(f"Event: {event_type} - {details}")
    
    def export_logs(self, filepath: Optional[str] = None) -> str:
        """
        Export the debate logs to a file.
        
        Args:
            filepath: Optional filepath to save logs
            
        Returns:
            Path to the exported log file
        """
        if filepath is None:
            # Create a default filepath
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"debate_{self.debate_id}_{timestamp}_logs.txt"
            filepath = os.path.join(self.log_dir, filename)
        
        # Get log file handler path
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                log_path = handler.baseFilename
                break
        else:
            self.logger.error("No file handler found for exporting logs")
            return ""
        
        # Copy the log file to the export path
        try:
            import shutil
            shutil.copy2(log_path, filepath)
            self.logger.info(f"Exported logs to {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Error exporting logs: {e}")
            return ""