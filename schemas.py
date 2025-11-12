from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TaskBase(BaseModel):
    """Базовая схема задачи"""
    title: str = Field(..., min_length=3, max_length=200, description="Название задачи")
    description: Optional[str] = Field(None, max_length=500, description="Описание задачи")
    is_important: bool = Field(..., description="Важная задача?")
    deadline_at: Optional[datetime] = Field(None, description="Дедлайн задачи (срочность определяется автоматически)")


class TaskCreate(TaskBase):
    """Схема для создания задачи"""
    # is_urgent будет вычисляться автоматически из deadline_at
    pass


class TaskUpdate(BaseModel):
    """Схема для обновления задачи (все поля опциональные)"""
    title: Optional[str] = Field(None, min_length=3, max_length=200, description="Название задачи")
    description: Optional[str] = Field(None, max_length=500, description="Описание задачи")
    is_important: Optional[bool] = Field(None, description="Важная задача?")
    deadline_at: Optional[datetime] = Field(None, description="Дедлайн задачи")
    completed: Optional[bool] = Field(None, description="Задача завершена?")


class TaskResponse(TaskBase):
    """Схема для ответа (что возвращает API)"""
    id: int = Field(..., description="ID задачи", examples=[1])
    is_urgent: bool = Field(..., description="Срочная задача? (вычисляется автоматически)")
    quadrant: str = Field(..., description="Квадрант: Q1, Q2, Q3, Q4", examples=["Q1"])
    completed: bool = Field(default=False, description="Задача завершена?")
    created_at: datetime = Field(..., description="Дата создания")
    completed_at: Optional[datetime] = Field(None, description="Дата завершения")

    class Config:
        from_attributes = True  # Для работы с SQLAlchemy моделями
