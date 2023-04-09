import requests
import logging
import json
from py_etherpad import EtherpadLiteClient

class PadInterface:
    def __init__(self, config):
        self.config = config
        self.pad = EtherpadLiteClient(self.config.etherpad_api_key, baseUrl=self.config.etherpad_api_url)

    def _get_trsc_pad_id(self, pad_id):
        return pad_id + ".trsc"

    def _get_summ_pad_id(self, pad_id):
        return pad_id + ".summ"

    def create_pad_stack(self, pad_id):
        # creates a pad for the transcript and a pad for the summary
        # TODO: do I want to put the pads in a separate group?
        # TODO: error handling here
        transcript_pad_id = self._get_trsc_pad_id(pad_id)
        summ_pad_id = self._get_summ_pad_id(pad_id)
        self.pad.createPad(transcript_pad_id, "Works with a transcript!")
        self.pad.createPad(summ_pad_id, "Works with a summary!")
    
    def add_trsc_line(self, pad_id, trsc_line):
        # FIXME: how will this api work? It would be logical to keep the session id private
        # so that not everyone can access the recording button
        # TODO: error handling here
        transcript_pad_id = self._get_trsc_pad_id(pad_id)
        trsc_line = "\n" + trsc_line
        self.pad.appendText(transcript_pad_id, trsc_line)

    def add_summ_line(self, pad_id, summ_line, summ_line_id):
        # FIXME: how will this api work? It would be logical to keep the session id private
        # so that not everyone can access the recording button
        # TODO: HTML appending so that we can tag summary lines
        # TODO: error handling here
        summary_pad_id = self._get_summ_pad_id(pad_id)
        summ_line = "\n" + summ_line
        # TODO: pyetherpadlite does not support our API extensions yet with the ep_minuteman plugin
        # therefore, we have to make the requests ourselves
        url = self.config.etherpad_api_url + "/appendSumm"
        params = {}
        data = {"padID": summary_pad_id, "apikey": self.config.etherpad_api_key, "data": json.dumps({"id": summ_line_id, "text": summ_line})}

        response = requests.post(url, params=params, data=data)
        if response.status_code == 200 and response.json()["code"] == 0:
            return True
        logging.debug(response)
        return False
        # self.pad.appendText(summary_pad_id, summ_line)
    
    def update_summ_line(self, pad_id, summ_line, summ_line_id):
        summary_pad_id = self._get_summ_pad_id(pad_id)
        summ_line = "\n" + summ_line
        # TODO: pyetherpadlite does not support our API extensions yet with the ep_minuteman plugin
        # therefore, we have to make the requests ourselves
        url = self.config.etherpad_api_url + "/updateSumm"
        params = {}
        data = {"padID": summary_pad_id, "apikey": self.config.etherpad_api_key, "data": json.dumps({"id": summ_line_id, "text": summ_line})}

        response = requests.post(url, params=params, data=data)
        if response.status_code == 200 and response.json()["code"] == 0:
            return True
        logging.debug(response)
        return False

    def get_transcript(self, pad_id):
        transcript_pad_id = self._get_trsc_pad_id(pad_id)
        transcript = self.pad.getText(transcript_pad_id)
        return transcript["text"]