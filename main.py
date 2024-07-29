from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
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
    id: Optional[int] = None
    title: str
    description: Optional[str] = ""
    completed: bool = False
    date_created: datetime = Field(default_factory=datetime.now)
    due_date: Optional[date] = None
    estimated_time: Optional[str] = ""
    suggested_rewriting: Optional[str] = ""
    subtasks: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    prio: Optional[str] = ""

tasks: List[Task] = []

def anthropic_model(task_title: str, task_description: str) -> dict:
    try:
        with open('prompt.txt', 'r') as file:
            prompt = file.read().strip()
        prompt = prompt.replace("{TASK_TITLE}", task_title)
        prompt = prompt.replace("{TASK_DESCRIPTION}", task_description)
        
        response = completion(
            model="claude-3-5-sonnet-20240620",
            messages=[{"content": prompt, "role": "user"}],
        )
        content = response['choices'][0]['message']['content']
        parsed_content = json.loads(content)
        result = {
            "suggested_rewriting": parsed_content.get("suggested_rewriting", ""),
            "estimated_time": parsed_content.get("estimated_time", ""),
            "subtasks": parsed_content.get("subtasks", []),
            "tags": parsed_content.get("tags", []),
            "prioritization": parsed_content.get("prio", "")
        }
        return result
    except Exception as e:
        return {
            "suggested_rewriting": "",
            "estimated_time": "",
            "subtasks": [],
            "tags": [],
            "prioritization": ""
        }

@app.get("/tasks", response_model=List[Task])
def get_tasks():
    return tasks

@app.post("/tasks", response_model=Task)
def create_task(task: Task):
    try:
        task.id = len(tasks) + 1
        response = anthropic_model(task.title, task.description)
        # add AI response to task fields
        task.suggested_rewriting = response.get("suggested_rewriting", "")
        task.estimated_time = response.get("estimated_time", "")
        task.subtasks = response.get("subtasks", [])
        task.tags = response.get("tags", [])
        task.prio = response.get("prioritization", "")
        # append to list
        tasks.append(task)
        
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, updated_task: Task):
    for index, task in enumerate(tasks):
        if task.id == task_id:
            updated_task.id = task_id
            #rerun AI model if task was changed
            if updated_task.title != task.title or updated_task.description != task.description:
                response = anthropic_model(updated_task.title, updated_task.description)
                updated_task.suggested_rewriting = response.get("suggested_rewriting", "")
                updated_task.estimated_time = response.get("estimated_time", "")
                updated_task.subtasks = response.get("subtasks", [])
                updated_task.tags = response.get("tags", [])
                updated_task.prio = response.get("prioritization", "")
            # update
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