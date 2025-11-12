from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Task
from schemas import TaskCreate, TaskUpdate, TaskResponse
from database import get_async_session

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Task not found"}},
)


def calculate_urgency(deadline_at: datetime | None) -> bool:
    """
    Определяет срочность задачи на основе дедлайна.
    Возвращает True если дедлайн меньше 3 дней от текущего момента.

    Args:
        deadline_at: Дедлайн задачи (с timezone или без)

    Returns:
        bool: True если срочно (< 3 дней), False в остальных случаях
    """
    if deadline_at is None:
        return False

    # Получаем текущее время с timezone
    now = datetime.now(timezone.utc)

    # Если deadline без timezone, добавляем UTC
    if deadline_at.tzinfo is None:
        deadline_at = deadline_at.replace(tzinfo=timezone.utc)

    # Разница между дедлайном и текущим временем
    time_until_deadline = deadline_at - now

    # Срочно если осталось меньше 3 дней
    return time_until_deadline < timedelta(days=3)


def calculate_quadrant(is_important: bool, is_urgent: bool) -> str:
    """Определяет квадрант по матрице Эйзенхауэра"""
    if is_important and is_urgent:
        return "Q1"
    elif is_important and not is_urgent:
        return "Q2"
    elif not is_important and is_urgent:
        return "Q3"
    else:
        return "Q4"


@router.get("", response_model=List[TaskResponse])
async def get_all_tasks(
        db: AsyncSession = Depends(get_async_session)
) -> List[TaskResponse]:
    """Получить все задачи"""
    result = await db.execute(select(Task))
    tasks = result.scalars().all()
    return tasks


@router.get("/quadrant/{quadrant}", response_model=List[TaskResponse])
async def get_tasks_by_quadrant(
        quadrant: str,
        db: AsyncSession = Depends(get_async_session)
) -> List[TaskResponse]:
    """Получить задачи по квадранту (Q1, Q2, Q3, Q4)"""
    if quadrant not in ["Q1", "Q2", "Q3", "Q4"]:
        raise HTTPException(
            status_code=400,
            detail="Неверный квадрант. Используйте: Q1, Q2, Q3, Q4"
        )

    result = await db.execute(
        select(Task).where(Task.quadrant == quadrant)
    )
    tasks = result.scalars().all()
    return tasks


@router.get("/search", response_model=List[TaskResponse])
async def search_tasks(
        q: str = Query(..., min_length=2, description="Поисковый запрос"),
        db: AsyncSession = Depends(get_async_session)
) -> List[TaskResponse]:
    """Поиск задач по названию или описанию"""
    keyword = f"%{q.lower()}%"

    result = await db.execute(
        select(Task).where(
            (Task.title.ilike(keyword)) |
            (Task.description.ilike(keyword))
        )
    )
    tasks = result.scalars().all()

    if not tasks:
        raise HTTPException(
            status_code=404,
            detail="По данному запросу ничего не найдено"
        )

    return tasks


@router.get("/status/{status}", response_model=List[TaskResponse])
async def get_tasks_by_status(
        status: str,
        db: AsyncSession = Depends(get_async_session)
) -> List[TaskResponse]:
    """Получить задачи по статусу (completed/pending)"""
    if status not in ["completed", "pending"]:
        raise HTTPException(
            status_code=400,
            detail="Недопустимый статус. Используйте: completed или pending"
        )

    is_completed = (status == "completed")

    result = await db.execute(
        select(Task).where(Task.completed == is_completed)
    )
    tasks = result.scalars().all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_by_id(
        task_id: int,
        db: AsyncSession = Depends(get_async_session)
) -> TaskResponse:
    """Получить задачу по ID"""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    return task


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
        task: TaskCreate,
        db: AsyncSession = Depends(get_async_session)
) -> TaskResponse:
    """
    Создать новую задачу.
    Срочность (is_urgent) определяется автоматически на основе deadline_at:
    - Если дедлайн < 3 дней → срочно
    - Если дедлайн >= 3 дней или не указан → не срочно
    """
    # НОВОЕ: Автоматически определяем срочность из deadline_at
    is_urgent = calculate_urgency(task.deadline_at)

    # Определяем квадрант
    quadrant = calculate_quadrant(task.is_important, is_urgent)

    new_task = Task(
        title=task.title,
        description=task.description,
        is_important=task.is_important,
        is_urgent=is_urgent,  # Вычисляется автоматически
        quadrant=quadrant,
        completed=False,
        deadline_at=task.deadline_at  # НОВОЕ
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return new_task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
        task_id: int,
        task_update: TaskUpdate,
        db: AsyncSession = Depends(get_async_session)
) -> TaskResponse:
    """
    Обновить задачу.
    При изменении deadline_at срочность пересчитывается автоматически.
    """
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    # Получаем только те поля, которые были переданы
    update_data = task_update.model_dump(exclude_unset=True)

    # Обновляем поля
    for field, value in update_data.items():
        setattr(task, field, value)

    # НОВОЕ: Пересчитываем срочность если изменился deadline_at
    if "deadline_at" in update_data:
        task.is_urgent = calculate_urgency(task.deadline_at)

    # Пересчитываем квадрант если изменились важность или срочность
    if "is_important" in update_data or "deadline_at" in update_data:
        task.quadrant = calculate_quadrant(task.is_important, task.is_urgent)

    await db.commit()
    await db.refresh(task)

    return task


@router.patch("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
        task_id: int,
        db: AsyncSession = Depends(get_async_session)
) -> TaskResponse:
    """Отметить задачу как завершенную"""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    task.completed = True
    task.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(task)

    return task


@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
async def delete_task(
        task_id: int,
        db: AsyncSession = Depends(get_async_session)
) -> dict:
    """Удалить задачу"""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    deleted_task_info = {
        "id": task.id,
        "title": task.title
    }

    await db.delete(task)
    await db.commit()

    return {
        "message": "Задача успешно удалена",
        "id": deleted_task_info["id"],
        "title": deleted_task_info["title"]
    }
