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

    def create_pad_stack(self, pad_id):
        # creates a pad for the transcript and a pad for the summary
        # TODO: do I want to put the pads in a separate group?
        # TODO: error handling here
        transcript_pad_id = self._get_trsc_pad_id(pad_id)
        summ_pad_id = self._get_summ_pad_id(pad_id)
        self.pad.createPad(transcript_pad_id, "Works with a transcript!")
        self.pad.createPad(summ_pad_id, "Works with a summary!")
    
    # def add_trsc_line(self, pad_id, trsc_line):
    #     # FIXME: how will this api work? It would be logical to keep the session id private
    #     # so that not everyone can access the recording button
    #     # TODO: error handling here
    #     transcript_pad_id = self._get_trsc_pad_id(pad_id)
    #     trsc_line = "\n" + trsc_line
    #     self.pad.appendText(transcript_pad_id, trsc_line)

    # def add_summ_line(self, pad_id, summ_line, summ_line_id, trsc_start, trsc_end):
    #     # FIXME: how will this api work? It would be logical to keep the session id private
    #     # so that not everyone can access the recording button
    #     # TODO: HTML appending so that we can tag summary lines
    #     # TODO: error handling here
    #     summary_pad_id = self._get_summ_pad_id(pad_id)
    #     # TODO: pyetherpadlite does not support our API extensions yet with the ep_minuteman plugin
    #     # therefore, we have to make the requests ourselves
    #     url = self.config.etherpad_api_url + "/appendSumm"
    #     params = {}
    #     data = {
    #         "padID": summary_pad_id,
    #         "apikey": self.config.etherpad_api_key,
    #         "data": json.dumps({
    #             "id": summ_line_id,
    #             "text": summ_line,
    #             "preTrsc": trsc_start,
    #             "postTrsc": trsc_end
    #         }
    #     )}

    #     response = requests.post(url, params=params, data=data)
    #     if response.status_code == 200 and response.json()["code"] == 0:
    #         return True
    #     logging.debug(response)
    #     return False
    #     # self.pad.appendText(summary_pad_id, summ_line)
    
    # def update_summ_line(self, pad_id, summ_line, summ_line_id):
    #     summary_pad_id = self._get_summ_pad_id(pad_id)
    #     # TODO: pyetherpadlite does not support our API extensions yet with the ep_minuteman plugin
    #     # therefore, we have to make the requests ourselves
    #     url = self.config.etherpad_api_url + "/updateSumm"
    #     params = {}
    #     data = {"padID": summary_pad_id, "apikey": self.config.etherpad_api_key, "data": json.dumps({"id": summ_line_id, "text": summ_line})}

    #     response = requests.post(url, params=params, data=data)
    #     if response.status_code == 200 and response.json()["code"] == 0:
    #         return True
    #     logging.debug(response)
    #     return False

    def get_transcript(self, pad_id):
        transcript_pad_id = self._get_trsc_pad_id(pad_id)
        transcript = self.pad.getText(transcript_pad_id)
        return transcript["text"]
    
    # def get_transcript_segments(self, pad_id):
    #     transcript = self.get_transcript(pad_id)

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