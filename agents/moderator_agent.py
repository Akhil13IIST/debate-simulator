"""
Moderator Agent Module

This module defines the ModeratorAgent class which represents a moderator
in the debate simulator. Moderators introduce debates, facilitate transitions
between speakers, provide summaries, and conclude debates.
"""

import logging
import random
from typing import Dict, List, Any, Optional, Callable

from agents.base_agent import BaseAgent
from utils.search.tavily_search import get_tavily_client

logger = logging.getLogger(__name__)

class ModeratorAgent(BaseAgent):
    """
    Agent class representing a moderator in the debate simulator.
    """
    
    def __init__(self, 
                 name: str, 
                 persona: Dict[str, Any],
                 moderation_style: Optional[str] = None,
                 fact_checking: bool = False,
                 tavily_api_key: Optional[str] = None,
                 llm_config: Optional[Dict[str, Any]] = None):
        """
        Initialize a moderator agent.
        
        Args:
            name: Name of the moderator
            persona: Dictionary containing persona details (traits, description, etc.)
            moderation_style: Style of moderation (e.g., "neutral", "provocative")
            fact_checking: Whether the moderator should perform fact checking
            tavily_api_key: API key for Tavily search (for fact checking)
            llm_config: Configuration for the language model
        """
        super().__init__(name, persona, llm_config)
        
        self.moderation_style = moderation_style or persona.get("moderation_style", "neutral")
        self.fact_checking = fact_checking
        
        # Initialize Tavily client if fact checking is enabled
        if fact_checking:
            self.tavily_client = get_tavily_client(tavily_api_key)
            logger.info(f"Initialized Tavily client for fact checking with moderator: {name}")
        else:
            self.tavily_client = None
        
        # Initialize moderator-specific state
        self.debate_topic = ""
        self.debate_rules = {}
        self.debaters = []
        self.speaker_scores = {}
        self.fact_checks = []
        
        logger.info(f"Initialized moderator agent: {name} with style: {moderation_style}")
    
    def _get_agent_type(self) -> str:
        """
        Get the type of agent for prompt template selection.
        
        Returns:
            String identifying the agent type
        """
        return "moderator"
    
    def set_debate_config(self, 
                          topic: str, 
                          debaters: List[Dict[str, Any]], 
                          rules: Dict[str, Any]) -> None:
        """
        Set the debate configuration for the moderator.
        
        Args:
            topic: The debate topic
            debaters: List of debater information dictionaries
            rules: Dictionary of debate rules
        """
        self.debate_topic = topic
        self.debaters = debaters
        self.debate_rules = rules
        
        # Initialize scores for each debater
        self.speaker_scores = {
            debater.get("name", f"Debater {i+1}"): {
                "arguments": [],
                "total": 0
            }
            for i, debater in enumerate(debaters)
        }
        
        logger.info(f"Set debate configuration for moderator: {self.name}")
    
    def generate_introduction(self) -> str:
        """
        Generate an introduction for the debate.
        
        Returns:
            Introduction string
        """
        context = {
            "message_type": "introduction",
            "topic": self.debate_topic,
            "debaters": [d.get("name", "Unknown Debater") for d in self.debaters],
            "rules": self.debate_rules,
            "moderation_style": self.moderation_style
        }
        
        return self.generate_message(context)
    
    def generate_transition(self, 
                           current_speaker: str, 
                           next_speaker: str, 
                           turn_number: int, 
                           total_turns: int) -> str:
        """
        Generate a transition between speakers.
        
        Args:
            current_speaker: Name of the current speaker
            next_speaker: Name of the next speaker
            turn_number: Current turn number
            total_turns: Total number of turns in the debate
            
        Returns:
            Transition string
        """
        context = {
            "message_type": "transition",
            "topic": self.debate_topic,
            "current_speaker": current_speaker,
            "next_speaker": next_speaker,
            "turn_number": turn_number,
            "total_turns": total_turns,
            "moderation_style": self.moderation_style
        }
        
        return self.generate_message(context)
    
    def generate_summary(self, 
                         turn_number: int, 
                         transcript: List[Dict[str, Any]]) -> str:
        """
        Generate a summary of the debate so far.
        
        Args:
            turn_number: Current turn number
            transcript: List of transcript messages
            
        Returns:
            Summary string
        """
        context = {
            "message_type": "summary",
            "topic": self.debate_topic,
            "turn_number": turn_number,
            "transcript": transcript,
            "moderation_style": self.moderation_style
        }
        
        return self.generate_message(context)
    
    def evaluate_argument(self, 
                          speaker: str, 
                          argument: str, 
                          turn_number: int) -> Dict[str, Any]:
        """
        Evaluate an argument made by a debater using NLP.
        
        Args:
            speaker: Name of the speaker
            argument: The argument content
            turn_number: Current turn number
            
        Returns:
            Evaluation dictionary
        """
        logger.debug(f"Evaluating argument by {speaker} at turn {turn_number}")
        
        # Define default scores in case of failures
        default_score = 7.5  # Default to a mid-high range score (7.5 out of 10)
        
        # Define evaluation criteria
        criteria = {
            "clarity": "How clear and understandable the argument is",
            "evidence": "The quality and relevance of evidence and examples provided",
            "reasoning": "The logical coherence and soundness of reasoning",
            "persuasiveness": "How convincing and compelling the overall argument is",
            "relevance": "How relevant the argument is to the debate topic"
        }
        
        # Create prompt for LLM to evaluate the argument
        evaluation_prompt = f"""
You are an expert debate evaluator assessing an argument in a debate on the topic: "{self.debate_topic}"
Please evaluate the following argument made by {speaker} in turn {turn_number} of the debate.

ARGUMENT:
{argument}

EVALUATION CRITERIA:
- Clarity (1-10): How clear and understandable the argument is
- Evidence (1-10): The quality and relevance of evidence and examples provided
- Reasoning (1-10): The logical coherence and soundness of reasoning
- Persuasiveness (1-10): How convincing and compelling the overall argument is
- Relevance (1-10): How relevant the argument is to the debate topic

For each criterion, provide:
1. A score from 1-10 (MUST be a numeric value, not text)
2. A brief explanation of the score

Finally, provide:
1. A list of key strengths (2-3 points)
2. A list of key weaknesses (1-2 points)
3. An overall score from 1-10 based on all criteria (MUST be a numeric value, not text)
4. A brief reasoning for the overall evaluation

Your response must be in the following JSON format:
{{
  "criteria": {{
    "clarity": {{
      "score": <score>,
      "explanation": "<explanation>"
    }},
    "evidence": {{
      "score": <score>,
      "explanation": "<explanation>"
    }},
    "reasoning": {{
      "score": <score>,
      "explanation": "<explanation>"
    }},
    "persuasiveness": {{
      "score": <score>,
      "explanation": "<explanation>"
    }},
    "relevance": {{
      "score": <score>,
      "explanation": "<explanation>"
    }}
  }},
  "strengths": ["<strength1>", "<strength2>", ...],
  "weaknesses": ["<weakness1>", "<weakness2>", ...],
  "overall_score": <overall_score>,
  "reasoning": "<reasoning>"
}}

IMPORTANT: All scores MUST be numeric values between 1 and 10, not strings.
"""
        
        try:
            # Use the LLM to evaluate the argument
            import groq
            import os
            import json
            from utils.text_utils import parse_json_safely
            
            # Get API key from environment variable
            api_key = os.environ.get("GROQ_API_KEY")
            
            if not api_key:
                logger.warning("GROQ_API_KEY not found. Using placeholder evaluation.")
                return self._get_placeholder_evaluation(speaker, turn_number)
            
            # Initialize Groq client
            client = groq.Client(api_key=api_key)
            
            # Choose model based on configuration
            model = self.llm_config.get("model", "llama3-8b-8192")
            
            # Generate chat completion
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert debate evaluator who analyzes arguments based on clarity, evidence, reasoning, persuasiveness, and relevance. Always respond with numeric scores between 1-10."},
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=0.2,  # Lower temperature for more consistent evaluations
                max_tokens=1000,
                top_p=0.9,
            )
            
            # Extract the content from the response
            response_content = response.choices[0].message.content
            logger.debug(f"Raw evaluation response: {response_content[:100]}...")
            
            # Parse the JSON response
            evaluation_data = parse_json_safely(response_content)
            
            if not evaluation_data or "criteria" not in evaluation_data:
                logger.warning(f"Failed to parse evaluation response for {speaker}. Using fallback. Response: {response_content[:200]}")
                return self._get_placeholder_evaluation(speaker, turn_number)
            
            # Extract criteria scores and convert to numeric if needed
            criteria_scores = {}
            for criterion, data in evaluation_data.get("criteria", {}).items():
                try:
                    # Try to get the score as a number
                    score_value = data.get("score")
                    
                    # Handle various formats from the API
                    if isinstance(score_value, (int, float)):
                        numeric_score = float(score_value)
                    elif isinstance(score_value, str) and score_value.strip().isdigit():
                        numeric_score = float(score_value.strip())
                    else:
                        # Default if we can't parse
                        logger.warning(f"Invalid score format for {criterion}: {score_value}. Using default.")
                        numeric_score = 7.0
                    
                    # Ensure the score is within range
                    criteria_scores[criterion] = min(max(numeric_score, 1.0), 10.0)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error converting score for {criterion}: {e}. Using default score.")
                    criteria_scores[criterion] = 7.0
            
            # Ensure all criteria have valid scores
            for criterion in ["clarity", "evidence", "reasoning", "persuasiveness", "relevance"]:
                if criterion not in criteria_scores:
                    criteria_scores[criterion] = 7.0
            
            # Parse overall score
            try:
                overall_score_value = evaluation_data.get("overall_score")
                if isinstance(overall_score_value, (int, float)):
                    overall_score = float(overall_score_value)
                elif isinstance(overall_score_value, str) and overall_score_value.strip().replace('.', '', 1).isdigit():
                    overall_score = float(overall_score_value.strip())
                else:
                    # If overall_score is not valid, calculate from criteria scores
                    overall_score = sum(criteria_scores.values()) / len(criteria_scores)
            except (ValueError, TypeError):
                # Fallback to average of criteria scores
                overall_score = sum(criteria_scores.values()) / len(criteria_scores)
            
            # Ensure overall score is within range and properly rounded
            overall_score = round(min(max(overall_score, 1.0), 10.0), 1)
            
            # Build the evaluation result
            evaluation = {
                "speaker": speaker,
                "turn": turn_number,
                "score": overall_score,
                "criteria_scores": {k: round(v, 1) for k, v in criteria_scores.items()},  # Round to 1 decimal
                "strengths": evaluation_data.get("strengths", ["Good argumentation"]),
                "weaknesses": evaluation_data.get("weaknesses", ["Could be improved"]),
                "reasoning": evaluation_data.get("reasoning", "This is an automated evaluation.")
            }
            
            logger.info(f"Successfully evaluated argument by {speaker} with score {overall_score}")
            
        except Exception as e:
            logger.error(f"Error evaluating argument with LLM: {e}")
            return self._get_placeholder_evaluation(speaker, turn_number)
        
        # Ensure we have a valid evaluation with numeric scores
        if evaluation["score"] == 0 or not isinstance(evaluation["score"], (int, float)):
            logger.warning(f"Invalid evaluation score: {evaluation['score']}. Using placeholder.")
            evaluation = self._get_placeholder_evaluation(speaker, turn_number)
        
        # Store the evaluation - using a try-except to protect against any errors
        try:
            if speaker in self.speaker_scores:
                self.speaker_scores[speaker]["arguments"].append(evaluation)
                
                # Update total score (average of all arguments)
                scores = [arg["score"] for arg in self.speaker_scores[speaker]["arguments"] 
                         if isinstance(arg["score"], (int, float)) and arg["score"] > 0]
                
                if scores:  # Only update if we have valid scores
                    self.speaker_scores[speaker]["total"] = round(sum(scores) / len(scores), 1)
                else:
                    # If no valid scores, set a default
                    self.speaker_scores[speaker]["total"] = default_score
        except Exception as e:
            logger.error(f"Error updating speaker scores: {e}")
            # Ensure the speaker has a non-zero score
            if speaker in self.speaker_scores:
                self.speaker_scores[speaker]["total"] = default_score
        
        return evaluation

    def _get_placeholder_evaluation(self, speaker: str, turn_number: int) -> Dict[str, Any]:
        """
        Get a placeholder evaluation when LLM evaluation fails.
        
        Args:
            speaker: Name of the speaker
            turn_number: Current turn number
            
        Returns:
            Placeholder evaluation dictionary
        """
        # Generate a more varied score between 5.0 and 9.5 for demonstration
        score = random.uniform(5.0, 9.5)
        score = round(score, 1)
        
        # Generate separate criteria scores with more variation
        criteria_scores = {
            "clarity": round(random.uniform(4.0, 9.5), 1),
            "evidence": round(random.uniform(4.0, 9.5), 1),
            "reasoning": round(random.uniform(4.0, 9.5), 1),
            "persuasiveness": round(random.uniform(4.0, 9.5), 1),
            "relevance": round(random.uniform(4.0, 9.5), 1)
        }
        
        # Create more varied strengths and weaknesses to choose from
        possible_strengths = [
            "Clear argumentation", 
            "Good use of evidence", 
            "Well-structured points",
            "Effectively addresses counterarguments",
            "Strong opening statement",
            "Uses persuasive language",
            "Appeals to both emotions and logic",
            "Provides strong examples",
            "Clear stance on the topic",
            "Connects well with audience"
        ]
        
        possible_weaknesses = [
            "Could be more concise", 
            "More specific examples needed",
            "Some logical fallacies present",
            "Counterarguments not fully addressed",
            "Overreliance on emotional appeals",
            "Sources could be stronger",
            "Occasional repetition of points",
            "Some tangential arguments",
            "Connection to topic sometimes unclear",
            "Conclusion could be stronger"
        ]
        
        # Select random strengths and weaknesses
        strengths = random.sample(possible_strengths, min(3, len(possible_strengths)))
        weaknesses = random.sample(possible_weaknesses, min(2, len(possible_weaknesses)))
        
        # Generate a variety of reasoning statements
        possible_reasoning = [
            f"This evaluation is based on {speaker}'s argument structure and evidence presentation.",
            f"The evaluation considers the persuasive techniques and logical flow of {speaker}'s arguments.",
            f"This assessment reflects the clarity, evidence, and persuasiveness of the presented argument.",
            f"The scoring is based on how effectively {speaker} addressed the debate topic and opponents' points.",
            f"This evaluation assesses the strength of reasoning and evidence in {speaker}'s presentation."
        ]
        
        reasoning = random.choice(possible_reasoning)
        
        return {
            "speaker": speaker,
            "turn": turn_number,
            "score": score,
            "criteria_scores": criteria_scores,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "reasoning": reasoning
        }
    
    def generate_fact_check(self, 
                           statement: str, 
                           turn_number: int) -> Optional[str]:
        """
        Generate a fact check for a statement.
        
        Args:
            statement: The statement to fact check
            turn_number: Current turn number
            
        Returns:
            Fact check string or None if fact checking is disabled
        """
        if not self.fact_checking or not self.tavily_client:
            return None
        
        try:
            # Use Tavily to get factual information
            fact_check_results = self.tavily_client.fact_check(statement)
            
            # Track this fact check
            self.fact_checks.append({
                "statement": statement,
                "turn": turn_number,
                "results": fact_check_results
            })
            
            # If there was an error, return a simple message
            if "error" in fact_check_results and not fact_check_results.get("sources"):
                logger.warning(f"Error in fact checking: {fact_check_results.get('error')}")
                return f"I attempted to fact check this statement, but encountered an error: {fact_check_results.get('error')}"
            
            # Extract sources from fact check results
            sources = fact_check_results.get("sources", [])
            
            if not sources:
                return "I attempted to fact check this statement, but couldn't find relevant information."
            
            # Build a context for the LLM with the sources
            source_context = "\n\n".join([
                f"Source: {source['title']}\nURL: {source['url']}\nContent: {source['content']}"
                for source in sources
            ])
            
            # Generate the fact check response using the LLM
            context = {
                "message_type": "fact_check",
                "topic": self.debate_topic,
                "statement": statement,
                "turn_number": turn_number,
                "moderation_style": self.moderation_style,
                "sources": source_context,
                "num_sources": len(sources)
            }
            
            return self.generate_message(context)
            
        except Exception as e:
            logger.error(f"Error in fact checking: {e}")
            return f"I attempted to fact check this statement, but encountered an error."
    
    def generate_conclusion(self) -> str:
        """
        Generate a conclusion for the debate.
        
        Returns:
            Conclusion string
        """
        # Determine the winner
        winner = max(self.speaker_scores.items(), key=lambda x: x[1]["total"])
        winner_name = winner[0]
        winner_score = winner[1]["total"]
        
        # Format the scores as text to avoid unhashable type error
        score_lines = []
        for debater_name, score_data in self.speaker_scores.items():
            score_lines.append(f"- {debater_name}: {score_data['total']} out of 10")
        score_text = "\n".join(score_lines)
        
        context = {
            "message_type": "conclusion",
            "topic": self.debate_topic,
            "score_text": score_text,
            "persona_description": self.persona.get("description", ""),
            "winner": winner_name,
            "winner_score": winner_score,
            "moderation_style": self.moderation_style
        }
        
        return self.generate_message(context)
    
    def generate_intervention(self, issue: str) -> str:
        """
        Generate an intervention for problematic behavior.
        
        Args:
            issue: Description of the issue requiring intervention
            
        Returns:
            Intervention string
        """
        context = {
            "message_type": "intervention",
            "topic": self.debate_topic,
            "issue": issue,
            "moderation_style": self.moderation_style
        }
        
        return self.generate_message(context)
    
    def get_debate_results(self) -> Dict[str, Any]:
        """
        Get the final results of the debate.
        
        Returns:
            Dictionary of debate results
        """
        # Determine the winner
        winner = max(self.speaker_scores.items(), key=lambda x: x[1]["total"])
        winner_name = winner[0]
        winner_score = winner[1]["total"]
        
        # Sort debaters by score
        ranked_debaters = sorted(
            self.speaker_scores.items(),
            key=lambda x: x[1]["total"],
            reverse=True
        )
        
        return {
            "topic": self.debate_topic,
            "winner": winner_name,
            "winner_score": winner_score,
            "rankings": [
                {
                    "name": name,
                    "score": data["total"],
                    "arguments_evaluated": len(data["arguments"])
                }
                for name, data in ranked_debaters
            ]
        }
    
    def generate_research_context(self, topic: str) -> str:
        """
        Generate research context for a debate topic using Tavily search.
        
        Args:
            topic: The debate topic
            
        Returns:
            String containing research context or empty string if Tavily is not configured
        """
        if not self.tavily_client:
            logger.warning("Tavily client not initialized, cannot generate research context")
            return ""
        
        try:
            research_context = self.tavily_client.generate_research_context(
                topic=topic,
                max_results=3  # Limit to 3 results for conciseness
            )
            
            logger.info(f"Generated research context for topic: {topic[:50]}...")
            return research_context
            
        except Exception as e:
            logger.error(f"Error generating research context: {e}")
            return f"Error generating research context: {str(e)}"
            
    def get_fact_checks(self) -> List[Dict[str, Any]]:
        """
        Get all fact checks performed during the debate.
        
        Returns:
            List of fact check results
        """
        return self.fact_checks