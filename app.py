import streamlit as st
import requests
import json
from datetime import datetime, date
import time

URL = "http://127.0.0.1:8000"
def date_time_encoder(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def fetch_tasks():
    response = requests.get(f"{URL}/tasks")
    return response.json()

def create_task(task):
    task_json = json.dumps(task, default=date_time_encoder)
    response = requests.post(f"{URL}/tasks", data=task_json, headers={'Content-Type': 'application/json'})
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error creating task. Status code: {response.status_code}")
        st.error(f"Response content: {response.text}")
        return None

def update_task(task_id, task):
    task_json = json.dumps(task, default=date_time_encoder)
    response = requests.put(f"{URL}/tasks/{task_id}", data=task_json, headers={'Content-Type': 'application/json'})
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error updating task. Status code: {response.status_code}")
        st.error(f"Response content: {response.text}")
        return None

def delete_task(task_id):
    response = requests.delete(f"{URL}/tasks/{task_id}")
    return response.json()


st.title("To-Do List App")

# view tasks
st.header("Your Tasks")
tasks = fetch_tasks()

if 'update_mode' not in st.session_state:
    st.session_state.update_mode = {}

for task in tasks:
    task_class = "completed-task" if task['completed'] else ""
    expander_text = f"{task['title']} | Completed" if task['completed'] else f"{task['title']}"
    with st.expander(expander_text, expanded=False) as task_expander:
        st.write(f"Description: {task.get('description', '')}")
        st.write(f"Suggested Rewriting: {task.get('suggested_rewriting', '')}")
        st.write(f"Estimated Time: {task.get('estimated_time', '')}")
        st.write("Subtasks:")
        for subtask in task.get('subtasks', []):
            st.write(f"- {subtask}")
        st.write(f"Tags: {', '.join(task.get('tags', []))}")
        st.write(f"Priority: {task.get('prio', '')}")
        task_completed = st.checkbox("Completed", value=task['completed'], key=f"completed {task['id']}")
        st.write(f"Due Date: {task.get('due_date', '')}")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button(f"Update", key=f"updatebut {task['id']}"):
                st.session_state.update_mode[task['id']] = True

            if st.session_state.update_mode.get(task['id'], False):
                task_title = st.text_input("New Title", value=task['title'], key=f"title {task['id']}")
                task_description = st.text_area("New Description", value=task.get('description', ''), key=f"desc {task['id']}")
                task_due_date = st.date_input("New Due Date", value=datetime.fromisoformat(task['due_date']) if task['due_date'] else datetime.now(), key=f"date {task['id']}")

                if st.button("Save", key=f"savebut {task['id']}"):
                    updated_task = {
                        "id": task['id'],
                        "title": task_title,
                        "description": task_description,
                        "completed": task_completed,
                        "date_created": task['date_created'],
                        "due_date": task_due_date.isoformat(),
                        "suggested_rewriting": task.get('suggested_rewriting', ''),
                        "estimated_time": task.get('estimated_time', ''),
                        "subtasks": task.get('subtasks', []),
                        "tags": task.get('tags', []),
                        "prio": task.get('prio', '')
                    }
                    result = update_task(task['id'], updated_task)
                    if result:
                        st.success("Task updated successfully!")
                        st.session_state.update_mode[task['id']] = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to update task. Please try again.")
        with col2:
            if st.button(f"Delete", key=f"deletebut {task['id']}"):
                delete_task(task['id'])
                st.rerun()
                
#initialize add task values
if 'task_title' not in st.session_state:
    st.session_state.task_title = ""
if 'task_description' not in st.session_state:
    st.session_state.task_description = ""
if 'task_due_date' not in st.session_state:
    st.session_state.task_due_date = datetime.now()

st.sidebar.header("Add a New Task")
task_title = st.sidebar.text_input("Title")
task_description = st.sidebar.text_area("Description")
task_due_date = st.sidebar.date_input("Due Date", value=st.session_state.task_due_date)

if st.sidebar.button("Add Task"):
    new_task = {
        "title": task_title,
        "description": task_description,
        "completed": False,
        "date_created": datetime.now().isoformat(),
        "due_date": task_due_date.isoformat(),
    }
    result = create_task(new_task)
    if result:
        st.sidebar.success("Task added successfully!")
        st.rerun()
    else:
        st.sidebar.error("Failed to add task. Please try again.")