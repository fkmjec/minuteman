import json

import requests
from py_etherpad import EtherpadLiteClient


class PadInterface:
    def __init__(self, config):
        self.config = config
        self.pad = EtherpadLiteClient(
            self.config.etherpad_api_key, baseUrl=self.config.etherpad_api_url
        )

    # TODO: move these utility functions to some general util file
    def _get_trsc_pad_id(self, pad_id):
        return pad_id + ".trsc"

    def _get_summ_pad_id(self, pad_id):
        return pad_id + ".summ"

    def session_id_from_pad(self, pad_id):
        if pad_id.endswith(".trsc"):
            return pad_id[0:-5], "trsc"
        elif pad_id.endswith(".summ"):
            return pad_id[0:-5], "summ"
        else:
            raise ValueError("Incorrect pad_id that does not end with .summ or .trcs")

    def create_session(self, session_id, config):
        # creates a pad for the transcript and a pad for the summary
        transcript_pad_id = self._get_trsc_pad_id(session_id)
        summ_pad_id = self._get_summ_pad_id(session_id)
        self._create_session_object(session_id, config)
        self.pad.createPad(transcript_pad_id, "Works with a transcript!")
        self.pad.createPad(summ_pad_id, "Works with a summary!")

    def set_chunk_len(self, session_id, chunk_len):
        url = self.config.etherpad_api_url + "/setChunkLen"
        params = {}
        data = {
            "apikey": self.config.etherpad_api_key,
            "session_id": session_id,
            "chunk_len": chunk_len,
        }
        requests.post(url, params=params, data=data)

    def _create_session_object(self, session_id, config):
        url = self.config.etherpad_api_url + "/createSessionObject"
        headers = {"Content-Type": "application/json"}
        data = {
            "apikey": self.config.etherpad_api_key,
            "session_id": session_id,
            "config": config.get_dict(),
        }
        requests.post(url, headers=headers, data=json.dumps(data))

    def get_session_config(self, session_id):
        params = {"session_id": session_id}
        url = self.config.etherpad_api_url + "/sessionConfig"
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise ValueError("Could not get session config")
        return response.json()

    def set_summ_model(self, session_id, summ_model):
        url = self.config.etherpad_api_url + "/setSummModel"
        params = {}
        data = {
            "session_id": session_id,
            "summ_model": summ_model,
        }
        requests.post(url, params=params, data=data)

    def set_recording_status(self, session_id, status):
        url = self.config.etherpad_api_url + "/setRecordStatus"
        params = {}
        data = {
            "session_id": session_id,
            "record_status": status,
        }
        requests.post(url, params=params, data=data)
