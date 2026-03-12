"""
GET /students/{student_id} endpoint.
Returns a student's details by ID.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas
from app.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/students/{student_id}", response_model=schemas.Student)
async def get_student(
    student_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a student by their ID.
    """
    student = await crud.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student