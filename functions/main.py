# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_admin import db


from firebase_functions import https_fn
from firebase_admin import initialize_app, credentials
import os
import json
from datetime import datetime

import pytz

credential_path = "lamatodo-be-1e97f3e1a9d8.json"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path


cred = credentials.ApplicationDefault()


initialize_app(cred, {
    'databaseURL': 'https://lamatodo-be-default-rtdb.firebaseio.com/'
})

ref = db.reference('tasks')

#

FAKE_UID = "123456"  # Replace with your fake UID
TIMEZONE_USER = 'Europe/Berlin'




@https_fn.on_request()
def getCurrentDate(req: https_fn.Request) -> https_fn.Response:
    # Get the current date and time
    now = datetime.now()

    # Convert to the user's timezone
    user_tz = pytz.timezone(TIMEZONE_USER)
    now_user_tz = now.astimezone(user_tz)

    # Return the date in ISO 8601 format
    return https_fn.Response(now_user_tz.isoformat())

@https_fn.on_request()
def addTask(req: https_fn.Request) -> https_fn.Response:
    task = req.get_json().get('task', None)
    priority = req.get_json().get('priority', None)
    date_str = req.get_json().get('date', None)
    label = req.get_json().get('label', None)
    subtasks = req.get_json().get('subtasks', None)

    # subtasks is a string seperated by ;   
    subtasks = subtasks.split(";")

    if task is None:
        return https_fn.Response("No task provided", status=400)

    if date_str is not None:
        try:
            # Parse the date string into a datetime object
            date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            return https_fn.Response("Invalid date format", status=400)
    else:
        date = None

    # Create a reference to the user's tasks in the database
    user_tasks_ref = ref.child(FAKE_UID)

    # Push a new task to the user's tasks
    new_task_ref = user_tasks_ref.push()
    new_task_ref.set({
        'task': task,
        'priority': priority,
        'date': date.isoformat() if date else None,
        'label': label,
        'subtasks': subtasks
    })

    # Return the ID of the new task
    return https_fn.Response(new_task_ref.key)


@https_fn.on_request()
def editTask(req: https_fn.Request) -> https_fn.Response:
    task_id = req.get_json().get('task_id', None)
    new_task = req.get_json().get('task', None)
    new_priority = req.get_json().get('priority', None)
    date_str = req.get_json().get('date', None)
    label = req.get_json().get('label', None)
    subtasks = req.get_json().get('subtasks', None)

    # subtasks is a string seperated by ;   
    subtasks = subtasks.split(";")

    if task_id is None or new_task is None:
        return https_fn.Response("Task ID or new task details not provided", status=400)

    if date_str is not None:
        try:
            # Parse the date string into a datetime object
            date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            return https_fn.Response("Invalid date format", status=400)
    else:
        date = None

    # Create a reference to the specific task in the database
    task_ref = ref.child(FAKE_UID).child(task_id)

    # Update the task details
    task_ref.update({
        'task': new_task,
        'priority': new_priority,
        'date': date.isoformat() if date else None,
        'label': label,
        'subtasks': subtasks
    })

    return https_fn.Response("Task updated successfully")


@https_fn.on_request()
def getTasks(req: https_fn.Request) -> https_fn.Response:
    # Create a reference to the user's tasks in the database
    user_tasks_ref = ref.child(FAKE_UID)

    # Get all tasks
    tasks = user_tasks_ref.get()

    return https_fn.Response(json.dumps(tasks), mimetype='application/json')

@https_fn.on_request()
def removeTask(req: https_fn.Request) -> https_fn.Response:
    task_id = req.get_json().get('task_id', None)

    if task_id is None:
        return https_fn.Response("Task ID not provided", status=400)

    # Create a reference to the specific task in the database
    task_ref = ref.child(FAKE_UID).child(task_id)

    # Remove the task
    task_ref.delete()

    return https_fn.Response("Task removed successfully")