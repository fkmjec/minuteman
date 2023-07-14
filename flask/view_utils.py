import random
import string
import datetime
import dateutil.parser
import pickle
import json
import requests

class SessionConfig:
    def __init__(
        self, 
        chunk_len,
        debug,
        summ_model_id,
    ) -> None:
        self.chunk_len = chunk_len
        self.debug =  debug
        self.summ_model_id = summ_model_id

    def validate(self):
        # TODO 
        pass

    def from_json_string(json_string):
        temp_dict = json.loads(json_string)
        try:
            chunk_len = temp_dict["chunk_len"]
            debug = temp_dict["debug"] == "true"
            summ_model_id = temp_dict["summ_model_id"]
        except KeyError as e:
            raise ValueError(f"SessionConfig json string missing key: {e}")
        return SessionConfig(chunk_len, debug, summ_model_id)


    def serialize(self):
        config_dict = {
            "chunk_len": self.chunk_len,
            "debug": self.debug,
            "summ_model_id": self.summ_model_id
        }
        return json.dumps(config_dict)


def get_torchserve_available_models(torch_url):
    url = torch_url + "/models"

    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError("Could not get available models")
    models = response.json()["models"]
    models = map(lambda x: x["modelName"], models)
    return models


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