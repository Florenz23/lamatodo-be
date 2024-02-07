import pytz
from datetime import datetime, timedelta
import statistics
import pandas as pd
import logging



class KpiTracking:
    def __init__(self, refs):
        self.ref_user_auth = refs['user_auth']
        self.ref_tasks = refs['tasks']
        self.timezone_user = 'Europe/Berlin'
        self.set_data_frames()

    def set_data_frames(self):
        json_data = self.ref_user_auth.get()

        df_user_auth = pd.DataFrame.from_dict(json_data, orient='index')
        df_tasks = pd.DataFrame.from_dict(self.ref_tasks.get(), orient='index')

        self.df_user_auth = df_user_auth
        self.df_tasks = df_tasks


    def get_current_date(self):
        now = datetime.now()
        user_tz = pytz.timezone(self.timezone_user)
        return now.astimezone(user_tz)

    def registrations_last_day(self):
        now = self.get_current_date()

    def registrations_last_7_days(self):
        now = self.get_current_date()

    def active_users_last_day(self):
        now = self.get_current_date()

    def active_users_last_7_days(self):
        now = self.get_current_date()

    def average_tasks_per_user(self):
        pass

    def median_tasks_per_user(self):
        pass

    # def tutorial_completion_rate(self):
    #     completed_tutorial = [user['completed_tutorial'] for user in self.ref_user_auth.get().values()]
    #     return completed_tutorial.count(True) / len(completed_tutorial)