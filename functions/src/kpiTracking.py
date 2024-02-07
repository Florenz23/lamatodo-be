import pytz
from datetime import datetime, timedelta
import statistics
import pandas as pd
import logging
import numpy as np




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
        one_day_ago = np.datetime64(now - timedelta(days=1))

        # Ensure the registration_date column is in datetime format
        self.df_user_auth['registration_date'] = pd.to_datetime(self.df_user_auth['registration_date'])

        # Filter rows from the last day
        last_day_registrations = self.df_user_auth[self.df_user_auth['registration_date'] >= one_day_ago]
        count_last_day_registrations = last_day_registrations.shape[0]

        return count_last_day_registrations

    def registrations_last_7_days(self):
        now = self.get_current_date()
        seven_days_ago = np.datetime64(now - timedelta(days=7))

        # Ensure the registration_date column is in datetime format
        self.df_user_auth['registration_date'] = pd.to_datetime(self.df_user_auth['registration_date'])

        # Filter rows from the last 7 days
        last_7_days_registrations = self.df_user_auth[self.df_user_auth['registration_date'] >= seven_days_ago]
        
        count_last_7_days_registrations = last_7_days_registrations.shape[0]

        return count_last_7_days_registrations


    def active_users_last_day(self):
        now = pd.Timestamp.now()
        one_day_ago = now - pd.Timedelta(days=1)
        
        # Convert 'last_activity' to datetime
        self.df_tasks['last_activity'] = pd.to_datetime(self.df_tasks['last_activity'])
        
        # Filter the DataFrame to only include rows where the timestamp is within the last day
        recent_projects = self.df_tasks[self.df_tasks['last_activity'] >= one_day_ago]
        
        # Count the unique project_ids
        count = recent_projects['project_id'].nunique()

        return count

    def active_users_last_7_days(self):
        now = pd.Timestamp.now()
        one_day_ago = now - pd.Timedelta(days=7)
        
        # Convert 'last_activity' to datetime
        self.df_tasks['last_activity'] = pd.to_datetime(self.df_tasks['last_activity'])
        
        # Filter the DataFrame to only include rows where the timestamp is within the last day
        recent_projects = self.df_tasks[self.df_tasks['last_activity'] >= one_day_ago]
        
        # Count the unique project_ids
        count = recent_projects['project_id'].nunique()

        return count

    def average_tasks_per_project(self):
        # Group tasks by project_id and count the number of tasks per project
        tasks_per_project = self.df_tasks.groupby('project_id').size()
        
        # Calculate and return the average number of tasks per project
        return tasks_per_project.mean()

    def median_tasks_per_project(self):
        # Group tasks by project_id and count the number of tasks per project
        tasks_per_project = self.df_tasks.groupby('project_id').size()
        
        # Calculate and return the median number of tasks per project
        return tasks_per_project.median()

        # def tutorial_completion_rate(self):
        #     completed_tutorial = [user['completed_tutorial'] for user in self.ref_user_auth.get().values()]
        #     return completed_tutorial.count(True) / len(completed_tutorial)