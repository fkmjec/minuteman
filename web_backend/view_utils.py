import random
import string

def get_random_id(length):
    id = ""
    for i in range(length):
        id = id + random.choice(string.ascii_lowercase)
    return id