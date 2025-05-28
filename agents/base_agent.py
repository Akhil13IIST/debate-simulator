"""
Base Agent Module

This module defines the BaseAgent class which is the foundation for
all agent types in the debate simulator (debaters and moderator).
"""

import os
import json
import uuid
import logging
import datetime
from typing import Dict, List, Any, Optional, Union

from utils.prompt_utils import get_prompt_manager

logger = logging.getLogger(__name__)

class BaseAgent:
    """
    Base class for all agents in the debate simulator.
    
    This class provides the common functionality for all agent types,
    including state management, message generation, and history tracking.
    """
    
    def __init__(self, 
                 name: str, 
                 persona: Dict[str, Any],
                 llm_config: Optional[Dict[str, Any]] = None):
        """
        Initialize a base agent.
        
        Args:
            name: Name of the agent
            persona: Dictionary containing persona details (traits, description, etc.)
            llm_config: Configuration for the language model
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.persona = persona
        self.llm_config = llm_config or {}
        self.message_history = []
        self.state = {}
        
        # Get prompt manager instance
        self.prompt_manager = get_prompt_manager()
        
        logger.info(f"Initialized agent: {self.name} ({self.__class__.__name__})")
    
    def generate_message(self, context: Dict[str, Any]) -> str:
        """
        Generate a message based on the given context.
        
        Args:
            context: Dictionary containing context for the message
            
        Returns:
            Generated message string
        """
        message_type = context.get("message_type", "generic")
        prompt_template = f"{self._get_agent_type()}_{message_type}"
        
        # Handle special case for debate topic - ensure it's emphasized in system prompt
        topic = context.get("topic", "")
        
        # Combine context with agent attributes, but flatten persona to avoid unhashable dict issues
        prompt_context = {
            "name": self.name,
            "persona_description": self.persona.get("description", ""),
            "persona_traits": self.persona.get("traits", []),
            "persona_background": self.persona.get("background", ""),
            **context
        }
        
        # Format the prompt
        prompt = self.prompt_manager.format_template(prompt_template, **prompt_context)
        
        # Add topic emphasis to ensure LLM respects the exact topic
        if topic:
            prompt = f"IMPORTANT: The debate topic is exactly: \"{topic}\". Do not change or reinterpret the topic.\n\n{prompt}"
        
        # Generate response using LLM
        response = self._generate_response(prompt)
        
        # Save to message history
        self._add_to_history(message_type, context, response)
        
        return response
    
    def _generate_response(self, prompt: str) -> str:
        """
        Generate a response using the Groq language model API.
        
        Args:
            prompt: The prompt to send to the language model
            
        Returns:
            Generated response string
        """
        logger.debug(f"Generating response for {self.name} using prompt: {prompt[:100]}...")
        
        try:
            import groq
            import os
            
            # Get API key from environment variable
            api_key = os.environ.get("GROQ_API_KEY")
            
            if not api_key:
                logger.warning("GROQ_API_KEY not found in environment variables. Using placeholder response.")
                return f"No GROQ_API_KEY found. This is a placeholder response from {self.name}."
            
            # Initialize Groq client
            client = groq.Client(api_key=api_key)
            
            # Choose model based on configuration
            model = self.llm_config.get("model", "llama3-8b-8192")
            
            # Generate chat completion
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": f"You are {self.name}, {self.persona.get('description', 'an AI assistant')}. Your traits are: {', '.join(self.persona.get('traits', []))}"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.llm_config.get("temperature", 0.7),
                max_tokens=self.llm_config.get("max_tokens", 800),
                top_p=self.llm_config.get("top_p", 0.9),
            )
            
            # Extract the content from the response
            return response.choices[0].message.content
        
        except ImportError:
            logger.error("Groq package not installed. Please install with 'pip install groq'")
            return f"Error: Groq package not installed. This is a placeholder response from {self.name}."
        
        except Exception as e:
            logger.error(f"Error generating response via Groq: {e}")
            return f"Error: {str(e)}. This is a placeholder response from {self.name}."
    
    def _add_to_history(self, message_type: str, context: Dict[str, Any], response: str) -> None:
        """
        Add a message to the agent's history.
        
        Args:
            message_type: Type of message
            context: Message context dictionary
            response: Generated response
        """
        self.message_history.append({
            "type": message_type,
            "context": context,
            "response": response,
            "timestamp": self._get_timestamp()
        })
    
    def _get_timestamp(self) -> str:
        """
        Get the current timestamp as a string.
        
        Returns:
            ISO format timestamp string
        """
        return datetime.datetime.now().isoformat()
    
    def _get_agent_type(self) -> str:
        """
        Get the type of agent for prompt template selection.
        
        Returns:
            String identifying the agent type
        """
        return "agent"
    
    def get_all_messages(self, message_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all messages from the agent's history, optionally filtered by type.
        
        Args:
            message_type: Optional type of messages to filter by
            
        Returns:
            List of message dictionaries
        """
        if message_type:
            return [msg for msg in self.message_history if msg["type"] == message_type]
        return self.message_history
    
    def get_last_message(self, message_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get the last message from the agent's history, optionally filtered by type.
        
        Args:
            message_type: Optional type of message to filter by
            
        Returns:
            Last message dictionary or None if no messages found
        """
        messages = self.get_all_messages(message_type)
        return messages[-1] if messages else None
    
    def reset_history(self) -> None:
        """
        Reset the agent's message history.
        """
        self.message_history = []
        logger.info(f"Reset message history for agent: {self.name}")
    
    def update_state(self, key: str, value: Any) -> None:
        """
        Update the agent's state.
        
        Args:
            key: State key
            value: State value
        """
        self.state[key] = value
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the agent's state.
        
        Args:
            key: State key
            default: Default value if key not found
            
        Returns:
            State value or default if not found
        """
        return self.state.get(key, default)
    
    def save_to_file(self, filepath: str) -> bool:
        """
        Save the agent's state and history to a file.
        
        Args:
            filepath: Path to save the agent data
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Prepare agent data
            agent_data = {
                "id": self.id,
                "name": self.name,
                "persona": self.persona,
                "llm_config": self.llm_config,
                "state": self.state,
                "message_history": self.message_history,
                "agent_type": self.__class__.__name__
            }
            
            # Save to file
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(agent_data, f, indent=2)
            
            logger.info(f"Saved agent data to: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving agent data: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, filepath: str) -> "BaseAgent":
        """
        Load an agent from a file.
        
        Args:
            filepath: Path to the agent data file
            
        Returns:
            Loaded agent instance
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                agent_data = json.load(f)
            
            # Create agent instance
            agent = cls(
                name=agent_data["name"],
                persona=agent_data["persona"],
                llm_config=agent_data["llm_config"]
            )
            
            # Restore state
            agent.id = agent_data["id"]
            agent.state = agent_data["state"]
            agent.message_history = agent_data["message_history"]
            
            logger.info(f"Loaded agent from: {filepath}")
            return agent
        except Exception as e:
            logger.error(f"Error loading agent data: {e}")
            raise