from datetime import datetime, timedelta

def is_recent(time):
    return datetime.now() - timedelta(seconds=3) < time

