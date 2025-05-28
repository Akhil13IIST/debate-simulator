"""
Debater Agent Module

This module defines the DebaterAgent class which represents a debater
in the debate simulator. Debaters make arguments, rebuttals, and closing
statements based on their persona and assigned stance.
"""

import logging
from typing import Dict, List, Any, Optional

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class DebaterAgent(BaseAgent):
    """
    Agent class representing a debater in the debate simulator.
    """
    
    def __init__(self, 
                 name: str, 
                 persona: Dict[str, Any],
                 stance: str,
                 debate_style: Optional[str] = None,
                 llm_config: Optional[Dict[str, Any]] = None):
        """
        Initialize a debater agent.
        
        Args:
            name: Name of the debater
            persona: Dictionary containing persona details (traits, description, etc.)
            stance: Stance on the debate topic ("for", "against", or "neutral")
            debate_style: Debating style (e.g., "logical", "emotional")
            llm_config: Configuration for the language model
        """
        super().__init__(name, persona, llm_config)
        
        self.stance = stance
        self.debate_style = debate_style or persona.get("debate_style", "logical")
        self.current_topic = None
        
        # Initialize debater-specific state
        self.arguments_made = []
        self.opponent_arguments_addressed = []
        
        logger.info(f"Initialized debater agent: {name} with stance: {stance}")
    
    def _get_agent_type(self) -> str:
        """
        Get the type of agent for prompt template selection.
        
        Returns:
            String identifying the agent type
        """
        return "debater"
    
    def generate_opening_statement(self, topic: str) -> str:
        """
        Generate an opening statement for the debate.
        
        Args:
            topic: The debate topic
            
        Returns:
            Opening statement string
        """
        # Store the current topic to ensure consistency
        self.current_topic = topic
        
        # Make the topic more explicit in the context
        context = {
            "message_type": "opening_statement",
            "topic": topic,
            "exact_topic": f"EXACT DEBATE TOPIC: '{topic}'", # Added for emphasis
            "stance": self.stance,
            "debate_style": self.debate_style,
            "turn_number": 1
        }
        
        statement = self.generate_message(context)
        
        # Track this argument
        self.arguments_made.append({
            "type": "opening",
            "content": statement,
            "topic": topic
        })
        
        return statement
    
    def generate_argument(self, topic: str, turn_number: int, transcript_summary: Optional[str] = None) -> str:
        """
        Generate a general argument for the debate.
        
        Args:
            topic: The debate topic
            turn_number: Current turn number
            transcript_summary: Optional summary of the debate transcript so far
            
        Returns:
            Argument string
        """
        # Ensure topic consistency
        if self.current_topic is None:
            self.current_topic = topic
        
        # Make the topic more explicit in the context
        context = {
            "message_type": "argument",
            "topic": self.current_topic,
            "exact_topic": f"EXACT DEBATE TOPIC: '{self.current_topic}'", # Added for emphasis
            "stance": self.stance,
            "debate_style": self.debate_style,
            "turn_number": turn_number
        }
        
        if transcript_summary:
            context["transcript_summary"] = transcript_summary
        
        argument = self.generate_message(context)
        
        # Track this argument
        self.arguments_made.append({
            "type": "argument",
            "content": argument,
            "topic": self.current_topic,
            "turn": turn_number
        })
        
        return argument
    
    def generate_rebuttal(self, topic: str, turn_number: int, opponent_arguments: List[Dict[str, Any]]) -> str:
        """
        Generate a rebuttal to opponent arguments.
        
        Args:
            topic: The debate topic
            turn_number: Current turn number
            opponent_arguments: List of opponent arguments to address
            
        Returns:
            Rebuttal string
        """
        # Ensure topic consistency
        if self.current_topic is None:
            self.current_topic = topic
        
        # Make the topic more explicit in the context
        context = {
            "message_type": "rebuttal",
            "topic": self.current_topic,
            "exact_topic": f"EXACT DEBATE TOPIC: '{self.current_topic}'", # Added for emphasis
            "stance": self.stance,
            "debate_style": self.debate_style,
            "turn_number": turn_number,
            "opponent_arguments": opponent_arguments
        }
        
        rebuttal = self.generate_message(context)
        
        # Track this rebuttal and the opponent arguments addressed
        self.arguments_made.append({
            "type": "rebuttal",
            "content": rebuttal,
            "topic": self.current_topic,
            "turn": turn_number
        })
        
        for arg in opponent_arguments:
            self.opponent_arguments_addressed.append({
                "content": arg.get("content", ""),
                "speaker": arg.get("speaker", "Unknown"),
                "turn": turn_number
            })
        
        return rebuttal
    
    def generate_closing_statement(self, topic: str, turn_number: int) -> str:
        """
        Generate a closing statement for the debate.
        
        Args:
            topic: The debate topic
            turn_number: Current turn number
            
        Returns:
            Closing statement string
        """
        # Ensure topic consistency
        if self.current_topic is None:
            self.current_topic = topic
            
        # Make the topic more explicit in the context
        context = {
            "message_type": "closing_statement",
            "topic": self.current_topic,
            "exact_topic": f"EXACT DEBATE TOPIC: '{self.current_topic}'", # Added for emphasis
            "stance": self.stance,
            "debate_style": self.debate_style,
            "turn_number": turn_number,
            "arguments_made": self.arguments_made,
            "points_addressed": self.opponent_arguments_addressed
        }
        
        statement = self.generate_message(context)
        
        # Track this argument
        self.arguments_made.append({
            "type": "closing",
            "content": statement,
            "topic": self.current_topic,
            "turn": turn_number
        })
        
        return statement
    
    def get_stance_description(self) -> str:
        """
        Get a human-readable description of the debater's stance.
        
        Returns:
            Description of the stance
        """
        stance_descriptions = {
            "for": "in favor of",
            "against": "opposed to",
            "neutral": "neutral on",
            "pro": "in favor of",
            "con": "opposed to"
        }
        
        return stance_descriptions.get(self.stance.lower(), self.stance)
    
    def get_debate_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the debater's performance in the debate.
        
        Returns:
            Dictionary of debate statistics
        """
        return {
            "name": self.name,
            "stance": self.stance,
            "debate_style": self.debate_style,
            "arguments_count": len(self.arguments_made),
            "rebuttals_count": len([a for a in self.arguments_made if a["type"] == "rebuttal"]),
            "points_addressed": len(self.opponent_arguments_addressed)
        }