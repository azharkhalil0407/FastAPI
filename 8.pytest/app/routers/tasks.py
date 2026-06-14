from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.crud.tasks import create_task, delete_task, get_all_tasks, get_task_by_id, update_task
from app.dependencies import get_db
from app.schemas.tasks import TaskCreate, TaskResponse, TaskUpdate
from app.utils import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/", response_model=dict)
def list_tasks(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    search: str = Query(default=""),
    status: str = Query(default=None)
):
    data = get_all_tasks(db, current_user.id, page, size, search, status)
    return {
        "total": data["total"],
        "page": data["page"],
        "size": data["size"],
        "results": [TaskResponse.model_validate(t) for t in data["results"]]
    }

@router.get("/{task_id}", response_model=TaskResponse)
def fetch_task(task_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    task = get_task_by_id(task_id, db)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return task

@router.post("/", status_code=201, response_model=TaskResponse)
def add_task(task: TaskCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return create_task(task, db, current_user.id)

@router.put("/{task_id}", response_model=TaskResponse)
def edit_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    existing = get_task_by_id(task_id, db)
    if existing is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if existing.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return update_task(task_id, task, db)

@router.delete("/{task_id}")
def remove_task(task_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    existing = get_task_by_id(task_id, db)
    if existing is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if existing.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    delete_task(task_id, db)
    return {"message": "Task deleted"}