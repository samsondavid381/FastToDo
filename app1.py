import streamlit as st
import requests
import json
from datetime import datetime, date
import time
import hashlib
import colorsys

URL = "http://127.0.0.1:8000"

# Custom CSS to style the app
st.markdown("""
<style>
    .stApp {
    }
    .stButton>button {
        color:  #FFFFFF;
        background-color: #253237;
        border: 1px solid black;
        border-radius: 5px;
        padding: 5px 10px;
    }
    .task {
        background-color: #4472CA;
        color: #CFDEE7;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .task-complete {
        color: #5E7CE2;
    }
    .filter-section {
        background-color: #92B4F4;
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 10px;
        margin-right: 5px;
        font-size: 12px;
        background-color: #5E7CE2;
        color: #000000;
    }
    .tags-container {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
        margin-bottom: 5px;   
    }
</style>
""", unsafe_allow_html=True)
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

def generate_tag_colors(tags):
    colors = {}
    for tag in tags:
        hash_object = hashlib.md5(tag.encode())
        hash_hex = hash_object.hexdigest()
        hue = int(hash_hex[:8], 16) / 0xFFFFFFFF
        lightness = 0.7
        saturation = 0.5
        r, g, b = [int(x * 255) for x in colorsys.hls_to_rgb(hue, lightness, saturation)]
        colors[tag] = f"rgb({r}, {g}, {b})"
    return colors

st.sidebar.title("FastToDo")

with st.sidebar:
    st.header("Add New Task")
    new_task_title = st.text_input("Task Title")
    new_task_description = st.text_area("Task Description")
    new_task_due_date = st.date_input("Due Date")
    new_task_priority = st.selectbox("Priority", ["", "Low", "Medium", "High"])
    new_task_tags = st.text_input("Tags (comma-separated)")
    if st.button("📝 Add Task"):
        new_task = {
            "title": new_task_title,
            "description": new_task_description,
            "completed": False,
            "date_created": datetime.now().isoformat(),
            "due_date": new_task_due_date.isoformat(),
            "prio": new_task_priority.lower(),
            "tags": [tag.strip() for tag in new_task_tags.split(',') if tag.strip()]
        }
        result = create_task(new_task)
        if result:
            st.success("Task added successfully!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Failed to add task. Please try again.")

    st.markdown("---")
    st.header("Filter and Sort")

tasks = fetch_tasks()
all_tags = set()
for task in tasks:
    all_tags.update(task.get('tags', []))
tag_colors = generate_tag_colors(all_tags)

filter_tag = st.sidebar.selectbox("Filter by tag", ["All"] + list(all_tags))
sort_priority = st.sidebar.selectbox("Sort by priority", ["None", "High to Low", "Low to High"])


col1, col2 = st.columns([3, 3])


filtered_tasks = tasks if filter_tag == "All" else [task for task in tasks if filter_tag in task.get('tags', [])]
if 'update_mode' not in st.session_state:
    st.session_state.update_mode = {}

priority_order = {"high": 3, "medium": 2, "low": 1}
if sort_priority == "High to Low":
    filtered_tasks.sort(key=lambda x: priority_order.get(x.get('prio', '').lower(), 0), reverse=True)
elif sort_priority == "Low to High":
    filtered_tasks.sort(key=lambda x: priority_order.get(x.get('prio', '').lower(), 0))

def get_priority_emoji(priority):
    priority = priority.lower()
    if priority == "high":
        return "🔴"
    elif priority == "medium":
        return "🟡"
    elif priority == "low":
        return "🟢"
    else:
        return "🟢"

def display_task(task, is_complete):
    priority_emoji = get_priority_emoji(task.get('prio', ''))
    expander_title = f"{priority_emoji} {task['title']}"
    
    with st.expander(expander_title, expanded=False):
        st.markdown(f"**Description:** {task.get('suggested_rewriting', 'description')}")
        st.markdown(f"**Due Date:** {task.get('due_date', '')}")
        st.markdown(f"**Priority:** {task.get('prio', '').capitalize()}")
        st.markdown("**Tags:**")
        tag_html = '<div class="tags-container">'
        for tag in task.get('tags', []):
            tag_html += f'<span class="tag" style="background-color: {tag_colors[tag]};">{tag}</span>'
        tag_html += '</div>'
        st.markdown(tag_html, unsafe_allow_html=True)
        st.markdown(f"**Estimated Time:** {task.get('estimated_time', '')}")
        st.markdown(f"**Subtasks:**")
        for subtask in task.get('subtasks', []):
            st.markdown(f"- {subtask}")
        
        col1, col2 = st.columns(2)
        with col1:
            if is_complete:
                if st.button(f"😑 Uncomplete", key=f"updatebutton{task['id']}"):
                    task['completed'] = False
                    update_task(task['id'], task)
                    st.rerun()
            else:
                if st.button(f"💪 Complete",key=f"completebutton{task['id']}"):
                    task['completed'] = True
                    update_task(task['id'], task)
                    st.rerun()
        with col2:
            if is_complete:
                if st.button(f"💥 Delete",key=f"deletebutton{task['id']}"):
                    delete_task(task['id'])
                    st.rerun()
            else:
                if st.button(f"📄 Update", key=f"updatebut {task['id']}"):
                        st.session_state.update_mode[task['id']] = True
                if st.session_state.update_mode.get(task['id'], False):
                        task_title = st.text_input("New Title", value=task['title'], key=f"updatetitle {task['id']}")
                        task_description = st.text_area("New Description", value=task.get('description', ''), key=f"updatedesc {task['id']}")
                        task_due_date = st.date_input("New Due Date", value=datetime.fromisoformat(task['due_date']) if task['due_date'] else datetime.now(), key=f"updatedate {task['id']}")
                        task_priority = st.selectbox("Priority", ["", "Low", "Medium", "High"],key="updateselectprio")
                        task_tags = st.text_input("Tags (comma-separated)",key="updatetags")
                        
                        if st.button("Save", key=f"savebut {task['id']}"):
                            updated_task = {
                                "id": task['id'],
                                "title": task_title,
                                "description": task_description,
                                "completed": is_complete,
                                "date_created": task['date_created'],
                                "due_date": task_due_date.isoformat(),
                                "suggested_rewriting": task.get('suggested_rewriting', ''),
                                "estimated_time": task.get('estimated_time', ''),
                                "subtasks": task.get('subtasks', []),
                                "tags": [tag.strip() for tag in task_tags.split(',') if tag.strip()] if task_tags else task.get('tags',[]),
                                "prio": task_priority if task_priority else task.get('prio',"")
                            }
                            result = update_task(task['id'], updated_task)
                            if result:
                                st.success("Task updated successfully!")
                                st.session_state.update_mode[task['id']] = False
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to update task. Please try again.")

with col1:
    st.header("To Do")
    for task in filtered_tasks:
        if not task['completed']:
            display_task(task, False)

with col2:
    st.header("Complete")
    for task in filtered_tasks:
        if task['completed']:
            display_task(task, True)
