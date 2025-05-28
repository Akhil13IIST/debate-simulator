"""
Debate Simulator Application

This is the main application module for the debate simulator.
It provides a streamlit-based UI for configuring and running debates.
"""

import os
import json
import time
import logging
import datetime
import streamlit as st
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from debate_engine import DebateEngine
from config.config_manager import ConfigManager
from utils.logging_utils import setup_logging
from ui.components import (
    render_header,
    render_debate_configuration,
    render_debate_controls,
    render_debate_transcript,
    render_debate_summary,
    render_persona_editor
)

# Set up logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(log_dir, f"debate_simulator_{timestamp}.log")
logger = setup_logging(log_dir=log_dir, log_level=logging.INFO, app_name="debate_simulator")

# Load environment variables from .env file
load_dotenv()

# Initialize session state variables if they don't exist
def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'debate_engine' not in st.session_state:
        st.session_state.debate_engine = None
    
    if 'config_manager' not in st.session_state:
        st.session_state.config_manager = ConfigManager()
    
    if 'debate_started' not in st.session_state:
        st.session_state.debate_started = False
    
    if 'debate_completed' not in st.session_state:
        st.session_state.debate_completed = False
    
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = "Setup"
    
    # Add LLM configuration options
    if 'llm_config' not in st.session_state:
        st.session_state.llm_config = {
            "model": "llama3-8b-8192",
            "temperature": 0.75,  # Slightly increased for more creative responses
            "max_tokens": 1000,   # Increased token limit for more detailed responses
            "top_p": 0.92         # Slightly increased for better quality
        }
    
    if 'groq_api_key' not in st.session_state:
        # Get API key from environment variables (loaded from .env file)
        st.session_state.groq_api_key = os.environ.get("GROQ_API_KEY", "")
    
    if 'available_personas' not in st.session_state:
        # Load available personas from config directory
        personas_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "config", 
            "personas"
        )
        personas = {}
        
        for filename in os.listdir(personas_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(personas_dir, filename), 'r') as f:
                        persona_data = json.load(f)
                        personas[persona_data.get('name', filename)] = persona_data
                except Exception as e:
                    logger.error(f"Error loading persona {filename}: {e}")
        
        st.session_state.available_personas = personas
    
    if 'topic' not in st.session_state:
        st.session_state.topic = ""
    
    if 'selected_debaters' not in st.session_state:
        st.session_state.selected_debaters = []
    
    if 'selected_moderator' not in st.session_state:
        st.session_state.selected_moderator = None
    
    if 'max_turns' not in st.session_state:
        st.session_state.max_turns = 3
    
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    
    if 'current_persona' not in st.session_state:
        st.session_state.current_persona = None

