"""
GET /next-question/{student_id}/{topic_id} endpoint.
Returns a quiz question with built-in variety.
"""

import logging
import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
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
    Return a quiz question for the given student with variety.
    Rotates through available questions and generates new ones as needed.
    """
    # Fetch student and topic
    student = await db.get(models.Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    topic = await db.get(models.Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    target_difficulty = student.preferred_difficulty or "medium"
    
    # Get IDs of questions this student has already attempted
    subquery = (
        select(models.QuizAttempt.quiz_id)
        .where(models.QuizAttempt.student_id == student_id)
        .subquery()
    )
    
    # STRATEGY 1: Try to find an unseen question of any difficulty first
    stmt = (
        select(models.Quiz)
        .where(models.Quiz.topic_id == topic_id)
        .where(models.Quiz.id.not_in(subquery))
        .order_by(models.Quiz.created_at.desc())
        .limit(5)  # Get up to 5 unseen questions
    )
    result = await db.execute(stmt)
    unseen_questions = result.scalars().all()
    
    if unseen_questions:
        # Randomly select one of the unseen questions
        selected = random.choice(unseen_questions)
        logger.info(f"Selected random unseen question {selected.id} for student {student_id}")
        return selected
    
    # STRATEGY 2: If no unseen questions, get ALL questions for this topic
    stmt = (
        select(models.Quiz)
        .where(models.Quiz.topic_id == topic_id)
        .order_by(models.Quiz.created_at.desc())
    )
    result = await db.execute(stmt)
    all_questions = result.scalars().all()
    
    if all_questions:
        # Student has seen all questions - pick a random one for review
        # This is better than generating new ones constantly
        selected = random.choice(all_questions)
        logger.info(f"All questions seen - recycling question {selected.id} for student {student_id}")
        return selected
    
    # STRATEGY 3: No questions exist at all - generate one
    logger.info(f"No questions found for topic {topic_id}, generating new one...")
    
    # Get recent questions to avoid repetition (from database)
    recent_stmt = (
        select(models.Quiz.question)
        .where(models.Quiz.topic_id == topic_id)
        .order_by(models.Quiz.created_at.desc())
        .limit(5)
    )
    recent_result = await db.execute(recent_stmt)
    recent_questions = [q[0] for q in recent_result.fetchall()]
    
    generated = await automated_service.generate_quiz_question(
        topic=topic.name,
        difficulty=target_difficulty,
        recent_questions=recent_questions
    )
    
    if "error" in generated:
        # If generation fails, create a simple fallback question
        fallback_questions = [
            {
                "question": "What is 2 + 2?",
                "option_a": "3",
                "option_b": "4", 
                "option_c": "5",
                "option_d": "6",
                "correct_answer": "B"
            },
            {
                "question": "What is the capital of France?",
                "option_a": "London",
                "option_b": "Berlin",
                "option_c": "Paris",
                "option_d": "Madrid", 
                "correct_answer": "C"
            },
            {
                "question": "Which planet is known as the Red Planet?",
                "option_a": "Venus",
                "option_b": "Mars",
                "option_c": "Jupiter",
                "option_d": "Saturn",
                "correct_answer": "B"
            }
        ]
        fallback = random.choice(fallback_questions)
        
        new_quiz = models.Quiz(
            topic_id=topic_id,
            question=fallback["question"],
            option_a=fallback["option_a"],
            option_b=fallback["option_b"],
            option_c=fallback["option_c"],
            option_d=fallback["option_d"],
            correct_answer=fallback["correct_answer"],
            difficulty_level=target_difficulty,
            ai_generated=False
        )
        db.add(new_quiz)
        await db.commit()
        await db.refresh(new_quiz)
        logger.info(f"Created fallback question {new_quiz.id}")
        return new_quiz
    
    # Create and store the AI-generated question
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