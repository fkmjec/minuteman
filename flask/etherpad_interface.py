import requests
import logging
import json
from bs4 import BeautifulSoup
from py_etherpad import EtherpadLiteClient

class PadInterface:
    def __init__(self, config):
        self.config = config
        self.pad = EtherpadLiteClient(self.config.etherpad_api_key, baseUrl=self.config.etherpad_api_url)

    # TODO: move these utility functions to some general util file
    def _get_trsc_pad_id(self, pad_id):
        return pad_id + ".trsc"

    def _get_summ_pad_id(self, pad_id):
        return pad_id + ".summ"
    
    def session_id_from_pad(self, pad_id):
        print(pad_id)
        if pad_id.endswith(".trsc"):
            return pad_id[0:-5], "trsc"
        elif pad_id.endswith(".summ"):
            return pad_id[0:-5], "summ"
        else:
            raise ValueError("Incorrect pad_id that does not end with .summ or .trcs")

    def create_session(self, session_id, debug=False):
        # creates a pad for the transcript and a pad for the summary
        # TODO: do I want to put the pads in a separate group?
        # TODO: error handling here
        transcript_pad_id = self._get_trsc_pad_id(session_id)
        summ_pad_id = self._get_summ_pad_id(session_id)
        self.pad.createPad(transcript_pad_id, "Works with a transcript!")
        self.pad.createPad(summ_pad_id, "Works with a summary!")
        self._create_session_object(session_id, debug=debug)

    def set_chunk_len(self, session_id, chunk_len):
        url = self.config.etherpad_api_url + "/setChunkLen"
        params = {}
        data = {
            "apikey": self.config.etherpad_api_key,
            "session_id": session_id,
            "chunk_len": chunk_len,
        }
        requests.post(url, params=params, data=data)


    def _create_session_object(self, session_id, debug):
        url = self.config.etherpad_api_url + "/createSessionObject"
        headers = {"Content-Type": "application/json"}
        data = {
            "apikey": self.config.etherpad_api_key,
            "session_id": session_id,
            "debug": debug
        }
        requests.post(url, headers=headers, data=json.dumps(data))


    def get_transcript(self, pad_id):
        transcript_pad_id = self._get_trsc_pad_id(pad_id)
        transcript = self.pad.getText(transcript_pad_id)
        return transcript["text"]
    

    def get_minutes(self, pad_id):
        # TODO maybe rework this together with a better api in ep_minuteman
        summary_pad_id = self._get_summ_pad_id(pad_id)
        html = self.pad.getHtml(summary_pad_id)["html"]
        soup = BeautifulSoup(html)
        summary_spans = soup.find_all("span", class_="summary")
        summary_spans_processed = []
        for summary_span in summary_spans:
            classes = summary_span["class"]
            summary_spans_processed.append((classes[1], summary_span.text))
        return summary_spans_processed