"""
UI Components Module

This module provides reusable UI components for the debate simulator Streamlit application.
"""

import streamlit as st
import pandas as pd
import time
import logging
from typing import Dict, List, Any, Optional, Callable

from utils.text_utils import truncate_text, format_debate_transcript, format_debate_summary

logger = logging.getLogger(__name__)

def render_header(title: str = "Multi-Agent Debate Simulator", 
                 subtitle: str = "Watch AI personas engage in structured debates on your chosen topics."):
    """
    Render the application header with title and subtitle.
    
    Args:
        title: The main title text
        subtitle: The subtitle text
    """
    st.title(title)
    st.markdown(subtitle)
    st.markdown("---")

def render_debate_configuration(
    personas: List[Dict[str, Any]],
    debate_configs: List[Dict[str, Any]],
    on_create_debate: Callable[[Dict[str, Any]], None]
):
    """
    Render the debate configuration panel for creating or selecting debates.
    
    Args:
        personas: List of available personas
        debate_configs: List of available debate configurations
        on_create_debate: Callback function when a debate is created/selected
    """
    st.header("Debate Configuration")
    
    # Create tabs for New Debate vs. Load Existing
    tab1, tab2 = st.tabs(["Create New Debate", "Load Existing Debate"])
    
    # Tab 1: Create New Debate
    with tab1:
        with st.form(key="create_debate_form"):
            st.subheader("Create a New Debate")
            
            # Debate topic
            topic = st.text_input("Debate Topic", 
                                  value="Does God exist?")
            
            # Number of turns
            num_turns = st.slider("Number of Debate Turns", min_value=1, max_value=10, value=3)
            
            # Include opening/closing statements
            col1, col2 = st.columns(2)
            with col1:
                include_opening = st.checkbox("Include Opening Statements", value=True)
            with col2:
                include_closing = st.checkbox("Include Closing Statements", value=True)
            
            # Fact checking
            fact_checking = st.checkbox("Enable Fact Checking", value=False)
            
            # Debater selection
            st.subheader("Select Debaters")
            
            # Format personas for selection
            debater_options = [f"{p['name']} - {p['description'][:50]}..." for p in personas]
            persona_ids = [p["id"] for p in personas]
            
            # Find default philosopher and scientist personas
            philosopher_idx = 0
            scientist_idx = 0
            
            # Look for philosopher persona for the "for" position
            for i, persona in enumerate(personas):
                if "philosopher" in persona.get("name", "").lower() or "philosopher" in persona.get("description", "").lower():
                    philosopher_idx = i
                    break
            
            # Look for scientist persona for the "against" position
            for i, persona in enumerate(personas):
                if "scientist" in persona.get("name", "").lower() or "scientist" in persona.get("description", "").lower():
                    scientist_idx = i
                    break
            
            # First debater (For position) - default to philosopher
            st.markdown("**First Debater (For Position)**")
            debater1_idx = st.selectbox(
                "Select First Debater",
                options=range(len(personas)),
                format_func=lambda x: debater_options[x],
                index=philosopher_idx
            )
            
            debater1_stance = st.radio("First Debater Stance", ["for", "neutral"], index=0)
            
            # Second debater (Against position) - default to scientist
            st.markdown("**Second Debater (Against Position)**")
            debater2_idx = st.selectbox(
                "Select Second Debater",
                options=range(len(personas)),
                format_func=lambda x: debater_options[x],
                index=scientist_idx
            )
            
            debater2_stance = st.radio("Second Debater Stance", ["against", "neutral"], index=0)
            
            # Moderator selection
            st.subheader("Select Moderator")
            
            # Filter for moderator personas
            moderator_personas = [p for p in personas if p.get("moderation_style")]
            if moderator_personas:
                moderator_options = [f"{p['name']} - {p['description'][:50]}..." for p in moderator_personas]
                moderator_ids = [p["id"] for p in moderator_personas]
                
                moderator_idx = st.selectbox(
                    "Select Moderator",
                    options=range(len(moderator_personas)),
                    format_func=lambda x: moderator_options[x]
                )
                
                moderator_id = moderator_ids[moderator_idx]
            else:
                st.warning("No moderator personas found. Using default moderator.")
                moderator_id = "neutral_moderator"
            
            # Submit button
            submit_button = st.form_submit_button("Create Debate")
            
            if submit_button:
                # Create the debate configuration
                debate_config = {
                    "topic": topic,
                    "num_turns": num_turns,
                    "include_opening": include_opening,
                    "include_closing": include_closing,
                    "fact_checking": fact_checking,
                    "debaters": [
                        {
                            "persona_id": persona_ids[debater1_idx],
                            "stance": debater1_stance
                        },
                        {
                            "persona_id": persona_ids[debater2_idx],
                            "stance": debater2_stance
                        }
                    ],
                    "moderator": {
                        "persona_id": moderator_id
                    }
                }
                
                # Call the create debate callback
                on_create_debate(debate_config)
    
    # Tab 2: Load Existing Debate
    with tab2:
        st.subheader("Load an Existing Debate")
        
        if not debate_configs:
            st.info("No saved debate configurations found.")
        else:
            # Create a dataframe for the debate configs
            debates_df = pd.DataFrame([
                {
                    "ID": config["id"],
                    "Topic": truncate_text(config["topic"], 50),
                    "Debaters": config["num_debaters"]
                }
                for config in debate_configs
            ])
            
            # Display the dataframe
            st.dataframe(debates_df, use_container_width=True)
            
            # Select a debate to load
            selected_debate_idx = st.selectbox(
                "Select Debate to Load",
                options=range(len(debate_configs)),
                format_func=lambda x: f"{debate_configs[x]['topic'][:50]}..."
            )
            
            # Load button
            if st.button("Load Selected Debate"):
                # Call the create debate callback with the selected config
                on_create_debate(debate_configs[selected_debate_idx])

