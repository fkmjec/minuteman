import random
import string
import datetime
import dateutil.parser

def get_random_id(length):
    id = ""
    for i in range(length):
        id = id + random.choice(string.ascii_lowercase)
    return id

def get_current_time():
    return datetime.datetime.utcnow()

def datetime_from_iso(iso_str):
    return dateutil.parser.parse(iso_str)