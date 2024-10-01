import logging
import urllib.parse

import requests
import transcript


# the class to hold config and create requests for the underlying TorchServe backend
class TorchInterface:
    def __init__(self, torch_backend_url, mock_ml_models):
        self.torch_backend_url = torch_backend_url
        self.mock_ml_models = mock_ml_models

    def _construct_model_address(self, model_name):
        return urllib.parse.urljoin(self.torch_backend_url, "predictions/" + model_name)

    def _prepare_request_data_files(self, model_input_string):
        files = {"data": ("model_input.txt", model_input_string)}
        return files

    def summarize_block(self, input_string, model_name):
        trsc = transcript.Transcript.from_automin(input_string)
        trsc.kartik_clean()
        trsc = trsc.raw_str()
        files = self._prepare_request_data_files(trsc)
        summ_addr = self._construct_model_address(model_name)
        if self.mock_ml_models:
            logging.debug(f"Summarization req to {summ_addr} mocked!")
            return "Summary mock!"
        else:
            logging.debug(f"Making transcription request to {summ_addr}")
            response = requests.post(summ_addr, files=files)
            if response.status_code != 200:
                return "summarization unsuccessful due to model error"
            return response.text

    def _prepare_request_data_audio(self, audio_data):
        files = {"data": ("model_input.audio", audio_data)}
        return files
