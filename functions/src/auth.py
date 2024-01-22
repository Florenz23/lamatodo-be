from firebase_admin import auth, initialize_app
from flask import request

ref = db.reference('user_data')
ref_tasks = ref.child('tasks')

initialize_app()

def login_user_with_email(email, password):
    pass