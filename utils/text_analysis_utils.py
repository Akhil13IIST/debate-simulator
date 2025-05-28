"""
Text Analysis Utilities Module

This module provides text analysis capabilities for the debate simulator,
including sentiment analysis, topic extraction, and other NLP features.
"""

import logging
import nltk
from textblob import TextBlob
from typing import Dict, Any, List, Tuple, Optional

# Download necessary NLTK resources on first run
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')
    nltk.download('punkt')

logger = logging.getLogger(__name__)

def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Analyze the sentiment of a text.
    
    Args:
        text: The text to analyze
        
    Returns:
        Dictionary containing sentiment analysis results
    """
    try:
        # Use TextBlob for sentiment analysis
        blob = TextBlob(text)
        
        # Get sentiment polarity (-1 to 1) and subjectivity (0 to 1)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Determine sentiment category
        if polarity > 0.3:
            sentiment = "positive"
        elif polarity < -0.3:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Emotional tone based on polarity and subjectivity
        if abs(polarity) > 0.6 and subjectivity > 0.6:
            tone = "emotional"
        elif abs(polarity) > 0.6 and subjectivity <= 0.6:
            tone = "factual but strong"
        elif abs(polarity) <= 0.3:
            tone = "balanced"
        else:
            tone = "moderate"
        
        return {
            "polarity": polarity,
            "subjectivity": subjectivity,
            "sentiment": sentiment,
            "tone": tone,
            "confidence": abs(polarity) * (1 - 0.5 * (0.5 - abs(0.5 - subjectivity)))
        }
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        return {
            "polarity": 0,
            "subjectivity": 0,
            "sentiment": "error",
            "tone": "unknown",
            "confidence": 0
        }

def extract_key_phrases(text: str, num_phrases: int = 5) -> List[str]:
    """
    Extract key phrases from text.
    
    Args:
        text: The text to analyze
        num_phrases: Number of key phrases to extract
        
    Returns:
        List of key phrases
    """
    try:
        # Use TextBlob for noun phrase extraction
        blob = TextBlob(text)
        noun_phrases = blob.noun_phrases
        
        # Filter and deduplicate phrases
        unique_phrases = []
        seen = set()
        
        for phrase in noun_phrases:
            if phrase not in seen and len(phrase.split()) >= 2:
                seen.add(phrase)
                unique_phrases.append(phrase)
        
        return unique_phrases[:num_phrases]
    except Exception as e:
        logger.error(f"Error extracting key phrases: {e}")
        return []

def analyze_debate_argument(argument: str) -> Dict[str, Any]:
    """
    Comprehensive analysis of a debate argument.
    
    Args:
        argument: The argument text to analyze
        
    Returns:
        Dictionary containing analysis results
    """
    try:
        # Sentiment analysis
        sentiment = analyze_sentiment(argument)
        
        # Key phrases
        key_phrases = extract_key_phrases(argument)
        
        # Basic text metrics
        words = argument.split()
        word_count = len(words)
        avg_word_length = sum(len(word) for word in words) / max(word_count, 1)
        sentence_count = len(nltk.sent_tokenize(argument))
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        # Complexity heuristic (simple approximation)
        complexity = min(1.0, (avg_sentence_length / 20) * (avg_word_length / 5))
        
        # Persuasiveness heuristic based on sentiment confidence and complexity
        persuasiveness = 0.4 * sentiment["confidence"] + 0.6 * complexity
        
        return {
            "sentiment": sentiment,
            "key_phrases": key_phrases,
            "metrics": {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "avg_word_length": avg_word_length,
                "avg_sentence_length": avg_sentence_length,
                "complexity": complexity
            },
            "persuasiveness": persuasiveness
        }
    except Exception as e:
        logger.error(f"Error analyzing debate argument: {e}")
        return {
            "sentiment": {"sentiment": "error"},
            "key_phrases": [],
            "metrics": {},
            "persuasiveness": 0
        }

def compare_arguments(argument1: str, argument2: str) -> Dict[str, Any]:
    """
    Compare two debate arguments.
    
    Args:
        argument1: First argument text
        argument2: Second argument text
        
    Returns:
        Dictionary containing comparison results
    """
    try:
        # Analyze both arguments
        analysis1 = analyze_debate_argument(argument1)
        analysis2 = analyze_debate_argument(argument2)
        
        # Compare sentiment
        sentiment_diff = analysis1["sentiment"]["polarity"] - analysis2["sentiment"]["polarity"]
        subjectivity_diff = analysis1["sentiment"]["subjectivity"] - analysis2["sentiment"]["subjectivity"]
        
        # Compare persuasiveness
        persuasiveness_diff = analysis1["persuasiveness"] - analysis2["persuasiveness"]
        
        # Compare complexity
        complexity_diff = analysis1["metrics"].get("complexity", 0) - analysis2["metrics"].get("complexity", 0)
        
        return {
            "sentiment_difference": sentiment_diff,
            "subjectivity_difference": subjectivity_diff,
            "persuasiveness_difference": persuasiveness_diff,
            "complexity_difference": complexity_diff,
            "more_persuasive": "first" if persuasiveness_diff > 0 else "second",
            "more_emotional": "first" if abs(analysis1["sentiment"]["polarity"]) > abs(analysis2["sentiment"]["polarity"]) else "second",
            "more_subjective": "first" if analysis1["sentiment"]["subjectivity"] > analysis2["sentiment"]["subjectivity"] else "second"
        }
    except Exception as e:
        logger.error(f"Error comparing arguments: {e}")
        return {
            "sentiment_difference": 0,
            "subjectivity_difference": 0,
            "persuasiveness_difference": 0,
            "complexity_difference": 0,
            "more_persuasive": "unknown",
            "more_emotional": "unknown",
            "more_subjective": "unknown"
        }