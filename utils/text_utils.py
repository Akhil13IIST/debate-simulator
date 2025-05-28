"""
Text Utilities Module

This module provides utility functions for text processing and formatting
used throughout the debate simulator.
"""

import re
import json
import html
from typing import Dict, List, Any, Optional, Union

def truncate_text(text: str, max_length: int = 100, add_ellipsis: bool = True) -> str:
    """
    Truncate text to the specified maximum length.
    
    Args:
        text: The text to truncate
        max_length: Maximum length of the truncated text
        add_ellipsis: Whether to add ellipsis (...) at the end of truncated text
        
    Returns:
        Truncated text
    """
    if text is None:
        return ""
    
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length].rstrip()
    if add_ellipsis:
        truncated += "..."
    
    return truncated

def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace, normalizing line breaks, etc.
    
    Args:
        text: The text to clean
        
    Returns:
        Cleaned text
    """
    if text is None:
        return ""
    
    # Replace multiple whitespace with a single space
    cleaned = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    cleaned = cleaned.strip()
    # Normalize line breaks
    cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
    
    return cleaned

def format_debate_transcript(transcript: List[Dict[str, Any]], format_type: str = "text") -> str:
    """
    Format a debate transcript for display or export.
    
    Args:
        transcript: List of debate transcript messages
        format_type: Format type ("text", "html", "markdown")
        
    Returns:
        Formatted transcript
    """
    if not transcript:
        return "No transcript available."
    
    formatted = []
    
    if format_type == "html":
        formatted.append("<div class='debate-transcript'>")
        
        for message in transcript:
            speaker = html.escape(message.get("speaker", "Unknown"))
            role = message.get("role", "")
            content = html.escape(message.get("content", ""))
            message_type = message.get("message_type", "")
            
            role_class = f"role-{role}" if role else ""
            msg_class = f"message-{message_type}" if message_type else ""
            
            formatted.append(f"<div class='message {role_class} {msg_class}'>")
            
            if role == "moderator":
                formatted.append(f"<div class='speaker moderator'>{speaker} (Moderator):</div>")
            else:
                stance = message.get("stance", "")
                stance_display = f" ({stance})" if stance else ""
                formatted.append(f"<div class='speaker debater'>{speaker}{stance_display}:</div>")
            
            formatted.append(f"<div class='content'>{content}</div>")
            formatted.append("</div>")
        
        formatted.append("</div>")
        
        return "\n".join(formatted)
    
    elif format_type == "markdown":
        for message in transcript:
            speaker = message.get("speaker", "Unknown")
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "moderator":
                formatted.append(f"**{speaker} (Moderator):**")
            else:
                stance = message.get("stance", "")
                stance_display = f" ({stance})" if stance else ""
                formatted.append(f"**{speaker}{stance_display}:**")
            
            formatted.append(content)
            formatted.append("---")
        
        return "\n\n".join(formatted)
    
    else:  # default text format
        for message in transcript:
            speaker = message.get("speaker", "Unknown")
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "moderator":
                formatted.append(f"{speaker} (Moderator):")
            else:
                stance = message.get("stance", "")
                stance_display = f" ({stance})" if stance else ""
                formatted.append(f"{speaker}{stance_display}:")
            
            formatted.append(content)
            formatted.append("-" * 40)
        
        return "\n\n".join(formatted)

def format_debate_summary(summary: Dict[str, Any], format_type: str = "text") -> str:
    """
    Format a debate summary for display or export.
    
    Args:
        summary: Dictionary containing debate summary information
        format_type: Format type ("text", "html", "markdown")
        
    Returns:
        Formatted summary
    """
    if not summary:
        return "No summary available."
    
    topic = summary.get("topic", "Unknown topic")
    status = summary.get("status", "unknown").replace("_", " ").title()
    turns_completed = summary.get("turns_completed", 0)
    total_turns = summary.get("total_turns", 0)
    duration = summary.get("duration", "Unknown")
    debaters = summary.get("debaters", [])
    scores = summary.get("scores", {})
    winner = summary.get("winner", "")
    
    if format_type == "html":
        formatted = [
            "<div class='debate-summary'>",
            f"<h2>Debate Summary: {html.escape(topic)}</h2>",
            f"<p><strong>Status:</strong> {html.escape(status)}</p>",
            f"<p><strong>Turns:</strong> {turns_completed}/{total_turns}</p>"
        ]
        
        if duration:
            formatted.append(f"<p><strong>Duration:</strong> {html.escape(str(duration))}</p>")
        
        formatted.append("<h3>Debaters</h3>")
        formatted.append("<ul>")
        for debater in debaters:
            name = html.escape(debater.get("name", "Unknown"))
            stance = html.escape(debater.get("stance", "unknown stance"))
            formatted.append(f"<li>{name} ({stance})</li>")
        formatted.append("</ul>")
        
        if scores:
            formatted.append("<h3>Scores</h3>")
            formatted.append("<table>")
            formatted.append("<tr><th>Debater</th><th>Score</th></tr>")
            
            for debater_name, debater_scores in scores.items():
                score = debater_scores.get("total", 0)
                formatted.append(f"<tr><td>{html.escape(debater_name)}</td><td>{score}</td></tr>")
            
            formatted.append("</table>")
            
            if winner:
                formatted.append(f"<p><strong>Winner:</strong> {html.escape(winner)}</p>")
        
        formatted.append("</div>")
        
        return "\n".join(formatted)
    
    elif format_type == "markdown":
        formatted = [
            f"# Debate Summary: {topic}",
            f"**Status:** {status}",
            f"**Turns:** {turns_completed}/{total_turns}"
        ]
        
        if duration:
            formatted.append(f"**Duration:** {duration}")
        
        formatted.append("\n## Debaters")
        for debater in debaters:
            name = debater.get("name", "Unknown")
            stance = debater.get("stance", "unknown stance")
            formatted.append(f"- **{name}** ({stance})")
        
        if scores:
            formatted.append("\n## Scores")
            formatted.append("| Debater | Score |")
            formatted.append("| ------- | ----- |")
            
            for debater_name, debater_scores in scores.items():
                score = debater_scores.get("total", 0)
                formatted.append(f"| {debater_name} | {score} |")
            
            if winner:
                formatted.append(f"\n**Winner:** {winner}")
        
        return "\n\n".join(formatted)
    
    else:  # default text format
        formatted = [
            f"Debate Summary: {topic}",
            f"Status: {status}",
            f"Turns: {turns_completed}/{total_turns}"
        ]
        
        if duration:
            formatted.append(f"Duration: {duration}")
        
        formatted.append("\nDebaters:")
        for debater in debaters:
            name = debater.get("name", "Unknown")
            stance = debater.get("stance", "unknown stance")
            formatted.append(f"- {name} ({stance})")
        
        if scores:
            formatted.append("\nScores:")
            for debater_name, debater_scores in scores.items():
                score = debater_scores.get("total", 0)
                formatted.append(f"{debater_name}: {score}")
            
            if winner:
                formatted.append(f"\nWinner: {winner}")
        
        return "\n".join(formatted)

def parse_json_safely(json_str: str) -> Dict[str, Any]:
    """
    Parse a JSON string safely, handling common errors.
    
    Args:
        json_str: JSON string to parse
        
    Returns:
        Parsed JSON object or empty dict if parsing fails
    """
    try:
        # Handle case when response starts with explanatory text
        if not json_str.strip().startswith("{"):
            # Look for the first opening brace which might indicate the start of JSON
            json_start = json_str.find("{")
            if json_start != -1:
                json_str = json_str[json_start:]
        
        # Handle case when response ends with explanatory text
        last_brace = json_str.rfind("}")
        if last_brace != -1 and last_brace < len(json_str) - 1:
            json_str = json_str[:last_brace+1]
        
        # Remove any markdown formatting that might be present (e.g., from LLM outputs)
        if json_str.startswith("```json"):
            lines = json_str.strip().split("\n")
            json_str = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        elif json_str.startswith("```"):
            lines = json_str.strip().split("\n")
            json_str = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        
        # Try to load the JSON
        return json.loads(json_str)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print(f"Problematic JSON string (first 100 chars): {json_str[:100]}...")
        
        # Make a second attempt with a more aggressive approach
        try:
            # Try to extract just the JSON object using regex
            import re
            json_pattern = r'({[\s\S]*})'  # Match everything between outermost braces
            matches = re.search(json_pattern, json_str)
            
            if matches:
                potential_json = matches.group(1)
                return json.loads(potential_json)
        except Exception as inner_e:
            print(f"Second attempt at JSON parsing failed: {inner_e}")
        
        return {}