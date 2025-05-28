"""
Tavily Search Integration Module

This module provides utilities for interacting with the Tavily Search API
for factual information retrieval and fact-checking in debates.
"""

import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

class TavilySearchClient:
    """
    Client for interacting with the Tavily Search API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Tavily search client.
        
        Args:
            api_key: Tavily API key, if not provided will try to get from environment variable
        """
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY", "")
        self.base_url = "https://api.tavily.com/v1"
        
        if not self.api_key:
            logger.warning("No Tavily API key provided. Search functionality will be limited.")
    
    def search(self, 
              query: str, 
              search_depth: str = "basic",
              include_domains: Optional[List[str]] = None,
              exclude_domains: Optional[List[str]] = None,
              max_results: int = 5) -> Dict[str, Any]:
        """
        Perform a search using the Tavily API.
        
        Args:
            query: The search query
            search_depth: "basic" or "advanced" search (advanced is more thorough but slower)
            include_domains: List of domains to include in the search
            exclude_domains: List of domains to exclude from the search
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary containing search results
        """
        if not self.api_key:
            logger.error("Cannot perform search: No Tavily API key configured")
            return {"error": "No API key configured", "results": []}
        
        try:
            headers = {
                "Content-Type": "application/json",
                "X-Api-Key": self.api_key
            }
            
            payload = {
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results
            }
            
            if include_domains:
                payload["include_domains"] = include_domains
                
            if exclude_domains:
                payload["exclude_domains"] = exclude_domains
            
            response = requests.post(
                f"{self.base_url}/search",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Tavily API error: {response.status_code} - {response.text}")
                return {
                    "error": f"API error: {response.status_code}",
                    "results": []
                }
                
        except Exception as e:
            logger.error(f"Error in Tavily search: {e}")
            return {"error": str(e), "results": []}
    
    def fact_check(self, statement: str) -> Dict[str, Any]:
        """
        Perform a fact check on a statement using Tavily search.
        
        Args:
            statement: The statement to fact-check
            
        Returns:
            Dictionary containing fact-check results
        """
        try:
            # Construct a query that will help fact-check the statement
            query = f"fact check: {statement}"
            
            # Perform a search with this query
            search_results = self.search(
                query=query,
                search_depth="advanced",  # More thorough search for fact checking
                max_results=3  # Limit to top 3 most relevant results
            )
            
            # If there was an error in the search, return the error
            if "error" in search_results and not search_results.get("results"):
                return {
                    "statement": statement,
                    "is_factual": None,
                    "confidence": 0,
                    "error": search_results["error"],
                    "sources": []
                }
            
            # Extract facts from the search results
            results = search_results.get("results", [])
            
            # Build a list of sources
            sources = []
            for r in results:
                sources.append({
                    "title": r.get("title", "Unknown source"),
                    "url": r.get("url", ""),
                    "content": r.get("content", "")[:250] + "..." if len(r.get("content", "")) > 250 else r.get("content", "")
                })
            
            # For a real implementation, we could use another LLM call to analyze 
            # the factual accuracy based on the sources returned
            # For now, we'll just return the sources so they can be used in fact-checking
            
            return {
                "statement": statement,
                "sources": sources,
                "search_results": search_results
            }
            
        except Exception as e:
            logger.error(f"Error in fact checking: {e}")
            return {
                "statement": statement,
                "is_factual": None,
                "confidence": 0,
                "error": str(e),
                "sources": []
            }
    
    def generate_research_context(self, topic: str, max_results: int = 5) -> str:
        """
        Generate research context for a debate topic.
        
        Args:
            topic: The debate topic
            max_results: Maximum number of results to include
            
        Returns:
            String containing the research context
        """
        try:
            search_results = self.search(
                query=topic,
                search_depth="advanced",
                max_results=max_results
            )
            
            if "error" in search_results and not search_results.get("results"):
                return f"Error retrieving research: {search_results.get('error')}"
            
            results = search_results.get("results", [])
            
            # Format the results as a context summary
            context = f"## Research on: {topic}\n\n"
            
            for i, r in enumerate(results):
                context += f"### Source {i+1}: {r.get('title', 'Unknown source')}\n"
                context += f"URL: {r.get('url', 'No URL')}\n\n"
                
                # Include snippet of content
                content = r.get('content', '')
                snippet = content[:500] + "..." if len(content) > 500 else content
                context += f"{snippet}\n\n"
            
            return context
            
        except Exception as e:
            logger.error(f"Error generating research context: {e}")
            return f"Error generating research: {str(e)}"


# Utility function to get a singleton Tavily client
_tavily_client = None

def get_tavily_client(api_key: Optional[str] = None) -> TavilySearchClient:
    """
    Get a singleton instance of the Tavily search client.
    
    Args:
        api_key: Optional API key to use, will override previously set key
        
    Returns:
        TavilySearchClient instance
    """
    global _tavily_client
    
    if _tavily_client is None or api_key is not None:
        _tavily_client = TavilySearchClient(api_key)
    
    return _tavily_client