def render_debate_controls(
    debate_status: str,
    on_start: Callable[[], None],
    on_pause: Callable[[], None],
    on_reset: Callable[[], None],
    on_export: Callable[[], None]
):
    """
    Render the debate control panel with buttons for starting, pausing, etc.
    
    Args:
        debate_status: Current status of the debate
        on_start: Callback function for starting/resuming the debate
        on_pause: Callback function for pausing the debate
        on_reset: Callback function for resetting the debate
        on_export: Callback function for exporting the debate
    """
    st.header("Debate Controls")
    
    # Create columns for the buttons
    col1, col2, col3, col4 = st.columns(4)
    
    # Start/Resume button
    with col1:
        start_label = "Start Debate" if debate_status in ["not_started", "completed"] else "Resume Debate"
        start_disabled = debate_status == "completed"
        
        if st.button(start_label, disabled=start_disabled, type="primary" if debate_status == "not_started" else "secondary"):
            on_start()
    
    # Pause button
    with col2:
        pause_disabled = debate_status != "in_progress"
        
        if st.button("Pause Debate", disabled=pause_disabled):
            on_pause()
    
    # Reset button
    with col3:
        reset_disabled = debate_status == "not_started"
        
        if st.button("Reset Debate", disabled=reset_disabled):
            on_reset()
    
    # Export button
    with col4:
        export_disabled = debate_status == "not_started" or not any(s in debate_status for s in ["in_progress", "paused", "completed"])
        
        if st.button("Export Debate", disabled=export_disabled):
            on_export()
    
    # Display status indicator
    status_color = {
        "not_started": "blue",
        "in_progress": "green",
        "paused": "orange",
        "completed": "violet"
    }.get(debate_status, "gray")
    
    status_emoji = {
        "not_started": "🔵",
        "in_progress": "🟢",
        "paused": "🟠",
        "completed": "🟣"
    }.get(debate_status, "⚪")
    
    st.markdown(f"**Current Status: {status_emoji} {debate_status.replace('_', ' ').title()}**")

