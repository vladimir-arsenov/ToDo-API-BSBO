from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Task
from database import get_async_session
from datetime import datetime, timezone

router = APIRouter(
    prefix="/stats",
    tags=["statistics"]
)


@router.get("", response_model=dict)
async def get_tasks_stats(
        db: AsyncSession = Depends(get_async_session)
) -> dict:
    """
    Получить статистику задач.
    НОВОЕ: Добавлен подсчет просроченных задач (overdue_tasks).
    """
    result = await db.execute(select(Task))
    tasks = result.scalars().all()

    total_tasks = len(tasks)

    by_quadrant = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
    by_status = {"completed": 0, "pending": 0}
    overdue_tasks = 0  # НОВОЕ: количество просроченных задач

    now = datetime.now(timezone.utc)

    for task in tasks:
        # Подсчет по квадрантам
        if task.quadrant in by_quadrant:
            by_quadrant[task.quadrant] += 1

        # Подсчет по статусу
        if task.completed:
            by_status["completed"] += 1
        else:
            by_status["pending"] += 1

            # НОВОЕ: Проверка на просроченные задачи
            if task.deadline_at:
                deadline = task.deadline_at
                if deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=timezone.utc)

                if deadline < now:
                    overdue_tasks += 1

    return {
        "total_tasks": total_tasks,
        "by_quadrant": by_quadrant,
        "by_status": by_status,
        "overdue_tasks": overdue_tasks  # НОВОЕ
    }
