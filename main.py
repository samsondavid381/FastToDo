from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional
from datetime import datetime, date
import os
from litellm import completion
import json

app = FastAPI()

from dotenv import load_dotenv
load_dotenv()
os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")

class Task(BaseModel):
    id: Optional[int] = Field(None, description="Unique identifier for the task")
    title: str = Field(..., description="Title of the task")
    description: str = Field(..., description="Detailed description of the task")
    completed: bool = Field(False, description="Whether the task is completed or not")
    date_created: datetime = Field(default_factory=datetime.now, description="Date and time when the task was created")
    due_date: Optional[date] = Field(None, description="Due date for the task")
    suggested_rewriting: Optional[str] = Field(None, description="Suggested rewriting of the task description")
    estimated_time: Optional[str] = Field(None, description="Estimated time to complete the task")
    subtasks: List[str] = Field(default_factory=list, description="List of subtasks")
    tags: List[str] = Field(default_factory=list, description="List of tags associated with the task")
    prio: Optional[str] = Field(None, description="Priority level of the task")

def anthropic_model(task_title: str, task_description: str, task_prio: str, task_tags: List[str]) -> Task:
    try:
        with open('prompt.txt', 'r') as file:
            prompt = file.read().strip()
        
        tags_string = ','.join(task_tags)
        prompt = prompt.replace("{TASK_TITLE}", task_title)
        prompt = prompt.replace("{TASK_DESCRIPTION}", task_description)
        prompt = prompt.replace("{TASK_PRIO}", task_prio)
        prompt = prompt.replace("{TASK_TAGS}", tags_string)
        
        schema_txt = json.dumps(Task.model_json_schema())
        prompt += f"\n{schema_txt}"
        
        response = completion(
            model="claude-3-5-sonnet-20240620",
            messages=[{"content": prompt, "role": "user"}],
        )
        content = response['choices'][0]['message']['content']
        
        task_data = json.loads(content)

        return Task(**task_data)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Invalid data structure: {e}")
    except Exception as e:
        print(f"Error in anthropic_model: {e}")
        return Task(
            title=task_title,
            description=task_description,
            suggested_rewriting=None,
            estimated_time=None,
            subtasks=[],
            tags=task_tags,
            prio=task_prio
        )
tasks: List[Task] = []
@app.get("/tasks", response_model=List[Task])
def get_tasks():
    return tasks

@app.post("/tasks", response_model=Task)
def create_task(task: Task):
    try:
        task.id = len(tasks) + 1
        ai_task = anthropic_model(task.title, task.description, task.prio or "", task.tags)
        
        if ai_task.suggested_rewriting is not None:
            task.suggested_rewriting = ai_task.suggested_rewriting
        if ai_task.estimated_time is not None:
            task.estimated_time = ai_task.estimated_time
        if ai_task.subtasks:
            task.subtasks = ai_task.subtasks
        if ai_task.tags:
            task.tags = ai_task.tags
        if ai_task.prio is not None:
            task.prio = ai_task.prio
        
        tasks.append(task)
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, updated_task: Task):
    for index, task in enumerate(tasks):
        if task.id == task_id:
            updated_task.id = task_id
            if updated_task.title != task.title or updated_task.description != task.description:
                ai_task = anthropic_model(updated_task.title, updated_task.description, updated_task.prio or "", updated_task.tags)
                if ai_task.suggested_rewriting is not None:
                    updated_task.suggested_rewriting = ai_task.suggested_rewriting
                if ai_task.estimated_time is not None:
                    updated_task.estimated_time = ai_task.estimated_time
                if ai_task.subtasks:
                    updated_task.subtasks = ai_task.subtasks
                if ai_task.tags:
                    updated_task.tags = ai_task.tags
                if ai_task.prio is not None:
                    updated_task.prio = ai_task.prio
            
            tasks[index] = updated_task
            return updated_task
    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    for index, task in enumerate(tasks):
        if task.id == task_id:
            del tasks[index]
            return {"message": "Task deleted successfully"}
    raise HTTPException(status_code=404, detail="Task not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)