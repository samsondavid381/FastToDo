import streamlit as st
import requests
from datetime import datetime

# FastAPI backend URL
API_URL = "http://127.0.0.1:8000"

# Function to fetch tasks from the backend
def get_tasks():
    response = requests.get(f"{API_URL}/tasks/")
    if response.status_code == 200:
        return response.json()
    else:
        return []

# Function to create a new task
def create_task(title, description, due_date):
    task = {
        "title": title,
        "description": description,
        "due_date": due_date.isoformat() if due_date else None
    }
    response = requests.post(f"{API_URL}/tasks/", json=task)
    return response.status_code == 200

# Function to update a task
def update_task(task_id, title, description, due_date, completed):
    task = {
        "title": title,
        "description": description,
        "due_date": due_date.isoformat() if due_date else None,
        "completed": completed
    }
    response = requests.put(f"{API_URL}/tasks/{task_id}", json=task)
    return response.status_code == 200

# Function to delete a task
def delete_task(task_id):
    response = requests.delete(f"{API_URL}/tasks/{task_id}")
    return response.status_code == 200

# Streamlit UI
st.title("Intelligent To-Do List and Reminder System")

# Create Task
st.header("Create a New Task")
title = st.text_input("Title")
description = st.text_area("Description")
due_date = st.date_input("Due Date", datetime.now())

if st.button("Create Task"):
    if create_task(title, description, due_date):
        st.success("Task created successfully")
    else:
        st.error("Failed to create task")

st.write("---")

# List Tasks
st.header("Your Tasks")
tasks = get_tasks()
for task in tasks:
    st.subheader(task["title"])
    st.write(f"Description: {task['description']}")
    st.write(f"Due Date: {task['due_date']}")
    st.write(f"Completed: {task['completed']}")
    
    if st.button("Mark as Completed", key=f"complete_{task['id']}"):
        update_task(task["id"], task["title"], task["description"], task["due_date"], True)
    
    if st.button("Delete Task", key=f"delete_{task['id']}"):
        delete_task(task["id"])
    
    st.write("---")

