# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_admin import db


from firebase_functions import https_fn
from firebase_admin import initialize_app, credentials
import os
import json

credential_path = "lamatodo-be-1e97f3e1a9d8.json"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path


cred = credentials.ApplicationDefault()


initialize_app(cred, {
    'databaseURL': 'https://lamatodo-be-default-rtdb.firebaseio.com/'
})

ref = db.reference('tasks')

#

FAKE_UID = "123456"  # Replace with your fake UID

@https_fn.on_request()
def addTask(req: https_fn.Request) -> https_fn.Response:
    task = req.get_json().get('task', None)
    priority = req.get_json().get('priority', None)
    if task is None:
        return https_fn.Response("No task provided", status=400)

    # Create a reference to the user's tasks in the database
    user_tasks_ref = ref.child(FAKE_UID)

    # Push a new task to the user's tasks
    new_task_ref = user_tasks_ref.push()
    new_task_ref.set({
        'task': task,
        'priority': priority
    })

    return https_fn.Response("Task added successfully")


@https_fn.on_request()
def getTasks(req: https_fn.Request) -> https_fn.Response:
    # Create a reference to the user's tasks in the database
    user_tasks_ref = ref.child(FAKE_UID)

    # Get all tasks
    tasks = user_tasks_ref.get()

    return https_fn.Response(json.dumps(tasks), mimetype='application/json')