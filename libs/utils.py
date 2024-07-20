import random

from sqlalchemy import inspect

from uuid import uuid4
from datetime import datetime


def now():
    return datetime.now()


def generate_id():
    id = str(uuid4())
    return id


def generate_otp():
    otp = ""
    while len(otp) < 6:
        otp += str(random.randint(1, 9))
    otp = int(otp)
    return otp


def date_time_diff_min(start: datetime, end: datetime):
    duration = end - start
    duration_in_seconds = duration.total_seconds()
    minutes = divmod(duration_in_seconds, 60)[0]
    return minutes


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}
