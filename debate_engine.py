"""
Debate Engine Module

This module defines the DebateEngine class, which orchestrates
the multi-agent debate simulation.
"""

import os
import json
import uuid
import time
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

from agents.debater_agent import DebaterAgent
from agents.moderator_agent import ModeratorAgent
from config.config_manager import ConfigManager
from utils.logging_utils import setup_logging

logger = logging.getLogger(__name__)

class DebateEngine:
    """
    Engine for simulating multi-agent debates.
    
    This class orchestrates the debate, managing the moderator and debater
    agents and controlling the flow of the debate.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the debate engine.
        
        Args:
            config: Configuration dictionary for the debate
        """
        self.config_manager = ConfigManager()
        self.config = config or {}
        self.debate_id = str(uuid.uuid4())
        self.moderator = None
        self.debaters = []
        self.transcript = []
        self.debate_status = "initialized"
        self.current_turn = 0
        self.max_turns = self.config.get("max_turns", 10)
        
        # Set up logging
        self.setup_logging()
        
        logger.info(f"Initialized DebateEngine with ID: {self.debate_id}")
    
    def setup_logging(self) -> None:
        """
        Set up logging for the debate engine.
        """
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "logs"
        )
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"debate_simulator_{timestamp}.log")
        
        setup_logging(log_dir=log_dir, log_level=logging.INFO, app_name="debate_simulator")
        
        logger.info(f"Set up logging to: {log_file}")
    
    def load_config(self, config_path: Optional[str] = None) -> bool:
        """
        Load configuration from a file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            True if configuration was loaded successfully, False otherwise
        """
        try:
            if config_path:
                self.config = self.config_manager.load_config(config_path)
            else:
                # Load default configuration
                self.config = self.config_manager.load_default_config()
            
            logger.info(f"Loaded configuration: {len(self.config)} settings")
            return True
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False
    
    def setup_debate(self, 
                     topic: str, 
                     debater_personas: List[Dict[str, Any]], 
                     moderator_persona: Dict[str, Any],
                     debate_rules: Optional[Dict[str, Any]] = None) -> bool:
        """
        Set up the debate with the given configuration.
        
        Args:
            topic: The debate topic
            debater_personas: List of debater persona configurations
            moderator_persona: Moderator persona configuration
            debate_rules: Dictionary of debate rules
            
        Returns:
            True if the debate was set up successfully, False otherwise
        """
        try:
            self.topic = topic
            
            # Setup default debate rules if none provided
            if not debate_rules:
                debate_rules = {
                    "format": "structured",
                    "round_time": 180,  # seconds
                    "max_rounds": self.max_turns,
                    "scoring_criteria": ["clarity", "evidence", "persuasiveness"],
                    "interruptions_allowed": False
                }
            
            self.debate_rules = debate_rules
            self.max_turns = debate_rules.get("max_rounds", self.max_turns)
            
            # Initialize moderator
            moderator_config = {
                "name": moderator_persona.get("name", "Moderator"),
                "persona": moderator_persona,
                "moderation_style": moderator_persona.get("moderation_style", "neutral"),
                "fact_checking": self.config.get("fact_checking", False),
                "tavily_api_key": self.config.get("tavily_api_key", os.environ.get("TAVILY_API_KEY", "")),
                "llm_config": self.config.get("llm_config", {})
            }
            
            self.moderator = ModeratorAgent(**moderator_config)
            
            # Initialize debaters
            self.debaters = []
            debater_info = []
            
            for i, persona in enumerate(debater_personas):
                stance = persona.get("stance", "for" if i % 2 == 0 else "against")
                
                debater_config = {
                    "name": persona.get("name", f"Debater {i+1}"),
                    "persona": persona,
                    "stance": stance,
                    "debate_style": persona.get("debate_style", "logical"),
                    "llm_config": self.config.get("llm_config", {})
                }
                
                debater = DebaterAgent(**debater_config)
                self.debaters.append(debater)
                
                # Add to debater info for moderator
                debater_info.append({
                    "name": debater.name,
                    "stance": debater.stance,
                    "stance_description": debater.get_stance_description()
                })
            
            # Set debate configuration for moderator
            self.moderator.set_debate_config(
                topic=topic,
                debaters=debater_info,
                rules=debate_rules
            )
            
            self.debate_status = "ready"
            logger.info(f"Set up debate on topic: {topic} with {len(self.debaters)} debaters")
            
            return True
        except Exception as e:
            logger.error(f"Error setting up debate: {e}")
            self.debate_status = "error"
            return False
    
    def start_debate(self) -> bool:
        """
        Start the debate.
        
        Returns:
            True if the debate was started successfully, False otherwise
        """
        if self.debate_status != "ready":
            logger.error(f"Cannot start debate: status is {self.debate_status}")
            return False
        
        try:
            self.debate_status = "in_progress"
            self.current_turn = 0
            
            # Generate moderator introduction
            introduction = self.moderator.generate_introduction()
            self._add_to_transcript("moderator", introduction, "introduction")
            
            # Generate opening statements from debaters
            for debater in self.debaters:
                opening = debater.generate_opening_statement(self.topic)
                self._add_to_transcript(debater.name, opening, "opening_statement")
                
                # Have moderator evaluate the argument
                self.moderator.evaluate_argument(
                    speaker=debater.name,
                    argument=opening,
                    turn_number=0
                )
            
            logger.info(f"Started debate on topic: {self.topic}")
            return True
        except Exception as e:
            logger.error(f"Error starting debate: {e}")
            self.debate_status = "error"
            return False
    
    def run_debate_turn(self) -> Tuple[bool, Optional[str]]:
        """
        Run a single turn of the debate.
        
        Returns:
            Tuple of (success, status_message)
        """
        if self.debate_status != "in_progress":
            return False, f"Cannot run turn: debate status is {self.debate_status}"
        
        if self.current_turn >= self.max_turns:
            return self.end_debate()
        
        try:
            self.current_turn += 1
            logger.info(f"Starting debate turn {self.current_turn}/{self.max_turns}")
            
            # For each debater, generate an argument or rebuttal
            for i, debater in enumerate(self.debaters):
                # Get opponent arguments to address
                opponent_arguments = self._get_opponent_arguments(debater.name)
                
                # If this is the first turn or there are no opponent arguments, 
                # generate a general argument
                if self.current_turn == 1 or not opponent_arguments:
                    # Get transcript summary for context
                    transcript_summary = self._get_transcript_summary()
                    
                    argument = debater.generate_argument(
                        topic=self.topic,
                        turn_number=self.current_turn,
                        transcript_summary=transcript_summary
                    )
                    
                    message_type = "argument"
                else:
                    # Generate a rebuttal to opponent arguments
                    argument = debater.generate_rebuttal(
                        topic=self.topic,
                        turn_number=self.current_turn,
                        opponent_arguments=opponent_arguments
                    )
                    
                    message_type = "rebuttal"
                
                # Add to transcript
                self._add_to_transcript(debater.name, argument, message_type)
                
                # Have moderator evaluate the argument
                self.moderator.evaluate_argument(
                    speaker=debater.name,
                    argument=argument,
                    turn_number=self.current_turn
                )
                
                # Perform fact-checking if enabled
                if self.config.get("fact_checking", False):
                    fact_check = self.moderator.generate_fact_check(
                        statement=argument,
                        turn_number=self.current_turn
                    )
                    
                    if fact_check:
                        self._add_to_transcript("moderator", fact_check, "fact_check")
                        logger.info(f"Added fact check for argument by {debater.name}")
                
                # If this isn't the last debater, generate a transition
                if i < len(self.debaters) - 1:
                    next_debater = self.debaters[i + 1]
                    
                    transition = self.moderator.generate_transition(
                        current_speaker=debater.name,
                        next_speaker=next_debater.name,
                        turn_number=self.current_turn,
                        total_turns=self.max_turns
                    )
                    
                    self._add_to_transcript("moderator", transition, "transition")
            
            # Generate a summary after each turn
            summary = self.moderator.generate_summary(
                turn_number=self.current_turn,
                transcript=self.transcript
            )
            
            self._add_to_transcript("moderator", summary, "summary")
            
            # Check if this is the last turn
            if self.current_turn >= self.max_turns:
                return self.end_debate()
            
            return True, f"Completed turn {self.current_turn}/{self.max_turns}"
        except Exception as e:
            logger.error(f"Error in debate turn {self.current_turn}: {e}")
            return False, f"Error in turn {self.current_turn}: {str(e)}"
    
    def end_debate(self) -> Tuple[bool, str]:
        """
        End the debate.
        
        Returns:
            Tuple of (success, status_message)
        """
        if self.debate_status not in ["in_progress", "ready"]:
            return False, f"Cannot end debate: status is {self.debate_status}"
        
        try:
            # Generate closing statements from debaters
            for debater in self.debaters:
                closing = debater.generate_closing_statement(
                    topic=self.topic,
                    turn_number=self.current_turn
                )
                
                self._add_to_transcript(debater.name, closing, "closing_statement")
                
                # Have moderator evaluate the closing statement
                self.moderator.evaluate_argument(
                    speaker=debater.name,
                    argument=closing,
                    turn_number=self.current_turn
                )
            
            # Generate moderator conclusion
            conclusion = self.moderator.generate_conclusion()
            self._add_to_transcript("moderator", conclusion, "conclusion")
            
            # Get debate results
            results = self.moderator.get_debate_results()
            
            # Save the debate transcript and results
            self._save_debate()
            
            self.debate_status = "completed"
            logger.info(f"Ended debate on topic: {self.topic}. Winner: {results.get('winner')}")
            
            return True, f"Debate completed. Winner: {results.get('winner')}"
        except Exception as e:
            logger.error(f"Error ending debate: {e}")
            self.debate_status = "error"
            return False, f"Error ending debate: {str(e)}"
    
    def _add_to_transcript(self, speaker: str, message: str, message_type: str) -> None:
        """
        Add a message to the debate transcript.
        
        Args:
            speaker: Name of the speaker
            message: Message content
            message_type: Type of message
        """
        self.transcript.append({
            "speaker": speaker,
            "content": message,
            "type": message_type,
            "turn": self.current_turn,
            "timestamp": datetime.datetime.now().isoformat()
        })
    
    def _get_opponent_arguments(self, debater_name: str) -> List[Dict[str, Any]]:
        """
        Get arguments from opponents for a given debater.
        
        Args:
            debater_name: Name of the debater
            
        Returns:
            List of opponent argument dictionaries
        """
        # Get arguments from the most recent turn
        recent_arguments = [
            {
                "speaker": msg["speaker"],
                "content": msg["content"],
                "type": msg["type"],
                "turn": msg["turn"]
            }
            for msg in self.transcript
            if msg["speaker"] != debater_name and msg["speaker"] != "moderator" and 
               (msg["turn"] == self.current_turn or msg["turn"] == self.current_turn - 1)
               and msg["type"] in ["argument", "rebuttal", "opening_statement"]
        ]
        
        return recent_arguments[-3:]  # Limit to the most recent 3 arguments
    
    def _get_transcript_summary(self) -> str:
        """
        Get a summary of the debate transcript.
        
        Returns:
            Summary string
        """
        # For a real implementation, this would use an LLM to summarize
        # For now, just use a simple summary
        
        # Count messages by type and speaker
        type_counts = {}
        speaker_messages = {}
        
        for msg in self.transcript:
            msg_type = msg["type"]
            speaker = msg["speaker"]
            
            if msg_type not in type_counts:
                type_counts[msg_type] = 0
            type_counts[msg_type] += 1
            
            if speaker not in speaker_messages:
                speaker_messages[speaker] = 0
            speaker_messages[speaker] += 1
        
        # Create a simple summary
        summary = f"Debate on topic: {self.topic}. "
        summary += f"Current turn: {self.current_turn} of {self.max_turns}. "
        summary += "Participants: " + ", ".join(speaker_messages.keys()) + ". "
        
        if "argument" in type_counts:
            summary += f"{type_counts.get('argument', 0)} arguments, "
        if "rebuttal" in type_counts:
            summary += f"{type_counts.get('rebuttal', 0)} rebuttals, "
        if "summary" in type_counts:
            summary += f"{type_counts.get('summary', 0)} summaries. "
        
        return summary
    
    def _save_debate(self) -> bool:
        """
        Save the debate transcript and results to files.
        
        Returns:
            True if the debate was saved successfully, False otherwise
        """
        try:
            # Create debates directory if it doesn't exist
            debates_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "config",
                "debates"
            )
            os.makedirs(debates_dir, exist_ok=True)
            
            # Prepare the debate data
            debate_data = {
                "id": self.debate_id,
                "topic": self.topic,
                "rules": self.debate_rules,
                "status": self.debate_status,
                "turns": self.current_turn,
                "max_turns": self.max_turns,
                "timestamp": datetime.datetime.now().isoformat(),
                "transcript": self.transcript,
                "results": self.moderator.get_debate_results() if self.moderator else None,
                "debaters": [
                    {
                        "name": debater.name,
                        "stance": debater.stance,
                        "debate_style": debater.debate_style,
                        "stats": debater.get_debate_stats()
                    }
                    for debater in self.debaters
                ]
            }
            
            # Save to a unique file
            filename = f"{self.debate_id[:8]}.json"
            file_path = os.path.join(debates_dir, filename)
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(debate_data, f, indent=2)
            
            logger.info(f"Saved debate data to: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving debate: {e}")
            return False
    
    def get_transcript(self, speaker: Optional[str] = None, message_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get the debate transcript, optionally filtered by speaker or message type.
        
        Args:
            speaker: Optional name of the speaker to filter by
            message_type: Optional type of message to filter by
            
        Returns:
            List of transcript messages
        """
        if speaker and message_type:
            return [msg for msg in self.transcript if msg["speaker"] == speaker and msg["type"] == message_type]
        elif speaker:
            return [msg for msg in self.transcript if msg["speaker"] == speaker]
        elif message_type:
            return [msg for msg in self.transcript if msg["type"] == message_type]
        else:
            return self.transcript
    
    def get_results(self) -> Dict[str, Any]:
        """
        Get the results of the debate.
        
        Returns:
            Dictionary of debate results
        """
        if self.debate_status != "completed":
            return {
                "status": self.debate_status,
                "message": "Debate has not been completed"
            }
        
        return self.moderator.get_debate_results() if self.moderator else {
            "status": "error",
            "message": "No moderator available"
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the debate.
        
        Returns:
            Dictionary of debate status information
        """
        return {
            "id": self.debate_id,
            "topic": getattr(self, "topic", "Not set"),
            "status": self.debate_status,
            "current_turn": self.current_turn,
            "max_turns": self.max_turns,
            "debaters": [debater.name for debater in self.debaters],
            "moderator": self.moderator.name if self.moderator else None,
            "transcript_length": len(self.transcript)
        }