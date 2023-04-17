import logging
import requests
import urllib.parse
import transcript

SUMM_MODEL_NAME = "bart"
TRANSCRIBE_MODEL_NAME = "whisper"

# the class to hold config and create requests for the underlying TorchServe backend
class TorchInterface:
    def __init__(self, config):
        self.config = config

    def _construct_model_address(self, model_name):
        return urllib.parse.urljoin(self.config.torch_backend_url, "predictions/" + model_name)
    
    def _prepare_request_data_files(self, model_input_string):
        files = {'data': ('model_input.txt', model_input_string)}
        return files

    def summarize_block(self, input_string):
        trsc = transcript.Transcript.from_automin(input_string)
        trsc.kartik_clean()
        trsc = trsc.raw_str()
        files = self._prepare_request_data_files(trsc)
        summ_addr = self._construct_model_address(SUMM_MODEL_NAME)
        if self.config.mock_ml_models:
            logging.debug(f"Summarization req to {summ_addr} mocked!")
            return "Summary mock!"
        else:
            logging.debug(f"Making transcription request to {summ_addr}")
            response = requests.post(summ_addr, files=files)
            return response.text


    def _prepare_request_data_audio(self, audio_data):
        files = {'data': ('model_input.audio', audio_data)}
        return files


    def _transcribe_audio(self, audio_data):
        files = self._prepare_request_data_audio(audio_data)
        transcription_addr = self._construct_model_address(TRANSCRIBE_MODEL_NAME)
        if self.config.mock_ml_models:
            logging.debug(f"Transcription to {transcription_addr} mocked!")
            return "Transcript mock!"
        else:
            logging.debug(f"Making transcription request to {transcription_addr}")
            response = requests.post(transcription_addr, files=files)
            return response.text


    def transcribe_chunk(self, chunk):
        transcribed_text = self._transcribe_audio(chunk)
        return transcribed_text