# Callback functions
def start_debate():
    """Start a new debate with the configured settings."""
    try:
        if not st.session_state.topic:
            st.warning("Please enter a debate topic.")
            return
        
        if len(st.session_state.selected_debaters) < 2:
            st.warning("Please select at least two debaters.")
            return
        
        if not st.session_state.selected_moderator:
            st.warning("Please select a moderator.")
            return
        
        # Show a status message to indicate processing
        status_placeholder = st.empty()
        status_placeholder.info("Setting up debate... This may take a few moments.")
        
        # Create debate engine instance
        st.session_state.debate_engine = DebateEngine()
        
        # Set up default config with Groq LLM settings
        config = {
            "max_turns": st.session_state.max_turns,
            "llm_config": st.session_state.llm_config
        }
        
        # Set Groq API key in environment variable for the agents to use
        if st.session_state.groq_api_key:
            os.environ["GROQ_API_KEY"] = st.session_state.groq_api_key
        
        status_placeholder.info("Finding debate personas...")
        
        # Get selected personas by ID (not by name)
        debater_personas = []
        for debater_id in st.session_state.selected_debaters:
            # Find persona by ID or by name
            persona = None
            for p in st.session_state.available_personas.values():
                if p.get("id") == debater_id or p.get("name") == debater_id:
                    persona = p
                    break
            
            if persona:
                debater_personas.append(persona)
            else:
                logger.warning(f"Could not find persona for debater ID/name: {debater_id}")
        
        # Find moderator persona by ID or by name
        moderator_id = st.session_state.selected_moderator
        moderator_persona = None
        for p in st.session_state.available_personas.values():
            if p.get("id") == moderator_id or p.get("name") == moderator_id:
                moderator_persona = p
                break
        
        if not moderator_persona:
            logger.warning(f"Could not find persona for moderator ID/name: {moderator_id}")
            st.warning("Could not find the selected moderator persona. Using a default moderator.")
            # Create a default moderator persona
            moderator_persona = {
                "name": "Default Moderator",
                "description": "A neutral, professional debate moderator.",
                "traits": ["neutral", "professional", "fair"],
                "moderation_style": "neutral"
            }
        
        status_placeholder.info("Setting up debate... Configuring debate engine...")
        
        # Setup the debate
        success = st.session_state.debate_engine.setup_debate(
            topic=st.session_state.topic,
            debater_personas=debater_personas,
            moderator_persona=moderator_persona,
            debate_rules={
                "format": "structured",
                "max_rounds": st.session_state.max_turns,
                "scoring_criteria": ["clarity", "evidence", "persuasiveness"]
            }
        )
        
        if success:
            status_placeholder.info("Starting debate... Generating introductions and opening statements...")
            
            # Start the debate
            start_success = st.session_state.debate_engine.start_debate()
            if start_success:
                st.session_state.debate_started = True
                st.session_state.current_tab = "Debate"
                logger.info(f"Started debate on topic: {st.session_state.topic}")
                # Clear the status message since we're transitioning to the Debate tab
                status_placeholder.empty()
            else:
                status_placeholder.error("Failed to start the debate.")
        else:
            status_placeholder.error("Failed to set up the debate.")
    
    except Exception as e:
        logger.error(f"Error starting debate: {e}")
        st.error(f"An error occurred: {str(e)}")

def run_debate_turn():
    """Run a single turn of the current debate."""
    try:
        if not st.session_state.debate_engine:
            st.warning("No active debate.")
            return
        
        # Create a status placeholder for progress updates
        status_placeholder = st.empty()
        status_placeholder.info(f"Running debate turn {st.session_state.debate_engine.current_turn + 1}... This may take a few moments.")
        
        # Run a debate turn
        success, message = st.session_state.debate_engine.run_debate_turn()
        
        if success:
            st.session_state.debate_status = st.session_state.debate_engine.get_status()
            
            # Check if debate has been completed
            if st.session_state.debate_status["status"] == "completed":
                status_placeholder.success("Debate completed! Displaying results...")
                st.session_state.debate_completed = True
                st.session_state.current_tab = "Results"
            else:
                status_placeholder.success(f"Turn completed: {message}")
                # Force a rerun to update the UI with the new transcript
                st.rerun()
            
            logger.info(f"Completed debate turn: {message}")
        else:
            status_placeholder.error(f"Failed to run debate turn: {message}")
    
    except Exception as e:
        logger.error(f"Error running debate turn: {e}")
        st.error(f"An error occurred: {str(e)}")

def end_debate():
    """End the current debate early."""
    try:
        if not st.session_state.debate_engine:
            st.warning("No active debate.")
            return
        
        # End the debate
        success, message = st.session_state.debate_engine.end_debate()
        
        if success:
            st.session_state.debate_completed = True
            st.session_state.current_tab = "Results"
            logger.info(f"Ended debate: {message}")
        else:
            st.error(f"Failed to end debate: {message}")
    
    except Exception as e:
        logger.error(f"Error ending debate: {e}")
        st.error(f"An error occurred: {str(e)}")

def reset_debate():
    """Reset the debate state and return to setup."""
    st.session_state.debate_engine = None
    st.session_state.debate_started = False
    st.session_state.debate_completed = False
    st.session_state.current_tab = "Setup"
    logger.info("Reset debate state")

def add_debater(debater_name):
    """Add a debater to the selected debaters."""
    if debater_name not in st.session_state.selected_debaters:
        st.session_state.selected_debaters.append(debater_name)

