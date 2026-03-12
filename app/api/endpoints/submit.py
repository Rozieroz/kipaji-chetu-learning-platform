"""
POST /submit-answer endpoint with Groq-powered feedback.

Records a student's quiz attempt and returns basic result.
--> This endpoint accepts a student's answer submission, evaluates it against the correct answer, 
    stores the attempt in the database, and returns the recorded attempt with correctness and score.

    ====================================
POST /submit-answer endpoint accepting frontend payload.
Maps frontend fields to database model.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import crud, schemas, models
from app.database import get_db
from app.automated.client import automated_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/submit-answer", response_model=schemas.QuizAttemptWithFeedback)
async def submit_answer(
    submission: schemas.AnswerSubmissionFrontend,
    db: AsyncSession = Depends(get_db)
):
    """
    Accept a student's answer (frontend format), evaluate it,
    generate AI feedback, store the attempt, and return with feedback.
    """
    # Fetch quiz using question_id as quiz_id
    quiz = await db.get(models.Quiz, submission.question_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Fetch student
    student = await db.get(models.Student, submission.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Determine selected letter
    selected_letter = submission.answer if submission.answer in ['A','B','C','D'] else None
    if not selected_letter:
        # Try mapping from full text (if answer was the full option text)
        option_map = {
            quiz.option_a: 'A',
            quiz.option_b: 'B',
            quiz.option_c: 'C',
            quiz.option_d: 'D',
        }
        selected_letter = option_map.get(submission.answer)
    if not selected_letter and submission.answer_index is not None:
        # Fallback using index (0→A, 1→B, etc.)
        index_to_letter = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
        selected_letter = index_to_letter.get(submission.answer_index)
    if not selected_letter:
        raise HTTPException(status_code=400, detail="Could not map answer to a valid option")

    # Determine correctness
    is_correct = (selected_letter == quiz.correct_answer)
    score = 100.0 if is_correct else 0.0

    # Generate AI feedback
    simplified_mode = student.learning_mode == "simplified" or student.accessibility_enabled
    feedback_text = await automated_service.generate_feedback(
        question=quiz.question,
        user_answer=selected_letter,          # pass the letter for clarity
        correct_answer=quiz.correct_answer,
        is_correct=is_correct,
        simplified=simplified_mode
    )

    # Prepare attempt data (time_taken not provided, default to 0)
    attempt_data = schemas.QuizAttemptCreate(
        student_id=submission.student_id,
        quiz_id=submission.question_id,
        selected_answer=selected_letter,
        is_correct=is_correct,
        score=score,
        time_taken=0,                          # placeholder; could be enhanced
        attempt_number=1
    )

    try:
        # Store attempt
        attempt = await crud.create_quiz_attempt(db, attempt_data)

        # Log automated interaction
        await crud.log_automated_interaction(
            db=db,
            student_id=student.id,
            quiz_id=quiz.id,
            prompt=f"Q: {quiz.question}\nUser: {selected_letter}\nCorrect: {quiz.correct_answer}",
            response=feedback_text,
            simplified_mode=simplified_mode
        )

        # Attach feedback to response
        attempt.feedback = feedback_text

        # Update student's preferred difficulty (optional, call after commit)
        await crud.update_student_difficulty(db, submission.student_id)

        logger.info(f"Stored attempt {attempt.id} for student {submission.student_id}")

    except Exception as e:
        logger.error(f"Failed to store attempt or log interaction: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    return attempt