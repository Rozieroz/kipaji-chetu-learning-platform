"""
GET /topics endpoint.
Returns a list of all topics.
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models, schemas
from app.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/topics", response_model=list[schemas.Topic])
async def get_topics(db: AsyncSession = Depends(get_db)):
    """Return all topics."""
    result = await db.execute(select(models.Topic))
    topics = result.scalars().all()
    return topics