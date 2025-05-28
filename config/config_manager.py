"""
Configuration Manager Module

This module provides utilities for loading and managing configuration data
for the debate simulator, including personas, debate templates, and settings.
"""

import os
import json
import uuid
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Manages loading, saving, and accessing configuration data for the application.
    """
    
    def __init__(self, config_dir: str = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory containing configuration files
                       (default: config/ relative to project root)
        """
        if config_dir is None:
            # Default to config directory relative to this file
            self.config_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                "config"
            )
        else:
            self.config_dir = config_dir
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Create subdirectories if they don't exist
        self.personas_dir = os.path.join(self.config_dir, "personas")
        self.debates_dir = os.path.join(self.config_dir, "debates")
        self.settings_path = os.path.join(self.config_dir, "settings.json")
        
        os.makedirs(self.personas_dir, exist_ok=True)
        os.makedirs(self.debates_dir, exist_ok=True)
        
        # Initialize caches
        self._personas_cache = {}
        self._debates_cache = {}
        self._settings_cache = None
        
        logger.info(f"Initialized ConfigManager with config directory: {self.config_dir}")
    
    def load_personas(self, refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Load all available personas.
        
        Args:
            refresh: Whether to refresh the cache
            
        Returns:
            Dictionary mapping persona IDs to persona data
        """
        if not refresh and self._personas_cache:
            return self._personas_cache
        
        personas = {}
        
        try:
            for filename in os.listdir(self.personas_dir):
                if filename.endswith('.json'):
                    persona_id = os.path.splitext(filename)[0]
                    persona_path = os.path.join(self.personas_dir, filename)
                    
                    with open(persona_path, 'r', encoding='utf-8') as f:
                        persona_data = json.load(f)
                        
                    # Ensure persona has an ID field matching the filename
                    persona_data['id'] = persona_id
                    personas[persona_id] = persona_data
            
            logger.info(f"Loaded {len(personas)} personas")
        except Exception as e:
            logger.error(f"Error loading personas: {e}")
        
        # Fall back to default personas if none are found
        if not personas:
            personas = self._get_default_personas()
            logger.info(f"Using {len(personas)} default personas")
            
            # Save default personas to files
            for persona_id, persona_data in personas.items():
                self.save_persona(persona_data)
        
        self._personas_cache = personas
        return personas
    
    def _get_default_personas(self) -> Dict[str, Dict[str, Any]]:
        """
        Get default personas to use if none are found.
        
        Returns:
            Dictionary of default personas
        """
        return {
            "logical_debater": {
                "id": "logical_debater",
                "name": "Logical Debater",
                "description": "A logical and analytical debater who relies on facts and rational arguments",
                "traits": [
                    "logical",
                    "analytical",
                    "factual",
                    "methodical",
                    "precise"
                ],
                "debate_style": "logical"
            },
            "emotional_debater": {
                "id": "emotional_debater",
                "name": "Emotional Debater",
                "description": "An emotional and passionate debater who appeals to values and emotions",
                "traits": [
                    "emotional",
                    "passionate",
                    "empathetic",
                    "values-driven",
                    "inspiring"
                ],
                "debate_style": "emotional"
            },
            "neutral_moderator": {
                "id": "neutral_moderator",
                "name": "Neutral Moderator",
                "description": "A balanced and fair moderator who ensures equal speaking time and civility",
                "traits": [
                    "balanced",
                    "neutral",
                    "fair",
                    "organized",
                    "clear"
                ],
                "moderation_style": "neutral"
            },
            "provocative_moderator": {
                "id": "provocative_moderator",
                "name": "Provocative Moderator",
                "description": "A challenging moderator who pushes debaters with tough questions",
                "traits": [
                    "provocative",
                    "challenging",
                    "incisive",
                    "energetic",
                    "direct"
                ],
                "moderation_style": "provocative"
            }
        }
    
    def get_persona(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific persona by ID.
        
        Args:
            persona_id: ID of the persona to retrieve
            
        Returns:
            Persona data dictionary or None if not found
        """
        # Ensure personas are loaded
        if not self._personas_cache:
            self.load_personas()
        
        return self._personas_cache.get(persona_id)
    
    def save_persona(self, persona_data: Dict[str, Any]) -> bool:
        """
        Save a persona to file.
        
        Args:
            persona_data: Persona data dictionary
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            persona_id = persona_data.get('id', str(uuid.uuid4()))
            persona_data['id'] = persona_id
            
            persona_path = os.path.join(self.personas_dir, f"{persona_id}.json")
            
            with open(persona_path, 'w', encoding='utf-8') as f:
                json.dump(persona_data, f, indent=2)
            
            # Update cache
            if not self._personas_cache:
                self.load_personas()
                
            self._personas_cache[persona_id] = persona_data
            
            logger.info(f"Saved persona: {persona_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving persona: {e}")
            return False
    
    def delete_persona(self, persona_id: str) -> bool:
        """
        Delete a persona.
        
        Args:
            persona_id: ID of the persona to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            persona_path = os.path.join(self.personas_dir, f"{persona_id}.json")
            
            if os.path.exists(persona_path):
                os.remove(persona_path)
                
                # Update cache
                if persona_id in self._personas_cache:
                    del self._personas_cache[persona_id]
                
                logger.info(f"Deleted persona: {persona_id}")
                return True
            else:
                logger.warning(f"Persona not found for deletion: {persona_id}")
                return False
        except Exception as e:
            logger.error(f"Error deleting persona: {e}")
            return False
    
    def load_debate_configs(self, refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Load all saved debate configurations.
        
        Args:
            refresh: Whether to refresh the cache
            
        Returns:
            List of debate configuration dictionaries
        """
        if not refresh and self._debates_cache:
            return list(self._debates_cache.values())
        
        debate_configs = {}
        
        try:
            for filename in os.listdir(self.debates_dir):
                if filename.endswith('.json'):
                    debate_id = os.path.splitext(filename)[0]
                    debate_path = os.path.join(self.debates_dir, filename)
                    
                    with open(debate_path, 'r', encoding='utf-8') as f:
                        debate_data = json.load(f)
                    
                    # Ensure debate has an ID field matching the filename
                    debate_data['id'] = debate_id
                    debate_configs[debate_id] = debate_data
            
            logger.info(f"Loaded {len(debate_configs)} debate configurations")
        except Exception as e:
            logger.error(f"Error loading debate configurations: {e}")
        
        self._debates_cache = debate_configs
        return list(debate_configs.values())
    
    def get_debate_config(self, debate_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific debate configuration by ID.
        
        Args:
            debate_id: ID of the debate configuration to retrieve
            
        Returns:
            Debate configuration dictionary or None if not found
        """
        # Ensure debate configs are loaded
        if not self._debates_cache:
            self.load_debate_configs()
        
        return self._debates_cache.get(debate_id)
    
    def save_debate_config(self, debate_config: Dict[str, Any]) -> str:
        """
        Save a debate configuration to file.
        
        Args:
            debate_config: Debate configuration dictionary
            
        Returns:
            ID of the saved debate configuration
        """
        try:
            debate_id = debate_config.get('id', str(uuid.uuid4()))
            debate_config['id'] = debate_id
            
            debate_path = os.path.join(self.debates_dir, f"{debate_id}.json")
            
            with open(debate_path, 'w', encoding='utf-8') as f:
                json.dump(debate_config, f, indent=2)
            
            # Update cache
            if not self._debates_cache:
                self.load_debate_configs()
                
            self._debates_cache[debate_id] = debate_config
            
            logger.info(f"Saved debate configuration: {debate_id}")
            return debate_id
        except Exception as e:
            logger.error(f"Error saving debate configuration: {e}")
            return ""
    
    def delete_debate_config(self, debate_id: str) -> bool:
        """
        Delete a debate configuration.
        
        Args:
            debate_id: ID of the debate configuration to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            debate_path = os.path.join(self.debates_dir, f"{debate_id}.json")
            
            if os.path.exists(debate_path):
                os.remove(debate_path)
                
                # Update cache
                if debate_id in self._debates_cache:
                    del self._debates_cache[debate_id]
                
                logger.info(f"Deleted debate configuration: {debate_id}")
                return True
            else:
                logger.warning(f"Debate configuration not found for deletion: {debate_id}")
                return False
        except Exception as e:
            logger.error(f"Error deleting debate configuration: {e}")
            return False
    
    def load_settings(self, refresh: bool = False) -> Dict[str, Any]:
        """
        Load application settings.
        
        Args:
            refresh: Whether to refresh the cache
            
        Returns:
            Dictionary of application settings
        """
        if not refresh and self._settings_cache:
            return self._settings_cache
        
        settings = self._get_default_settings()
        
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    
                # Update default settings with loaded settings
                settings.update(loaded_settings)
                
                logger.info(f"Loaded application settings")
        except Exception as e:
            logger.error(f"Error loading application settings: {e}")
            # Save default settings if loading fails
            self.save_settings(settings)
        
        self._settings_cache = settings
        return settings
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """
        Get default application settings.
        
        Returns:
            Dictionary of default settings
        """
        return {
            "llm_config": {
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 500
            },
            "ui": {
                "theme": "light",
                "auto_scroll": True,
                "show_timestamps": True
            },
            "debate": {
                "default_turns": 3,
                "default_include_opening": True,
                "default_include_closing": True,
                "default_fact_checking": False,
                "export_format": "markdown"
            }
        }
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Save application settings.
        
        Args:
            settings: Settings dictionary
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            
            # Update cache
            self._settings_cache = settings
            
            logger.info(f"Saved application settings")
            return True
        except Exception as e:
            logger.error(f"Error saving application settings: {e}")
            return False

# Global config manager instance
_config_manager = None

def get_config_manager() -> ConfigManager:
    """
    Get the global configuration manager instance.
    
    Returns:
        The global configuration manager instance
    """
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager()
    
    return _config_manager