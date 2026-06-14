from sqlalchemy.orm import Session
from app.models.tasks import Task
from app.models.tags import Tag
from app.schemas.tasks import TaskCreate, TaskUpdate

def get_all_tasks(db: Session, user_id: int, page: int = 1, size: int = 10, search: str = "", status: str = None):
    query = db.query(Task).filter(Task.user_id == user_id)

    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))

    if status:
        query = query.filter(Task.status == status)

    total = query.count()
    results = query.offset((page - 1) * size).limit(size).all()

    return {"total": total, "page": page, "size": size, "results": results}

def get_task_by_id(task_id: int, db: Session):
    return db.query(Task).filter(Task.id == task_id).first()

def _get_or_create_tags(db: Session, tag_names: list[str]) -> list[Tag]:
    tags = []
    for name in set(tag_names):
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        tags.append(tag)
    return tags

def create_task(task: TaskCreate, db: Session, user_id: int):
    new_task = Task(
        title=task.title,
        description=task.description,
        status=task.status,
        due_date=task.due_date,
        user_id=user_id
    )
    db.add(new_task)
    db.flush()

    if task.tags:
        tags = _get_or_create_tags(db, task.tags)
        new_task.tags = tags

    db.commit()
    db.refresh(new_task)
    return new_task

def update_task(task_id: int, task: TaskUpdate, db: Session):
    existing = get_task_by_id(task_id, db)

    if task.title is not None:
        existing.title = task.title
    if task.description is not None:
        existing.description = task.description
    if task.status is not None:
        existing.status = task.status
    if task.due_date is not None:
        existing.due_date = task.due_date

    if task.tags is not None:
        tags = _get_or_create_tags(db, task.tags)
        existing.tags = tags

    db.commit()
    db.refresh(existing)
    return existing

def delete_task(task_id: int, db: Session):
    existing = get_task_by_id(task_id, db)
    db.delete(existing)
    db.commit()