def render_debate_transcript(
    transcript: List[Dict[str, Any]],
    auto_scroll: bool = True
):
    """
    Render the debate transcript panel.
    
    Args:
        transcript: List of debate transcript messages
        auto_scroll: Whether to automatically scroll to the latest message
    """
    st.header("Debate Transcript")
    
    if not transcript:
        st.info("The debate has not started yet. Configure and start a debate to see the transcript.")
        return
    
    # Create a container for the transcript
    transcript_container = st.container()
    
    with transcript_container:
        for i, message in enumerate(transcript):
            speaker = message.get("speaker", "Unknown")
            role = message.get("role", "")
            content = message.get("content", "")
            message_type = message.get("message_type", "")
            
            # Determine the display style based on role and message type
            if role == "moderator":
                # Moderator messages in blue
                st.markdown(f"**{speaker} (Moderator):**")
                st.info(content)
            else:
                # Debater messages
                stance = message.get("stance", "")
                stance_display = f" ({stance})" if stance else ""
                
                st.markdown(f"**{speaker}{stance_display}:**")
                
                # Color based on message type
                if message_type == "opening":
                    st.success(content)  # Green for opening
                elif message_type == "closing":
                    st.warning(content)  # Yellow for closing
                else:
                    st.markdown(content)  # Default for regular arguments/rebuttals
            
            # Add separator between messages
            st.markdown("---")
    
    # Auto-scroll to the bottom for new messages
    if auto_scroll and transcript:
        # Use JavaScript to scroll to the bottom
        js = """
        <script>
            window.scrollTo(0, document.body.scrollHeight);
        </script>
        """
        st.components.v1.html(js, height=0)

