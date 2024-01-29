import pytz
from datetime import datetime, timedelta
import statistics

class KpiTracking:
    def __init__(self, refs):
        self.ref_tasks = refs['tasks']
        self.ref_user_auth = refs['user_auth']
        self.timezone_user = 'Europe/Berlin'

    def get_current_date(self):
        now = datetime.now()
        user_tz = pytz.timezone(self.timezone_user)
        return now.astimezone(user_tz)

    def registrations_last_day(self):
        now = self.get_current_date()
        one_day_ago = now - timedelta(days=1)
        one_day_ago_str = one_day_ago.isoformat()
        registrations_last_day =  self.ref_user_auth.order_by_child('registration_date').start_at(one_day_ago_str).get()
        return len(registrations_last_day)

    def registrations_last_7_days(self):
        now = self.get_current_date()
        seven_days_ago = now - timedelta(days=7)
        seven_days_ago_str = seven_days_ago.isoformat()
        registrations_last_7_days = self.ref_user_auth.order_by_child('registration_date').start_at(seven_days_ago_str).get()
        return len(registrations_last_7_days)

    def active_users_last_day(self):
        now = self.get_current_date()
        one_day_ago = now - timedelta(days=1)
        one_day_ago_str = one_day_ago.isoformat()
        tasks = self.ref_tasks.order_by_child('last_activity').start_at(one_day_ago_str).get()
        if tasks and isinstance(tasks, dict):
            tasks = list(tasks.values())
        if tasks and isinstance(tasks[0], dict):
            return len(set(task['user_id'] for task in tasks))
        else:
            # handle the case where tasks is not as expected
            return 0

    def active_users_last_7_days(self):
        now = self.get_current_date()
        seven_days_ago = now - timedelta(days=7)
        seven_days_ago_str = seven_days_ago.isoformat()
        tasks = self.ref_tasks.order_by_child('last_activity').start_at(seven_days_ago_str).get()
        return len(set(task['user_id'] for task in tasks))

    def average_tasks_per_user(self):
        tasks_per_user = [len(self.ref_tasks.child(user_id).get()) if self.ref_tasks.child(user_id).get() is not None else 0 for user_id in self.ref_user_auth.get()]
        return statistics.mean(tasks_per_user)

    def median_tasks_per_user(self):
        tasks_per_user = [len(self.ref_tasks.child(user_id).get()) if self.ref_tasks.child(user_id).get() is not None else 0 for user_id in self.ref_user_auth.get()]
        return statistics.median(tasks_per_user)

    # def tutorial_completion_rate(self):
    #     completed_tutorial = [user['completed_tutorial'] for user in self.ref_user_auth.get().values()]
    #     return completed_tutorial.count(True) / len(completed_tutorial)