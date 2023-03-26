import requests

# TODO: this belongs somewhere systematic, perhaps to a config file/env vars
SUMM_API_ADDRESS = "http://torchserve:8084/predictions/bart"
TRANSCRIBE_API_ADDRESS = "http://torchserve:8084/predictions/whisper"

def _prepare_request_data_files(model_input_string):
    files = {'data': ('model_input.txt', model_input_string)}
    return files


def summarize_block(input_string):
    files = _prepare_request_data_files(input_string)
    response = requests.post(SUMM_API_ADDRESS, files=files)
    return response.text


def _prepare_request_data_audio(audio_data):
    files = {'data': ('model_input.audio', audio_data)}
    return files


def _transcribe_audio(audio_data):
    files = _prepare_request_data_audio(audio_data)
    response = requests.post(TRANSCRIBE_API_ADDRESS, files=files)
    return response.text


def transcribe_chunk(chunk):
    transcribed_text = _transcribe_audio(chunk)
    return transcribed_text