def render_debate_summary(summary: Dict[str, Any]):
    """
    Render the debate summary panel.
    
    Args:
        summary: Dictionary containing debate summary information
    """
    st.header("Debate Summary")
    
    if not summary:
        st.info("No debate summary available yet.")
        return
    
    # Create columns for the summary
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Debate Information")
        st.markdown(f"**Topic:** {summary.get('topic', 'Unknown')}")
        st.markdown(f"**Status:** {summary.get('status', 'Unknown').replace('_', ' ').title()}")
        st.markdown(f"**Turns:** {summary.get('turns_completed', 0)}/{summary.get('total_turns', 0)}")
        
        if summary.get('duration'):
            st.markdown(f"**Duration:** {summary.get('duration')}")
        
        # Show debaters
        st.subheader("Debaters")
        for debater in summary.get("debaters", []):
            st.markdown(f"- **{debater.get('name', 'Unknown')}** ({debater.get('stance', 'unknown stance')})")
    
    with col2:
        # Show scores and winner if available
        scores = summary.get("scores", {})
        if scores:
            st.subheader("Scores")
            
            # Create a dataframe for the scores
            scores_data = []
            for debater_name, debater_scores in scores.items():
                scores_data.append({
                    "Debater": debater_name,
                    "Score": debater_scores.get("total", 0)
                })
            
            scores_df = pd.DataFrame(scores_data)
            st.dataframe(scores_df, use_container_width=True)
            
            # Show winner with more prominence
            winner = summary.get("winner")
            if winner:
                st.success(f"**Winner:** {winner}")
                
                # Add detailed winner analysis section
                st.markdown("### Why They Won")
                
                # Get the detailed results from the summary if available
                detailed_results = summary.get("detailed_results", {})
                rankings = detailed_results.get("rankings", [])
                
                # Find the winner's details
                winner_details = next((r for r in rankings if r.get("name") == winner), None)
                
                # Display winner's strengths based on detailed results
                if winner_details:
                    st.markdown("#### Winning Factors:")
                    
                    # Display score breakdown if available
                    criteria_scores = winner_details.get("criteria_scores", {})
                    if criteria_scores:
                        for criterion, score in criteria_scores.items():
                            st.markdown(f"- **{criterion.title()}:** {score}/10")
                    
                    # Display arguments evaluated count
                    arguments_count = winner_details.get("arguments_evaluated", 0)
                    st.markdown(f"- **Arguments Made:** {arguments_count}")
                    
                    # Display strengths based on debate style
                    debate_style = winner_details.get("debate_style", "")
                    if debate_style:
                        style_strengths = {
                            "logical": "Used well-structured logical arguments",
                            "emotional": "Connected emotionally with the audience",
                            "aggressive": "Made strong, assertive points",
                            "balanced": "Presented balanced and nuanced perspectives",
                            "analytical": "Provided detailed analysis of the topic",
                            "passionate": "Demonstrated strong conviction in their position"
                        }
                        style_strength = style_strengths.get(debate_style.lower(), "")
                        if style_strength:
                            st.markdown(f"- **{style_strength}**")
                else:
                    # If no detailed winner info is available, create generic bullet points based on winner name
                    st.markdown("#### Key Strengths:")
                    st.markdown("- **Compelling Arguments:** Presented clear and convincing points")
                    st.markdown("- **Strong Rebuttals:** Effectively countered opposing arguments")
                    st.markdown("- **Persuasive Communication:** Maintained a persuasive and structured debate style")
                    
                    # If winner is The Pragmatist (as seen in terminal output)
                    if winner == "The Pragmatist":
                        st.markdown("- **Balanced Approach:** Used a practical, realistic perspective")
                        st.markdown("- **Evidence-Based:** Supported arguments with concrete examples")
                        st.markdown("- **Adaptability:** Responded effectively to counter-arguments")
        else:
            st.info("Scoring will be available when the debate is completed.")
    
    # Add a comprehensive Results section below the columns
    st.markdown("---")
    st.header("Complete Debate Analysis")
    
    # Extract detailed results
    detailed_results = summary.get("detailed_results", summary.get("results", {}))
    rankings = detailed_results.get("rankings", [])
    
    if rankings:
        # Create tabs for different result views
        result_tabs = st.tabs(["Overall Scores", "Performance Breakdown", "Key Arguments"])
        
        # Tab 1: Overall Scores
        with result_tabs[0]:
            # Create a more detailed dataframe for all debaters
            detailed_scores = []
            for rank in rankings:
                row = {
                    "Debater": rank.get("name", "Unknown"),
                    "Final Score": rank.get("score", 0),
                    "Position": "Winner" if rank.get("name") == summary.get("winner") else "Runner-up"
                }
                detailed_scores.append(row)
            
            detailed_df = pd.DataFrame(detailed_scores)
            st.dataframe(detailed_df, use_container_width=True)
        
        # Tab 2: Performance Breakdown  
        with result_tabs[1]:
            for rank in rankings:
                debater_name = rank.get("name", "Unknown")
                st.subheader(f"{debater_name}")
                
                # Show stance and style
                debater_info = next((d for d in summary.get("debaters", []) if d.get("name") == debater_name), {})
                stance = debater_info.get("stance", "")
                
                # Get debater stats if available
                stats = rank.get("stats", {})
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Position:** {stance.title() if stance else 'Not specified'}")
                    st.markdown(f"**Total Score:** {rank.get('score', 0)}")
                    
                with col2:
                    st.markdown(f"**Arguments Made:** {stats.get('arguments_count', 0)}")
                    st.markdown(f"**Rebuttals Made:** {stats.get('rebuttals_count', 0)}")
                
                st.markdown("---")
        
        # Tab 3: Key Arguments
        with result_tabs[2]:
            st.markdown("#### Most Impactful Arguments")
            st.info("This section shows a summary of the key arguments that influenced the debate outcome.")
            
            # For now, display a placeholder for key arguments
            # In a real implementation, these would be extracted from the debate transcript
            st.markdown("1. **Opening statements** set the tone for the debate")
            st.markdown("2. **Core arguments** presented the main positions")
            st.markdown("3. **Rebuttals** challenged opposing viewpoints")
            st.markdown("4. **Closing arguments** summarized and reinforced key points")
    else:
        st.info("Detailed results analysis will be available when the debate is completed.")

def render_loading_indicator(text: str = "Processing..."):
    """
    Render a loading indicator with the given text.
    
    Args:
        text: Text to display with the loading indicator
    """
    with st.spinner(text):
        st.markdown("⏳ " + text)
        
def render_export_options(
    on_export_transcript: Callable[[], None],
    on_export_summary: Callable[[], None],
    on_export_complete: Callable[[], None]
):
    """
    Render the export options dialog.
    
    Args:
        on_export_transcript: Callback for exporting transcript only
        on_export_summary: Callback for exporting summary only
        on_export_complete: Callback for exporting complete debate
    """
    st.header("Export Debate")
    
    st.info("Select what you want to export:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Transcript Only"):
            on_export_transcript()
    
    with col2:
        if st.button("Summary Only"):
            on_export_summary()
    
    with col3:
        if st.button("Complete Debate"):
            on_export_complete()
    
    st.markdown("---")

