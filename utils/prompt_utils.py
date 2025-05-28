"""
Prompt Utilities Module

This module provides utilities for working with prompt templates.
"""

import os
import re
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class PromptManager:
    """
    Class for managing prompt templates.
    
    This class provides functionality for loading prompt templates
    and formatting them with context variables.
    """
    
    def __init__(self, templates_dir: str = None):
        """
        Initialize the prompt manager.
        
        Args:
            templates_dir: Directory containing prompt templates
        """
        self.templates_dir = templates_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
            "prompt_templates"
        )
        self.templates = {}
        self.load_templates()
        
        logger.info(f"Initialized PromptManager with templates from: {self.templates_dir}")
    
    def load_templates(self) -> None:
        """
        Load all templates from the templates directory.
        """
        if not os.path.exists(self.templates_dir):
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            return
        
        for filename in os.listdir(self.templates_dir):
            if filename.endswith(".txt"):
                template_name = os.path.splitext(filename)[0]
                file_path = os.path.join(self.templates_dir, filename)
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        self.templates[template_name] = f.read()
                    
                    logger.debug(f"Loaded template: {template_name}")
                except Exception as e:
                    logger.error(f"Error loading template {template_name}: {e}")
        
        logger.info(f"Loaded {len(self.templates)} templates")
    
    def get_template(self, template_name: str) -> Optional[str]:
        """
        Get a template by name.
        
        Args:
            template_name: Name of the template to get
            
        Returns:
            Template string or None if not found
        """
        if template_name not in self.templates:
            # Try to load the template if it wasn't loaded initially
            try:
                file_path = os.path.join(self.templates_dir, f"{template_name}.txt")
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        self.templates[template_name] = f.read()
                        logger.debug(f"Loaded template on demand: {template_name}")
                        return self.templates[template_name]
            except Exception as e:
                logger.error(f"Error loading template {template_name} on demand: {e}")
                
            logger.warning(f"Template not found: {template_name}")
            return None
        
        return self.templates[template_name]
    
    def format_template(self, template_name: str, **kwargs) -> str:
        """
        Format a template with the given context variables.
        
        Args:
            template_name: Name of the template to format
            **kwargs: Context variables for the template
            
        Returns:
            Formatted template string
        """
        template = self.get_template(template_name)
        
        if not template:
            # Return a basic fallback template if the requested template is not found
            logger.warning(f"Using fallback template for: {template_name}")
            return f"This is a placeholder for the {template_name} template. " + \
                   f"Context: {', '.join(f'{k}={v}' for k, v in kwargs.items() if not isinstance(v, (dict, list)))}"
        
        # Pre-process the template to ensure all Python expressions are properly handled
        # This prevents the unhashable type error for dictionaries used as keys
        try:
            # First, make sure all variables are properly formatted
            result = template
            
            # Handle variables with braces like {variable}
            for var_match in re.finditer(r'\{([^{}]+)\}', template):
                var_expr = var_match.group(1)
                
                # Skip if it's already a Python expression
                if any(op in var_expr for op in ["==", "!=", "<", ">", "and", "or", "if", "else", "+", "-", "*", "/"]):
                    continue
                
                # Handle dot notation and dictionary access safely
                if "." in var_expr or "[" in var_expr:
                    parts = re.split(r'[\.\[]', var_expr.replace("]", ""))
                    base_var = parts[0]
                    
                    # Check if the base variable exists
                    if base_var not in kwargs:
                        # Leave the variable as is if the base doesn't exist
                        continue
                    
                    # Build a safe access chain using .get() for dictionaries
                    safe_expr = base_var
                    value = kwargs[base_var]
                    
                    for i, part in enumerate(parts[1:], 1):
                        if isinstance(value, dict):
                            # For dictionaries, use .get() with a default
                            safe_expr = f"{safe_expr}.get('{part}', '')"
                        elif isinstance(value, list) and part.isdigit():
                            # For lists, use an index with bounds checking
                            index = int(part)
                            if 0 <= index < len(value):
                                safe_expr = f"{safe_expr}[{part}]"
                                value = value[index]
                            else:
                                safe_expr = "''"  # Out of bounds, return empty string
                                break
                        else:
                            # Can't access further - set to empty string
                            safe_expr = "''"
                            break
                        
                        # Update value for next iteration if possible
                        if isinstance(value, dict):
                            value = value.get(part, {})
                    
                    # Replace the original expression with the safe one
                    result = result.replace(f"{{{var_expr}}}", f"{{{safe_expr}}}")
            
            # Use Python's string formatting to handle the template
            # This ensures proper evaluation of expressions
            formatted = result.format(**kwargs)
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting template {template_name}: {e}")
            # Provide a simple fallback with no template processing
            return f"Error processing template {template_name}: {str(e)}"
    
    def add_template(self, template_name: str, template_content: str) -> None:
        """
        Add a new template.
        
        Args:
            template_name: Name of the template
            template_content: Content of the template
        """
        self.templates[template_name] = template_content
        
        # Save the template to disk
        file_path = os.path.join(self.templates_dir, f"{template_name}.txt")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(template_content)
        
        logger.info(f"Added new template: {template_name}")

# Singleton instance
_prompt_manager = None

def get_prompt_manager() -> PromptManager:
    """
    Get the singleton PromptManager instance.
    
    Returns:
        PromptManager instance
    """
    global _prompt_manager
    
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    
    return _prompt_manager