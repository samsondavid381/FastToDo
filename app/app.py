import streamlit as st
import requests
from datetime import datetime

URL = "http://127.0.0.1:8000"

def fetch_tasks():
    response = requests.get(f"{URL}/tasks")
    return response.json()

def create_task(task):
    response = requests.post(f"{URL}/tasks", json=task)
    return response.json()

def update_task(task_id, task):
    response = requests.put(f"{URL}/tasks/{task_id}", json=task)
    return response.json()

def delete_task(task_id):
    response = requests.delete(f"{URL}/tasks/{task_id}")
    return response.json()

st.title("To-Do List App")

# View Tasks
st.header("Your Tasks")
tasks = fetch_tasks()

if 'update_mode' not in st.session_state:
    st.session_state.update_mode = {}

for task in tasks:
    task_expander = st.expander(f"{task['title']}")
    task.setdefault('completed', False)
    task.setdefault('date_created', datetime.now().date())
    task.setdefault('due_date', None)
    with task_expander:
        st.write(task.get('description', ''))
        st.write('Due Date: ' + task.get('due_date'))
        task_completed = st.checkbox("Completed", value=task['completed'], key=f"completed_{task['id']}")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button(f"Update", key=f"update_{task['id']}"):
                st.session_state.update_mode[task['id']] = True

            if st.session_state.update_mode.get(task['id'], False):
                task_title = st.text_input("New Title", value=task['title'], key=f"title_{task['id']}")
                task_description = st.text_area("New Description", value=task.get('description', ''), key=f"desc_{task['id']}")
                task_due_date = st.date_input("New Due Date", value=datetime.fromisoformat(task['due_date']) if task['due_date'] else datetime.now(), key=f"due_date_{task['id']}")
                if st.button("Save", key=f"save_{task['id']}"):
                    updated_task = {
                        "id": task['id'],
                        "title": task_title,
                        "description": task_description,
                        "completed": task_completed,
                        "date_created": task['date_created'],
                        "due_date": task_due_date.isoformat()
                    }
                    update_task(task['id'], updated_task)
                    st.session_state.update_mode[task['id']] = False
                    st.rerun()
        with col2:
            if st.button(f"Delete", key=f"delete_{task['id']}"):
                delete_task(task['id'])
                st.rerun()

# Adding a New Task
st.sidebar.header("Add a New Task")
task_title = st.sidebar.text_input("Title")
task_description = st.sidebar.text_area("Description")
task_due_date = st.sidebar.date_input("Due Date", value=datetime.now())
if st.sidebar.button("Add Task"):
    new_task = {
        "id": len(fetch_tasks()) + 1,
        "title": task_title,
        "description": task_description,
        "completed": False,
        "date_created": datetime.now().isoformat(),
        "due_date": task_due_date.isoformat()
    }
    create_task(new_task)
    st.sidebar.success("Task added successfully!")
    st.rerun()
