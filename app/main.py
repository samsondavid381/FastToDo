from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

app = FastAPI()

class Task(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    completed: bool = False
    date_created: datetime
    due_date: Optional[datetime] = None

tasks = []

@app.get("/tasks", response_model=List[Task])
def get_tasks():
    return tasks

@app.post("/tasks", response_model=Task)
def create_task(task: Task):
    tasks.append(task)
    return task

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, updated_task: Task):
    for task in tasks:
        if task.id == task_id:
            task.title = updated_task.title
            task.description = updated_task.description
            task.completed = updated_task.completed
            task.date_created = updated_task.date_created
            task.due_date = updated_task.due_date
            return task
    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    for task in tasks:
        if task.id == task_id:
            tasks.remove(task)
            return {"message": "Task deleted successfully"}
    raise HTTPException(status_code=404, detail="Task not found")