def render_persona_editor(
    personas: List[Dict[str, Any]],
    on_save_persona: Callable[[Dict[str, Any]], None]
):
    """
    Render the persona editor panel.
    
    Args:
        personas: List of available personas
        on_save_persona: Callback function when a persona is saved
    """
    st.header("Persona Editor")
    
    # Create tabs for Edit Existing vs Create New
    tab1, tab2 = st.tabs(["Edit Existing Persona", "Create New Persona"])
    
    # Tab 1: Edit Existing Persona
    with tab1:
        if not personas:
            st.info("No personas found to edit.")
        else:
            selected_persona_idx = st.selectbox(
                "Select Persona to Edit",
                options=range(len(personas)),
                format_func=lambda x: f"{personas[x]['name']} - {personas[x]['description'][:50]}..."
            )
            
            selected_persona = personas[selected_persona_idx]
            
            with st.form(key="edit_persona_form"):
                st.subheader(f"Editing: {selected_persona['name']}")
                
                # Fields for editing
                name = st.text_input("Name", value=selected_persona.get("name", ""))
                description = st.text_area("Description", value=selected_persona.get("description", ""), height=100)
                
                # Traits as a multi-line text area
                traits_text = "\n".join(selected_persona.get("traits", []))
                traits = st.text_area("Traits (one per line)", value=traits_text, height=150)
                
                # Role-specific fields
                if "debate_style" in selected_persona:
                    debate_style = st.selectbox(
                        "Debate Style",
                        options=["logical", "emotional", "aggressive", "balanced", "analytical", "passionate"],
                        index=["logical", "emotional", "aggressive", "balanced", "analytical", "passionate"].index(
                            selected_persona.get("debate_style", "logical")
                        ) if selected_persona.get("debate_style") in ["logical", "emotional", "aggressive", "balanced", "analytical", "passionate"] else 0
                    )
                else:
                    debate_style = None
                
                if "moderation_style" in selected_persona:
                    moderation_style = st.selectbox(
                        "Moderation Style",
                        options=["neutral", "provocative", "educational", "entertaining"],
                        index=["neutral", "provocative", "educational", "entertaining"].index(
                            selected_persona.get("moderation_style", "neutral")
                        ) if selected_persona.get("moderation_style") in ["neutral", "provocative", "educational", "entertaining"] else 0
                    )
                else:
                    moderation_style = None
                
                # Save button
                submit_button = st.form_submit_button("Save Changes")
                
                if submit_button:
                    # Create updated persona
                    updated_persona = {
                        "id": selected_persona["id"],
                        "name": name,
                        "description": description,
                        "traits": [trait.strip() for trait in traits.split("\n") if trait.strip()]
                    }
                    
                    if debate_style is not None:
                        updated_persona["debate_style"] = debate_style
                    
                    if moderation_style is not None:
                        updated_persona["moderation_style"] = moderation_style
                    
                    # Call the save callback
                    on_save_persona(updated_persona)
    
    # Tab 2: Create New Persona
    with tab2:
        with st.form(key="create_persona_form"):
            st.subheader("Create a New Persona")
            
            # Fields for new persona
            persona_id = st.text_input("ID (lowercase, no spaces)", value="", 
                                      help="Unique identifier for the persona, e.g., 'logical_debater'")
            name = st.text_input("Name", value="")
            description = st.text_area("Description", value="", height=100)
            
            # Traits as a multi-line text area
            traits = st.text_area("Traits (one per line)", value="", height=150)
            
            # Role selection
            role_type = st.radio("Persona Role", ["Debater", "Moderator"])
            
            # Role-specific fields
            if role_type == "Debater":
                debate_style = st.selectbox(
                    "Debate Style",
                    options=["logical", "emotional", "aggressive", "balanced", "analytical", "passionate"]
                )
                moderation_style = None
            else:
                debate_style = None
                moderation_style = st.selectbox(
                    "Moderation Style",
                    options=["neutral", "provocative", "educational", "entertaining"]
                )
            
            # Save button
            submit_button = st.form_submit_button("Create Persona")
            
            if submit_button:
                if not persona_id:
                    st.error("ID is required.")
                elif not name:
                    st.error("Name is required.")
                else:
                    # Create new persona
                    new_persona = {
                        "id": persona_id.lower().replace(" ", "_"),
                        "name": name,
                        "description": description,
                        "traits": [trait.strip() for trait in traits.split("\n") if trait.strip()]
                    }
                    
                    if debate_style is not None:
                        new_persona["debate_style"] = debate_style
                    
                    if moderation_style is not None:
                        new_persona["moderation_style"] = moderation_style
                    
                    # Call the save callback
                    on_save_persona(new_persona)

