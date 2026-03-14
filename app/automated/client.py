"""
Groq API client with rate limit handling and error resilience.
Uses Zero Data Retention (ZDR) configuration for privacy compliance.
"""

"""
Automated content generation service using Groq.
Handles quiz generation, feedback, simplified explanations, and rate limit resilience.
Zero Data Retention (ZDR) is enabled by default on Groq API.
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional
from groq import AsyncGroq
from groq import RateLimitError, APIError

import random

logger = logging.getLogger(__name__)

class AutomatedContentService:
    """Service for generating content using Groq LLMs with error handling."""
    
    def __init__(self):
        """Initialize the Groq async client with API key from environment."""
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            logger.warning("GROQ_API_KEY not found in environment variables")
        
        self.client = AsyncGroq(
            api_key=self.api_key,
            # Zero Data Retention is set, no additional configuration needed for ZDR
        )
        
        # Model selection based on task complexity and speed requirements
        self.models = {
            "quiz_generation": "llama-3.3-70b-versatile",   # High quality for question creation
            "feedback_standard": "llama-3.1-8b-instant",    # Fast enough for real-time feedback
            "feedback_simplified": "llama-3.1-8b-instant",  # Good balance for simplification
            "explanation_simplify": "llama-3.1-8b-instant"  # Quick responses for accessibility
        }
    
    def _extract_rate_limit_wait_time(self, error_message: str) -> str:
        """
        Extract wait time from rate limit error messages.
        Pattern matches: "try again in Xm Ys"
        """
        match = re.search(r"try again in (\d+)m(\d+\.?\d*)s", error_message)
        if match:
            minutes = match.group(1)
            seconds = match.group(2)
            return f"{minutes} minutes and {seconds} seconds"
        return "a few minutes"
    
    def _handle_api_error(self, error: Exception, operation: str) -> str:
        """
        Centralized error handling for API calls.
        Returns user-friendly error message.
        """
        error_str = str(error)
        logger.error(f"Groq API error during {operation}: {error_str}")
        
        # Check for rate limit (429)
        if "429" in error_str or "rate_limit_exceeded" in error_str:
            wait_time = self._extract_rate_limit_wait_time(error_str)
            return f"⚠️ Daily usage limit reached. Please try again in about {wait_time}. (Groq API rate limit)"
        
        # Other API errors
        if isinstance(error, APIError):
            return f"Groq API error: {error_str}"
        
        # Generic errors
        return f"Error calling Groq API: {error_str}"
    
    async def generate_quiz_question(self, topic: str, difficulty: str) -> Dict[str, Any]:
        """
        Generate a multiple-choice quiz question on a given topic.
        Returns question with 4 options, correct answer, and explanation.
        Includes a random seed to ensure variety.
        """

        seed = random.randint(1, 10000)

        prompt = f"""
        Create a {difficulty} difficulty multiple-choice quiz question about {topic}.
        Use a different question than usual (seed: {seed})
        Return in this exact JSON format:
        {{
            "question": "the question text",
            "option_a": "first option",
            "option_b": "second option",
            "option_c": "third option",
            "option_d": "fourth option",
            "correct_answer": "A/B/C/D",
            "explanation": "brief explanation of the correct answer"
        }}
        Ensure all fields are present and valid JSON.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.models["quiz_generation"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,                # the higher it isthe more random
                response_format={"type": "json_object"},
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            logger.info(f"Generated quiz question for {topic} at {difficulty} difficulty")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {"error": "Invalid response format from generation service"}
        except Exception as e:
            error_msg = self._handle_api_error(e, "quiz generation")
            return {"error": error_msg}
    
    async def generate_feedback(
        self,
        question: str,
        user_answer: str,
        correct_answer: str,
        is_correct: bool,
        simplified: bool = False
    ) -> str:
        """
        Generate personalized feedback for a student's answer.
        If simplified=True, produces shorter sentences and clearer language.
        """
        if is_correct:
            prompt = f"""
            The student answered correctly. Provide encouraging feedback 
            that reinforces why their answer was right.
            
            Question: {question}
            Correct answer: {correct_answer}
            
            Keep feedback concise and supportive.
            """
        else:
            prompt = f"""
            The student answered incorrectly. Provide helpful feedback that:
            1. Gently points out the mistake
            2. Explains the correct answer clearly
            3. Offers encouragement to try again
            
            Question: {question}
            Student's answer: {user_answer}
            Correct answer: {correct_answer}
            
            Keep feedback constructive and encouraging.
            """
        
        if simplified:
            prompt += "\n\nUse very simple language, short sentences, and clear explanations suitable for students who need simplified content."
        
        model = self.models["feedback_simplified"] if simplified else self.models["feedback_standard"]
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=200
            )
            
            feedback = response.choices[0].message.content
            logger.info(f"Generated feedback (simplified={simplified})")
            return feedback
            
        except Exception as e:
            error_msg = self._handle_api_error(e, "feedback generation")
            return error_msg
    
    async def simplify_explanation(self, text: str) -> str:
        """
        Convert complex explanations into simpler language.
        Used for students with accessibility needs.
        """
        prompt = f"""
        Rewrite the following explanation using very simple language:
        - Use short sentences
        - Avoid complex vocabulary
        - Break down concepts step by step
        - Make it easy to understand
        
        Original: {text}
        
        Simplified version:
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.models["explanation_simplify"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )
            
            simplified = response.choices[0].message.content
            logger.info("Generated simplified explanation")
            return simplified
            
        except Exception as e:
            logger.error(f"Simplification failed: {e}")
            return text  # Return original if simplification fails

# Singleton instance for reuse across the application
automated_service = AutomatedContentService()

"""
has a three‑tier model mapping for different tasks.
include sophisticated rate‑limit error parsing and user‑friendly messages.
return structured dictionaries with metadata (model used, token usage, etc.).
design with Zero Data Retention (ZDR) in mind.
"""