def remove_debater(debater_name):
    """Remove a debater from the selected debaters."""
    if debater_name in st.session_state.selected_debaters:
        st.session_state.selected_debaters.remove(debater_name)

def set_moderator(moderator_name):
    """Set the selected moderator."""
    st.session_state.selected_moderator = moderator_name

def save_persona(persona_data):
    """Save a persona to the personas directory."""
    try:
        # Ensure the persona has a name
        if not persona_data.get("name"):
            st.warning("Persona must have a name.")
            return False
        
        # Sanitize the filename
        filename = persona_data["name"].lower().replace(" ", "_") + ".json"
        
        # Create personas directory if it doesn't exist
        personas_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "config", 
            "personas"
        )
        os.makedirs(personas_dir, exist_ok=True)
        
        # Save the persona
        file_path = os.path.join(personas_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(persona_data, f, indent=2)
        
        # Update available personas
        st.session_state.available_personas[persona_data["name"]] = persona_data
        
        logger.info(f"Saved persona: {persona_data['name']}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving persona: {e}")
        st.error(f"An error occurred: {str(e)}")
        return False

def delete_persona(persona_name):
    """Delete a persona from the personas directory."""
    try:
        if persona_name not in st.session_state.available_personas:
            st.warning(f"Persona '{persona_name}' not found.")
            return False
        
        # Delete from available personas
        persona_data = st.session_state.available_personas.pop(persona_name)
        
        # Delete file
        filename = persona_name.lower().replace(" ", "_") + ".json"
        personas_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "config", 
            "personas"
        )
        file_path = os.path.join(personas_dir, filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Remove from selected debaters if present
        if persona_name in st.session_state.selected_debaters:
            st.session_state.selected_debaters.remove(persona_name)
        
        # Remove as moderator if selected
        if st.session_state.selected_moderator == persona_name:
            st.session_state.selected_moderator = None
        
        logger.info(f"Deleted persona: {persona_name}")
        return True
    
    except Exception as e:
        logger.error(f"Error deleting persona: {e}")
        st.error(f"An error occurred: {str(e)}")
        return False

def process_debate_config(config):
    """Process the debate configuration."""
    st.session_state.topic = config.get("topic", "")
    
    # For debaters, store the persona IDs and stances
    debaters = config.get("debaters", [])
    st.session_state.selected_debaters = [
        d.get("persona_id") for d in debaters if "persona_id" in d
    ]
    
    # For moderator, store the persona ID
    moderator = config.get("moderator", {})
    st.session_state.selected_moderator = moderator.get("persona_id") if isinstance(moderator, dict) else moderator
    
    st.session_state.max_turns = config.get("max_turns", config.get("num_turns", 3))
    start_debate()

def main():
    """Main application function."""
    # Initialize session state
    initialize_session_state()
    
    # Render header
    render_header()
    
    # Create tabs
    tabs = ["Setup", "Personas", "Debate", "Results", "History"]
    selected_tab = st.tabs(tabs)
    
    # Setup tab
    with selected_tab[0]:
        if st.session_state.current_tab == "Setup":
            st.header("Debate Setup")
            
            # Add Groq LLM Settings section
            from ui.components import render_llm_settings
            render_llm_settings()
            
            # Render setup form - just pass the callback without additional call
            render_debate_configuration(
                personas=list(st.session_state.available_personas.values()),
                debate_configs=[],
                on_create_debate=lambda config: process_debate_config(config)
            )
    
    # Personas tab
    with selected_tab[1]:
        if st.session_state.current_tab == "Personas":
            st.header("Persona Management")
            
            # Render persona editor
            render_persona_editor(
                personas=list(st.session_state.available_personas.values()),
                on_save_persona=save_persona
            )
    
    # Debate tab
    with selected_tab[2]:
        if st.session_state.current_tab == "Debate":
            st.header("Debate in Progress")
            
            if st.session_state.debate_started and st.session_state.debate_engine:
                # Render debate configuration
                # Add basic debate info display here
                st.subheader(f"Topic: {st.session_state.topic}")
                st.write(f"Turns: {st.session_state.debate_engine.get_status().get('current_turn', 0)}/{st.session_state.max_turns}")
                
                # Render transcript
                render_debate_transcript(
                    transcript=st.session_state.debate_engine.get_transcript()
                )
                
                # Render controls
                render_debate_controls(
                    debate_status=st.session_state.debate_engine.get_status().get('status', 'not_started'),
                    on_start=run_debate_turn,
                    on_pause=lambda: None,  # No pause functionality yet
                    on_reset=reset_debate,
                    on_export=lambda: None  # No export functionality yet
                )
            else:
                st.info("No active debate. Go to the Setup tab to start a new debate.")
    
    # Results tab
    with selected_tab[3]:
        if st.session_state.current_tab == "Results":
            st.header("Debate Results")
            
            if st.session_state.debate_completed and st.session_state.debate_engine:
                # Render results
                render_debate_summary(
                    summary={
                        'topic': st.session_state.topic,
                        'status': st.session_state.debate_engine.get_status().get('status', 'unknown'),
                        'turns_completed': st.session_state.debate_engine.get_status().get('current_turn', 0),
                        'total_turns': st.session_state.max_turns,
                        'debaters': [{'name': name, 'stance': 'for' if i % 2 == 0 else 'against'} for i, name in enumerate(st.session_state.selected_debaters)], 
                        'scores': st.session_state.debate_engine.get_results().get('scores', {}),
                        'winner': st.session_state.debate_engine.get_results().get('winner', 'No winner'),
                        'detailed_results': st.session_state.debate_engine.get_results()
                    }
                )
            else:
                st.info("No completed debate. Complete a debate to see results.")
    
    # History tab
    with selected_tab[4]:
        st.header("Debate History")
        
        # Find all saved debates
        debates_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "config",
            "debates"
        )
        
        if os.path.exists(debates_dir):
            debate_files = [f for f in os.listdir(debates_dir) if f.endswith('.json')]
            
            if debate_files:
                selected_debate = st.selectbox(
                    "Select a previous debate:",
                    options=debate_files,
                    format_func=lambda x: x.replace('.json', '')
                )
                
                if selected_debate:
                    try:
                        with open(os.path.join(debates_dir, selected_debate), 'r') as f:
                            debate_data = json.load(f)
                        
                        st.subheader(f"Topic: {debate_data.get('topic', 'Unknown')}")
                        st.write(f"ID: {debate_data.get('id', 'Unknown')}")
                        st.write(f"Date: {debate_data.get('timestamp', 'Unknown')}")
                        st.write(f"Status: {debate_data.get('status', 'Unknown')}")
                        st.write(f"Turns: {debate_data.get('turns', 0)} / {debate_data.get('max_turns', 0)}")
                        
                        st.subheader("Transcript")
                        for msg in debate_data.get('transcript', []):
                            st.markdown(f"**{msg.get('speaker')}** ({msg.get('type')})")
                            st.markdown(msg.get('content', ''))
                            st.markdown("---")
                        
                        if debate_data.get('results'):
                            st.subheader("Results")
                            st.json(debate_data['results'])
                    
                    except Exception as e:
                        st.error(f"Error loading debate data: {str(e)}")
            else:
                st.info("No saved debates found.")
        else:
            st.info("No debate history available.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"An error occurred: {str(e)}")


@st.cache_data(
    hash_funcs={
        dict: lambda d: hash(frozenset((k, str(v)) for k, v in d.items())),
        list: lambda l: hash(tuple(str(x) for x in l))
    }
)
def process_debate_arguments(args_dict):
    """Process debate arguments with proper caching"""
    # No need to convert to frozenset here, the hash_funcs will handle it
    return _process_args(args_dict)

def _process_args(args_dict):
    """Helper function to process arguments"""
    st.session_state.topic = args_dict.get("topic", "")
    st.session_state.selected_debaters = args_dict.get("debaters", [])
    st.session_state.selected_moderator = args_dict.get("moderator", None)
    st.session_state.max_turns = args_dict.get("max_turns", 3)
    start_debate()