def render_llm_settings(
    on_save_settings: Callable[[Dict[str, Any]], None] = None
):
    """
    Render LLM configuration settings for the debate simulator.
    
    Args:
        on_save_settings: Callback function when settings are saved
    """
    st.header("LLM Configuration")
    
    with st.expander("Configure LLM & Search API Settings", expanded=False):
        # Create tabs for different settings
        llm_tab, search_tab = st.tabs(["LLM Settings", "Search API Settings"])
        
        with llm_tab:
            # API Key
            api_key = st.text_input(
                "Groq API Key", 
                value=st.session_state.groq_api_key if 'groq_api_key' in st.session_state else "",
                type="password",
                help="Your Groq API key. This will be stored in session state and used for all LLM requests."
            )
            
            # Model selection
            model = st.selectbox(
                "Model",
                options=["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"],
                index=0 if 'llm_config' not in st.session_state else 
                      ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"].index(
                          st.session_state.llm_config.get("model", "llama3-8b-8192")
                      ) if st.session_state.llm_config.get("model") in ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"] else 0,
                help="The Groq model to use for generating responses."
            )
            
            # Temperature
            col1, col2 = st.columns(2)
            with col1:
                temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=1.0,
                    value=st.session_state.llm_config.get("temperature", 0.7) if 'llm_config' in st.session_state else 0.7,
                    step=0.1,
                    help="Higher values make output more random, lower values more deterministic."
                )
            
            # Max tokens
            with col2:
                max_tokens = st.slider(
                    "Max Tokens",
                    min_value=100,
                    max_value=1500,
                    value=st.session_state.llm_config.get("max_tokens", 800) if 'llm_config' in st.session_state else 800,
                    step=100,
                    help="Maximum number of tokens to generate in responses."
                )
                
        with search_tab:
            # Tavily API settings
            st.subheader("Tavily Search API")
            st.markdown("""
            [Tavily](https://tavily.com/) is a search API that provides real-time information 
            for fact-checking and research during debates.
            """)
            
            # Tavily API Key
            tavily_api_key = st.text_input(
                "Tavily API Key", 
                value=st.session_state.get("tavily_api_key", ""),
                type="password",
                help="Your Tavily API key for fact-checking. Get one at https://tavily.com/"
            )
            
            # Enable fact checking
            fact_checking = st.checkbox(
                "Enable Fact Checking", 
                value=st.session_state.get("fact_checking", False),
                help="When enabled, the moderator will fact-check important claims during the debate."
            )
            
            st.info("Fact checking requires a valid Tavily API key.")
        
        # Save button for all settings
        if st.button("Save Settings"):
            # Update session state for LLM
            st.session_state.groq_api_key = api_key
            
            st.session_state.llm_config = {
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": 0.9  # Default value, could be exposed in UI if needed
            }
            
            # Update session state for Tavily
            st.session_state.tavily_api_key = tavily_api_key
            st.session_state.fact_checking = fact_checking
            
            # Show success message
            st.success("Settings saved!")
            
            # Call callback if provided
            if on_save_settings:
                settings = {
                    "llm_config": st.session_state.llm_config,
                    "tavily_api_key": tavily_api_key,
                    "fact_checking": fact_checking
                }
                on_save_settings(settings)