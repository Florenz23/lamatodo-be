from datetime import datetime
from dateutil.parser import parse


def parse_subtasks(subtasks):
    if subtasks is not None:
        return subtasks.split(";")
    else:
        return []

def parse_recurring_task(recurring_task_string):
    if recurring_task_string is not None:
        return recurring_task_string.split(";")
    else:
        return []


def parse_date(date_str):
    if date_str is not None:
        try:
            date = parse(date_str)
            return date.isoformat()
        except ValueError:
            raise ValueError("Error parsing date")
    else:
        return None