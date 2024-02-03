# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_admin import db


from firebase_functions import https_fn,options
from firebase_admin import initialize_app, credentials
import os
import json
from datetime import datetime

import pytz

from src.parser import parse_subtasks, parse_date, parse_recurring_task

from src.kpiTracking import KpiTracking
import secrets

import urllib
from urllib.parse import parse_qs



from flask import Flask
app = Flask(__name__)


credential_path = "lamatodo-be-1e97f3e1a9d8.json"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path


cred = credentials.ApplicationDefault()


initialize_app(cred, {
    'databaseURL': 'https://lamatodo-be-default-rtdb.firebaseio.com/'
})

ref = db.reference('user_data')
ref_tasks = ref.child('tasks')
ref_user_auth = db.reference('user_auth')
ref_test = db.reference('test')
ref_log = db.reference('log')
# ref = db.reference('tasks')

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
    title = req.get_json().get('title', None)
    description = req.get_json().get('description', None)
    priority = req.get_json().get('priority', None)
    label = req.get_json().get('label', None)
    recurring_task = parse_recurring_task(req.get_json().get('recurring_task', None))
    subtasks = parse_subtasks(req.get_json().get('subtasks', None))
    project_id = req.get_json().get('project_id', None)
    try:
        date = parse_date(req.get_json().get('date', None))
    except ValueError as e:
        return https_fn.Response(str(e), status=400)

    if title is None:
        return https_fn.Response("No task provided", status=400)

    if project_id is None:
        return https_fn.Response("No project_id provided", status=400)

    # Create a reference to the user's tasks in the database
    # user_tasks_ref = ref_tasks.child(FAKE_UID)
    user_tasks_ref = ref_tasks

    # Push a new task to the user's tasks
    new_task_ref = user_tasks_ref.push()
    new_task = {
        'title': title,
        'description': description,
        "done": "false",
        'priority': priority,
        'label': label,
        'recurring_task': recurring_task,
        'subtasks': subtasks,
        'date': date,
        'project_id': project_id,
        'created_time': datetime.now().isoformat(),  # Add the created_time
        'last_activity': datetime.now().isoformat()  # Add the last_activity


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
    # task_ref = ref.child(FAKE_UID).child(task_id)
    task_ref = ref_tasks.child(task_id)

    # Get the fields to be updated
    fields_to_update = {}
    for field in ['title', 'desciption', 'done', 'priority', 'label', 'recurring_task', 'subtasks', 'date', 'project_id']:
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

    fields_to_update['edit_time'] = datetime.now().isoformat()
    fields_to_update['last_activity'] = datetime.now().isoformat()  # Add the last_activity


    # Update the task details
    task_ref.update(fields_to_update)

    # Return a success response
    return https_fn.Response(json.dumps(fields_to_update), status=200, mimetype='application/json')

@https_fn.on_request()
def getTasks(req: https_fn.Request) -> https_fn.Response:
    data = req.get_json()
    project_id = data.get('project_id', None)

    if project_id is None:
        return https_fn.Response("Project ID is required", status=400)

    # Create a reference to the user's tasks in the database
    tasks_ref = ref_tasks

    # Get tasks where the project_id is exactly equal to the provided project_id
    project_tasks = tasks_ref.order_by_child('project_id').equal_to(project_id).get()

    return https_fn.Response(json.dumps(project_tasks), mimetype='application/json')

@https_fn.on_request()
def removeTask(req: https_fn.Request) -> https_fn.Response:
    task_id = req.get_json().get('task_id', None)

    if task_id is None:
        return https_fn.Response("Task ID not provided", status=400)

    # Create a reference to the specific task in the database
    # task_ref = ref.child(FAKE_UID).child(task_id)
    task_ref = ref_tasks.child(task_id)

    # Remove the task
    task_ref.delete()

    return https_fn.Response("Task removed successfully")


@https_fn.on_request()
def addProject(req: https_fn.Request) -> https_fn.Response:
    data = req.get_json()

    # Check if name and user_id are provided
    if 'name' not in data or 'user_id' not in data:
        return https_fn.Response("Both name and user_id are required", status=400)

    # Create a reference to the projects in the database
    projects_ref = ref.child('projects')

    # Add the new project
    new_project_ref = projects_ref.push({
        'name': data['name'],
        'user_id': data['user_id']
    })

    return https_fn.Response(f"project_id: {new_project_ref.key}")


@https_fn.on_request()
def getProjects(req: https_fn.Request) -> https_fn.Response:
    # Extract user_id from the request data
    data = req.get_json()
    user_id = data.get('user_id')

    # Check if user_id is provided
    if not user_id:
        return https_fn.Response("no user_id provided", status=400)

    # Create a reference to the projects in the database
    projects_ref = ref.child('projects')

    # Get all projects of a given user_id
    user_projects = projects_ref.order_by_child('user_id').equal_to(user_id).get()

    # If the user has no projects, create a default one
    if not user_projects:
        default_project = {
            "name": "My Project",
            "user_id": user_id
        }
        projects_ref.push(default_project)
        user_projects = projects_ref.order_by_child('user_id').equal_to(user_id).get()

    return https_fn.Response(json.dumps(user_projects), mimetype='application/json')


@https_fn.on_request()
def auth(req: https_fn.Request) -> https_fn.Response:
    access_token = secrets.token_hex(16)  # 32 characters long token
    auth_code = secrets.token_hex(16)  # 32 characters long token
    data = req.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return https_fn.Response({
            'status': 'error',
            'message': 'Missing email or password'
        }, mimetype='application/json')

    user_auth_ref = ref_user_auth.order_by_child('email').equal_to(email).get()

    if not user_auth_ref:
        now = datetime.now()
        new_user = ref_user_auth.push({
            'email': email,
            'password': password,  # In a real-world application, never store passwords in plain text
            'registration_date': now.isoformat(),
            'access_token': access_token,
            'auth_code': auth_code
        })
        return https_fn.Response(json.dumps({
            'status': 'new_user',
            'user_id': new_user.key,
            'auth_code': auth_code  # return auth_code on successful registration
        }), mimetype='application/json')
    else:
        for user_id, user_info in user_auth_ref.items():
            if user_info['password'] == password:
                return https_fn.Response(json.dumps({
                    'status': 'login_success',
                    'user_id': user_id,
                    'auth_code': user_info['auth_code']  # return auth_code on successful login
                }), mimetype='application/json')
            else:
                return https_fn.Response(json.dumps({
                    'status': 'wrong_password'
                }), mimetype='application/json')
                

@https_fn.on_request(cors=options.CorsOptions(cors_origins="*", cors_methods=["get", "post"]))
def token(req: https_fn.Request) -> https_fn.Response:
    timestamp = datetime.now().isoformat()

    debug_token = {
        "access_token": "a15aeb28c5494e7d945087f2d6681754",
        "token_type": "bearer"
    }

    if req.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
        # Parse the body of the request and store it in a variable
        body = parse_qs(req.get_data(as_text=True))
        request_data_keys = ', '.join(body.keys()) if body.keys() else "empty"
        ref_log.push({
            "timestamp": timestamp,
            "request_keys_strint": body,
            "request_data_keys": request_data_keys,
        })
        obj = {
            "access_token": "a15aeb28c5494e7d945087f2d6681754",
            "token_type": "bearer",
            "status": "is x-form"
        }
        return https_fn.Response(json.dumps(obj), mimetype='application/json')


    request_keys_strint  = ', '.join(req.keys()) if req.keys() else "empty"
    ref_log.push({
        "timestamp": timestamp,
        "request_keys_strint": request_keys_strint
    })

    request_type = req.method
    request_headers = dict(req.headers)

    requ_data_keys = ', '.join(req.args.keys()) if req.args.keys() else "empty"

    ref_log.push({
        "timestamp": timestamp,
        "request_type": request_type,
        "headers": request_headers,
        # "data" : data,
        "data" : "jojo",
        "request_params" : req.args,
        "request_data_keys" : requ_data_keys,
        # "request_body" : req.data,

        # "data" : data

    })

    # rest of your code
    return https_fn.Response(json.dumps(debug_token), mimetype='application/json')

    data = req.get_json()
    ref_test.set(data)
    code = data.get('code')
    # Query ref_user_auth for a user with the provided auth_code
    user_auth = ref_user_auth.order_by_child('auth_code').equal_to(code).get()

    # Check if the query returned any results
    if not user_auth:
        # Store the request data in ref_test
        ref_test.set(data)
        return https_fn.Response(json.dumps({'message': 'Unauthorized','code':code}), status=401, mimetype='application/json')

    # Get the first record from user_auth
    first_record_key = next(iter(user_auth))
    user_record = user_auth[first_record_key]
    access_token = user_record['access_token']

    # Updated data
    token_data = {
        'access_token': access_token,
        'token_type': 'bearer',
    }

    return https_fn.Response(json.dumps(token_data), mimetype='application/json')

@https_fn.on_request()
def getUsers(req: https_fn.Request) -> https_fn.Response:
    # Query ref_user_auth for all users
    all_users = ref_user_auth.get()

    # Return all users in the response
    return https_fn.Response(json.dumps(all_users), mimetype='application/json')


@https_fn.on_request()
def getKpis(req: https_fn.Request) -> https_fn.Response:
    refs = {
        'tasks': ref_tasks,
        'user_auth': ref_user_auth
    }

    kpi = KpiTracking(refs)
    kpis = {
        'registrations_last_day': kpi.registrations_last_day(),
        'registrations_last_7_days': kpi.registrations_last_7_days(),
        'active_users_last_day': kpi.active_users_last_day(),
        'active_users_last_7_days': kpi.active_users_last_7_days(),
        'average_tasks_per_user': kpi.average_tasks_per_user(),
        'median_tasks_per_user': kpi.median_tasks_per_user()
        # 'tutorial_completion_rate': kpi.tutorial_completion_rate()
    }

    print("----------------------jaösdlkfjaösldkfjaösldfkjaösldkfjaösdklfjasd----------------------")

    return https_fn.Response(json.dumps(kpis), mimetype='application/json')


# if __name__ == "__main__":
#     # Replace 'your_function' with the actual function you want to test
#     getKpis({})

