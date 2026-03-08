"""
GET /next-question endpoint.
Returns a quiz question of appropriate difficulty for the student.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models, schemas
from app.database import get_db
from app.automated.client import automated_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/next-question/{student_id}/{topic_id}", response_model=schemas.Quiz)
async def get_next_question(
    student_id: int,
    topic_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Return a quiz question for the given student and topic.
    Difficulty is determined by the student's preferred_difficulty.
    If no suitable question exists in the database, generate one via Groq and store it.
    """
    # Fetch student and topic
    student = await db.get(models.Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    topic = await db.get(models.Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Determine target difficulty
    target_difficulty = student.preferred_difficulty or "medium"
    
    # Try to find an existing question for this topic and difficulty
    # Optionally ensure the student hasn't seen it recently (simplified: just pick any)
    stmt = (
        select(models.Quiz)
        .where(models.Quiz.topic_id == topic_id)
        .where(models.Quiz.difficulty_level == target_difficulty)
        .order_by(models.Quiz.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    question = result.scalar_one_or_none()
    
    if question:
        logger.info(f"Found existing question {question.id} for topic {topic_id}, difficulty {target_difficulty}")
        return question
    
    # No existing question – generate one via Groq
    logger.info(f"No question found for topic {topic_id}, difficulty {target_difficulty}. Generating...")
    generated = await automated_service.generate_quiz_question(
        topic=topic.name,
        difficulty=target_difficulty
    )
    
    if "error" in generated:
        raise HTTPException(status_code=503, detail=generated["error"])
    
    # Create new quiz record
    new_quiz = models.Quiz(
        topic_id=topic_id,
        question=generated["question"],
        option_a=generated["option_a"],
        option_b=generated["option_b"],
        option_c=generated["option_c"],
        option_d=generated["option_d"],
        correct_answer=generated["correct_answer"],
        difficulty_level=target_difficulty,
        ai_generated=True
    )
    db.add(new_quiz)
    await db.commit()
    await db.refresh(new_quiz)
    logger.info(f"Generated and stored new quiz {new_quiz.id}")
    
    return new_quiz