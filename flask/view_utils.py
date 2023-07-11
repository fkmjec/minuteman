import random
import string
import datetime
import dateutil.parser
import pickle

def get_random_id(length):
    id = ""
    for i in range(length):
        id = id + random.choice(string.ascii_lowercase)
    return id

def get_current_time():
    return datetime.datetime.utcnow()

def datetime_from_iso(iso_str):
    return dateutil.parser.parse(iso_str)

def get_formatted_utterance(author, utterance):
    return f"{author}: {utterance}"

def create_audio_chunk(session_id, author, recorder_id, timestamp, audio_data):
    return {
        "session_id": session_id,
        "author": author,
        "recorder_id": recorder_id,
        "timestamp": str(timestamp),
        "chunk": audio_data
    }

def serialize_dict(dict):
    return pickle.dumps(dict)