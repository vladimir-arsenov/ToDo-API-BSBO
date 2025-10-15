# Главный файл приложения
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
from datetime import datetime


app = FastAPI(
    title="ToDo лист API",
    description="API для управления задачами с использованием матрицы Эйзенхауэра",
    version="1.0.0",
    contact={
        "name" : "Владимир Арсенов"
    }
)

# Временное хранилище (позже будет заменено на PostgreSQL)
tasks_db: List[Dict[str, Any]] = [
    {
        "id": 1,
        "title": "Сдать проект по FastAPI",
        "description": "Завершить разработку API и написать документацию",
        "is_important": True,
        "is_urgent": True,
        "quadrant": "Q1",
        "completed": False,
        "created_at": datetime.now()
    },
    {
        "id": 2,
        "title": "Изучить SQLAlchemy",
        "description": "Прочитать документацию и попробовать примеры",
        "is_important": True,
        "is_urgent": False,
        "quadrant": "Q2",
        "completed": False,
        "created_at": datetime.now()
    },
    {
        "id": 3,
        "title": "Сходить на лекцию",
        "description": None,
        "is_important": False,
        "is_urgent": True,
        "quadrant": "Q3",
        "completed": False,
        "created_at": datetime.now()
    },
    {
        "id": 4,
        "title": "Посмотреть сериал",
        "description": "Новый сезон любимого сериала",
        "is_important": False,
        "is_urgent": False,
        "quadrant": "Q4",
        "completed": True,
        "created_at": datetime.now()
    },
]

@app.get("/")
async def welcome() -> dict:
    return {"message": "Привет, студент!" , "title": app.title, "description": app.description, "version": app.version, "contact":app.contact}

@app.get("/tasks")
async def get_all_tasks() -> dict:
    return {
        "count": len(tasks_db), # считает количество записей в хранилище
        "tasks": tasks_db # выводит всё, чта есть в хранилище
    }


@app.get("/tasks/quadrant/{quadrant}")
async def get_tasks_by_quadrant(quadrant: str) -> dict:
    if quadrant not in ["Q1", "Q2", "Q3", "Q4"]:
        raise HTTPException( #специальный класс в FastAPI для возврата HTTP ошибок. Не забудьте добавть его вызов в 1 строке
            status_code=400,
            detail="Неверный квадрант. Используйте: Q1, Q2, Q3, Q4" #текст, который будет выведен пользователю
        )
    filtered_tasks = [
        task # ЧТО добавляем в список
        for task in tasks_db # ОТКУДА берем элементы
        if task["quadrant"] == quadrant # УСЛОВИЕ фильтрации
    ]   
    return {
        "quadrant": quadrant,
        "count": len(filtered_tasks),
        "tasks": filtered_tasks
    }

@app.get("/tasks/stats")
async def get_tasks_stats() -> dict:
    return { 
        "total_tasks": len(tasks_db),
        "by_quadrant": 
        { 
            "Q1": len([task for task in tasks_db if task["quadrant"] == "Q1" ]),
            "Q2": len([task for task in tasks_db if task["quadrant"] == "Q2" ]),
            "Q3": len([task for task in tasks_db if task["quadrant"] == "Q3" ]),
            "Q4": len([task for task in tasks_db if task["quadrant"] == "Q4" ]),
        }, 
        "by_status": 
        { 
            "completed": len([task for task in tasks_db if task["completed"] == True ]), 
            "pending": len([task for task in tasks_db if task["completed"] == False ]),
        } 
    }

@app.get("/tasks/search")
async def search_tasks(q: str) -> dict:
    if len(q) < 2:
        raise HTTPException( 
            status_code=400,
            detail="Строка должна быть длинее 2 символов" 
        )
    q = q.lower()
    tasks = [ task for task in tasks_db if (q in task["title"].lower() or task["description"] and q in task["description"].lower()) ]

    return { 
        "query": q, 
        "count": len(tasks), 
        "tasks": tasks 
        }


@app.get("/tasks/{status}")
async def get_tasks_by_status(status: str) -> dict:
    if status != "completed" and status != "pending":
        raise HTTPException( 
            status_code=400,
            detail="Нет такого статуса" 
        )

    tasks = [task for task in tasks_db if task["completed"] == (status == "completed") ]
    return { 
        "status": status, 
        "count": len(tasks),
        "tasks": tasks 
    }



@app.get("/tasks/{task_id}")
async def get_task_by_id(task_id: int) -> dict:
    if task_id <= 0 or task_id > len(tasks_db):
        raise HTTPException( 
            status_code=400,
            detail="Нет такой задачи" 
        )

    return {
        "task" : tasks_db[task_id - 1]
    }