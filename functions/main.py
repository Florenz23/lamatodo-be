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

from src.parser import parse_subtasks, parse_date, parse_recurring_task


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

    # Get the current weekday
    weekday = now_user_tz.strftime('%A')

    # Prepare the response data
    response_data = {
        'date': now_user_tz.isoformat(),
        'weekday': weekday
    }

    # Return the date and weekday in JSON format
    return https_fn.Response(json.dumps(response_data), status=200, mimetype='application/json')

@https_fn.on_request()
def addTask(req: https_fn.Request) -> https_fn.Response:
    task = req.get_json().get('task', None)
    priority = req.get_json().get('priority', None)
    label = req.get_json().get('label', None)
    recurring_task = parse_recurring_task(req.get_json().get('recurring_task', None))
    subtasks = parse_subtasks(req.get_json().get('subtasks', None))
    try:
        date = parse_date(req.get_json().get('date', None))
    except ValueError as e:
        return https_fn.Response(str(e), status=400)

    if task is None:
        return https_fn.Response("No task provided", status=400)

    # Create a reference to the user's tasks in the database
    user_tasks_ref = ref.child(FAKE_UID)

    # Push a new task to the user's tasks
    new_task_ref = user_tasks_ref.push()
    new_task = {
        'task': task,
        "done": "false",
        'priority': priority,
        'label': label,
        'recurring_task': recurring_task,
        'subtasks': subtasks,
        'date': date,
    }
    new_task_ref.set(new_task)

    # Get the task ID and add it to the task dictionary
    new_task['task_id'] = new_task_ref.key

    # Return the new task as a JSON response
    return https_fn.Response(json.dumps(new_task), headers={'Content-Type': 'application/json'})


@https_fn.on_request()
def editTask(req: https_fn.Request) -> https_fn.Response:
    task_id = req.get_json().get('task_id', None)

    if task_id is None:
        return https_fn.Response("Task ID not provided", status=400)

    # Create a reference to the specific task in the database
    task_ref = ref.child(FAKE_UID).child(task_id)

    # Get the fields to be updated
    fields_to_update = {}
    for field in ['task', 'done', 'priority', 'label', 'recurring_task', 'subtasks', 'date']:
        if field in req.get_json():
            if field == 'recurring_task':
                fields_to_update[field] = parse_recurring_task(req.get_json().get(field))
            elif field == 'subtasks':
                fields_to_update[field] = parse_subtasks(req.get_json().get(field))
            elif field == 'date':
                try:
                    fields_to_update[field] = parse_date(req.get_json().get(field))
                except ValueError as e:
                    return https_fn.Response(str(e), status=400)
            else:
                fields_to_update[field] = req.get_json().get(field)

    # Update the task details
    task_ref.update(fields_to_update)

    # Return a success response
    return https_fn.Response(json.dumps(fields_to_update), status=200, mimetype='application/json')


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