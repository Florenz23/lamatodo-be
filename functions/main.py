from firebase_admin import credentials, initialize_app, db
from firebase_functions import https_fn

from flask import Flask, request, jsonify
from datetime import datetime
import pytz
import os
from flask import Flask, request, jsonify
import os
from datetime import datetime
import pytz
import secrets
from urllib.parse import parse_qs

from firebase_admin import credentials, initialize_app, db
from src.parser import parse_subtasks, parse_date, parse_recurring_task
from src.kpiTracking import KpiTracking
from src.parser import parse_subtasks, parse_date, parse_recurring_task


app = Flask(__name__)

# Initialize Firebase Admin
credential_path = "lamatodo-be-1e97f3e1a9d8.json"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path
cred = credentials.ApplicationDefault()
initialize_app(cred, {'databaseURL': 'https://lamatodo-be-default-rtdb.firebaseio.com/'})

# Firebase database references
ref = db.reference('user_data')
ref_tasks = ref.child('tasks')
ref_user_auth = db.reference('user_auth')
TIMEZONE_USER = 'Europe/Berlin'

@app.route('/getCurrentDate', methods=['GET'])
def get_current_date():
    now = datetime.now(pytz.timezone(TIMEZONE_USER))
    response_data = {
        'date': now.isoformat(),
        'weekday': now.strftime('%A')
    }
    return jsonify(response_data), 200

@app.route('/getTasks', methods=['POST'])
def get_tasks():
    data = request.get_json()
    project_id = data.get('project_id')
    if not project_id:
        return jsonify({"error": "Project ID is required"}), 400

    project_tasks = ref_tasks.order_by_child('project_id').equal_to(project_id).get()
    if project_tasks:
        return jsonify(project_tasks), 200
    else:
        return jsonify({"message": "No tasks found for the provided project_id"}), 404

@app.route('/addTask', methods=['POST'])
def add_task():
    req_data = request.json
    title = req_data.get('title')
    if title is None:
        return jsonify({"error": "No task provided"}), 400

    project_id = req_data.get('project_id')
    if project_id is None:
        return jsonify({"error": "No project_id provided"}), 400

    new_task = {
        'title': title,
        'description': req_data.get('description'),
        "done": "false",
        'priority': req_data.get('priority'),
        'label': req_data.get('label'),
        'recurring_task': req_data.get('recurring_task'),
        'subtasks': req_data.get('subtasks'),
        'date': parse_date(req_data.get('date')),
        'project_id': project_id,
        'created_time': datetime.now().isoformat(),
        'last_activity': datetime.now().isoformat()
    }
    
    new_task_ref = ref_tasks.push(new_task)
    new_task['task_id'] = new_task_ref.key
    return jsonify(new_task), 201


@app.route('/editTask', methods=['POST'])
def edit_task():
    req_data = request.json

    if not req_data:
        return jsonify({"error": "No data provided"}), 400

    task_id = req_data.get('task_id', None)
    if task_id is None:
        return jsonify({"error": "Task ID not provided"}), 400

    task_ref = ref_tasks.child(task_id)

    fields_to_update = {}
    for field in ['title', 'description', 'done', 'priority', 'label', 'recurring_task', 'subtasks', 'date', 'project_id']:
        if field in req_data:
            if field == 'recurring_task':
                fields_to_update[field] = req_data.get('recurring_task')
            elif field == 'subtasks':
                fields_to_update[field] = req_data.get('subtasks')
            elif field == 'date':
                try:
                    fields_to_update[field] = parse_date(req_data.get(field))
                except ValueError as e:
                    return jsonify({"error": str(e)}), 400
            else:
                fields_to_update[field] = req_data.get(field)

    fields_to_update['edit_time'] = datetime.now().isoformat()
    fields_to_update['last_activity'] = datetime.now().isoformat()

    task_ref.update(fields_to_update)

    return jsonify(fields_to_update), 200

@app.route('/removeTask', methods=['POST'])
def remove_task():
    data = request.json
    task_id = data.get('task_id')
    if task_id:
        ref_tasks.child(task_id).delete()
        return jsonify({"success": True, "message": "Task removed successfully", "task_id": task_id}), 200
    else:
        return jsonify({"success": False, "message": "No task_id provided"}), 400

# Additional routes for other functionalities can be added similarly.

@app.route('/addProject', methods=['POST'])
def add_project():
    data = request.json
    if 'name' not in data or 'user_id' not in data:
        return jsonify({"error": "Both name and user_id are required"}), 400

    projects_ref = ref.child('projects')
    new_project_ref = projects_ref.push({
        'name': data['name'],
        'user_id': data['user_id']
    })
    return jsonify({"project_id": new_project_ref.key}), 201

@app.route('/getProjects', methods=['GET'])
def get_projects():
    authorization_header = request.headers.get('Authorization')
    if not authorization_header:
        return jsonify({"error": "Authorization header is missing"}), 401

    access_token = authorization_header.split('Bearer ')[-1]
    user_auth = ref_user_auth.order_by_child('access_token').equal_to(access_token).get()
    if not user_auth:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = next(iter(user_auth))
    user_projects = ref.child('projects').order_by_child('user_id').equal_to(user_id).get()
    return jsonify(user_projects), 200

@app.route('/auth', methods=['POST'])
def auth():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    user_auth_ref = ref_user_auth.order_by_child('email').equal_to(email).get()
    if not user_auth_ref:
        access_token, auth_code = secrets.token_hex(16), secrets.token_hex(16)
        new_user = ref_user_auth.push({
            'email': email,
            'password': password,
            'registration_date': datetime.now().isoformat(),
            'access_token': access_token,
            'auth_code': auth_code
        })
        return jsonify({
            'status': 'new_user',
            'user_id': new_user.key,
            'auth_code': auth_code
        }), 201

    for user_id, user_info in user_auth_ref.items():
        if user_info['password'] == password:
            return jsonify({
                'status': 'login_success',
                'user_id': user_id,
                'auth_code': user_info['auth_code']
            }), 200
    return jsonify({"error": "Wrong password"}), 401

@app.route('/token', methods=['POST'])
def token():
    if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
        body = parse_qs(request.get_data(as_text=True))
        auth_code = body.get('code', [None])[0]
    else:
        return jsonify({"error": "Unsupported Content-Type"}), 400

    user_auth = ref_user_auth.order_by_child('auth_code').equal_to(auth_code).get()
    if not user_auth:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = next(iter(user_auth))
    access_token = user_auth[user_id]['access_token']
    return jsonify({'access_token': access_token, 'token_type': 'bearer'}), 200

@app.route('/getUsers', methods=['GET'])
def get_users():
    all_users = ref_user_auth.get()
    return jsonify(all_users), 200

@app.route('/getKpis', methods=['GET'])
def getKpis():
    refs = {
        'tasks': ref_tasks,
        'user_auth': ref_user_auth
    }
    kpi = KpiTracking(refs)
    return jsonify({"ok": "ok"}), 200

@https_fn.on_request()
def lamatodo(req: https_fn.Request) -> https_fn.Response:
    with app.request_context(req.environ):
        return app.full_dispatch_request()

if __name__ == "__main__":
    app.run(debug=True)