from typing import Optional
from datetime import date
from pydantic import BaseModel, Field
from app.models.tasks import TaskStatus

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.todo
    due_date: Optional[date] = None
    tags: list[str] = []

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[date] = None
    tags: Optional[list[str]] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    due_date: Optional[date]
    user_id: int
    tags: list[str] = []

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        # Convert SQLAlchemy Task object to dict, handling tags relationship
        data = {
            "id": obj.id,
            "title": obj.title,
            "description": obj.description,
            "status": obj.status,
            "due_date": obj.due_date,
            "user_id": obj.user_id,
            "tags": [tag.name for tag in obj.tags] if obj.tags else []
        }
        return cls(**data)