"""
Automated content generation service using Groq.
Handles quiz generation, feedback, and simplified explanations.
"""

import os
import logging
from typing import Dict, Any, Optional
from groq import Groq, AsyncGroq

logger = logging.getLogger(__name__)

class AutomatedContentService:
    """Service for generating content using Groq LLMs."""
    
    def __init__(self):
        self.client = AsyncGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        )
        # Model selection based on task complexity
        self.quiz_model = "llama-3.3-70b-versatile"  # Complex reasoning
        self.feedback_model = "llama-3.1-8b-instant"  # Faster, lighter
        self.simplified_model = "llama-3.1-8b-instant"  # Quick responses
        
    async def generate_quiz_question(self, topic: str, difficulty: str) -> Dict[str, Any]:
        """
        Generate a multiple-choice quiz question on a given topic.
        Returns question with 4 options and correct answer.
        """
        prompt = f"""
        Create a {difficulty} difficulty multiple-choice quiz question about {topic}.
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
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.quiz_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Generated quiz question for {topic} at {difficulty} difficulty")
            return result
            
        except Exception as e:
            logger.error(f"Quiz generation failed: {e}")
            raise
    
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
        
        try:
            response = await self.client.chat.completions.create(
                model=self.feedback_model if not simplified else self.simplified_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=200
            )
            
            feedback = response.choices[0].message.content
            logger.info(f"Generated feedback (simplified={simplified})")
            return feedback
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"Feedback generation failed: {error_str}")

            if "429" in error_str or "rate_limit_exceeded" in error_str:
                match = re.search(r"try again in (\d+)m(\d+\.?\d*)s", error_str)
                if match:
                    minutes, seconds = match.groups()
                    wait_time = f"{minutes} minutes and {seconds} seconds"
                else:
                    wait_time = "a few minutes"

                return f"⚠️ API rate limit reached. Please try again in {wait_time}."

            return "Unable to generate feedback at this time. Please try again."    
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
                model=self.simplified_model,
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

# Singleton instance
automated_service = AutomatedContentService()

"""

"""