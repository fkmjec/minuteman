import random
import string
import datetime

def get_random_id(length):
    id = ""
    for i in range(length):
        id = id + random.choice(string.ascii_lowercase)
    return id

def get_current_time():
    return datetime.datetime.utcnow()