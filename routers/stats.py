from fastapi import APIRouter, HTTPException, status
from database import tasks_db

router = APIRouter(
    prefix="/stats",
    tags=["stats"],
    responses={404:{"description":"Task not found"}},
)

@router.get("/")
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