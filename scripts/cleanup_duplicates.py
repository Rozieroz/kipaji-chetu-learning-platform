"""
Clean up duplicate or similar questions from the database.
Deletes in correct order to respect foreign key constraints.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import delete, text
from dotenv import load_dotenv
import os
from app import models

load_dotenv()

ASYNC_DB_URL = os.getenv("DATABASE_URL_ASYNC")

async def cleanup():
    """Delete all quiz-related data in correct order."""
    engine = create_async_engine(ASYNC_DB_URL)
    
    async with engine.begin() as conn:
        # 1. First delete ai_feedback_logs (they reference quizzes)
        await conn.execute(delete(models.AIFeedbackLog))
        print("Deleted AI feedback logs")
        
        # 2. Then delete quiz_attempts (they reference quizzes)
        await conn.execute(delete(models.QuizAttempt))
        print("Deleted quiz attempts")
        
        # 3. Finally delete quizzes
        await conn.execute(delete(models.Quiz))
        print(" Deleted quizzes")
        
        print("\n All question-related data cleared successfully!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(cleanup())