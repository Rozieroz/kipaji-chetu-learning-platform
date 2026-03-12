"""
create records only if they don't already exist.

Seed script to populate the database with sample data:
- Create a demo teacher.
- Create a class.
- Create two students: John Doe and Jane Doe.
- Enrol them in the class.
- Insert a few topics (if not already present).
"""


"""
Idempotent seed script: creates records only if they don't already exist.
"""

import os
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from dotenv import load_dotenv
from app import models
from app.database import Base

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ASYNC_DB_URL = os.getenv("DATABASE_URL_ASYNC")
if not ASYNC_DB_URL:
    raise RuntimeError("DATABASE_URL_ASYNC not set in .env")

DB_SCHEMA = os.getenv("schema", "public")

async def get_or_create_teacher(db: AsyncSession, email: str, defaults: dict):
    """Get existing teacher or create new one."""
    result = await db.execute(select(models.Teacher).where(models.Teacher.email == email))
    teacher = result.scalar_one_or_none()
    if teacher:
        logger.info(f"Teacher {email} already exists, skipping.")
        return teacher
    teacher = models.Teacher(**defaults, email=email)
    db.add(teacher)
    await db.flush()
    logger.info(f"Created teacher {email}")
    return teacher

async def get_or_create_class(db: AsyncSession, class_code: str, defaults: dict):
    result = await db.execute(select(models.Class).where(models.Class.class_code == class_code))
    cls = result.scalar_one_or_none()
    if cls:
        logger.info(f"Class {class_code} already exists, skipping.")
        return cls
    cls = models.Class(**defaults, class_code=class_code)
    db.add(cls)
    await db.flush()
    logger.info(f"Created class {class_code}")
    return cls

async def get_or_create_student(db: AsyncSession, email: str, defaults: dict):
    result = await db.execute(select(models.Student).where(models.Student.email == email))
    student = result.scalar_one_or_none()
    if student:
        logger.info(f"Student {email} already exists, skipping.")
        return student
    student = models.Student(**defaults, email=email)
    db.add(student)
    await db.flush()
    logger.info(f"Created student {email}")
    return student

async def get_or_create_topic(db: AsyncSession, data: dict):
    """
    Create a topic if it doesn't exist.
    The 'data' dict must contain at least the 'name' field.
    """
    name = data["name"]
    result = await db.execute(select(models.Topic).where(models.Topic.name == name))
    topic = result.scalar_one_or_none()
    if topic:
        logger.info(f"Topic {name} already exists, skipping.")
        return topic
    topic = models.Topic(**data)
    db.add(topic)
    await db.flush()
    logger.info(f"Created topic {name}")
    return topic

async def seed():
    engine = create_async_engine(ASYNC_DB_URL, echo=True)

    async with engine.begin() as conn:
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}"))
        await conn.execute(text(f"SET search_path TO {DB_SCHEMA}"))

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # 1. Teacher
        teacher = await get_or_create_teacher(
            db,
            email="teacher@kipaji.com",
            defaults={"name": "Demo Teacher", "password_hash": ""}
        )

        # 2. Class
        class_ = await get_or_create_class(
            db,
            class_code="MATH101",
            defaults={
                "name": "Mathematics 101",
                "teacher_id": teacher.id,
                "subject": "Mathematics",
                "description": "Introductory math class"
            }
        )

        # 3. Students (with preferred_difficulty)
        student1 = await get_or_create_student(
            db,
            email="john.doe@example.com",
            defaults={
                "first_name": "John",
                "last_name": "Doe",
                "learning_mode": "normal",
                "accessibility_enabled": False,
                "risk_score": 0.0,
                "preferred_difficulty": "medium"
            }
        )
        student2 = await get_or_create_student(
            db,
            email="jane.doe@example.com",
            defaults={
                "first_name": "Jane",
                "last_name": "Doe",
                "learning_mode": "simplified",
                "accessibility_enabled": True,
                "risk_score": 0.0,
                "preferred_difficulty": "easy"
            }
        )

        # 4. Enrol students in class (many-to-many)
        for student in [student1, student2]:
            stmt = select(models.ClassStudent).where(
                models.ClassStudent.class_id == class_.id,
                models.ClassStudent.student_id == student.id
            )
            result = await db.execute(stmt)
            if not result.scalar_one_or_none():
                enrolment = models.ClassStudent(class_id=class_.id, student_id=student.id)
                db.add(enrolment)
                logger.info(f"Enrolled {student.email} in {class_.class_code}")

        # 5. Topics (data includes name)
        topics_data = [
            {"name": "Algebra", "description": "Equations and variables", "difficulty_level": "medium"},
            {"name": "Geometry", "description": "Shapes and angles", "difficulty_level": "hard"},
            {"name": "Arithmetic", "description": "Basic operations", "difficulty_level": "easy"},
        ]
        for t in topics_data:
            await get_or_create_topic(db, data=t)

        await db.commit()
        logger.info("Seeding completed successfully!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed())