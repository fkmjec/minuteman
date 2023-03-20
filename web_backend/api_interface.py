import requests
import wave
import io

# TODO: this belongs somewhere systematic
TORCH_API_ADDRESS = "http://torchserve:8084/predictions/bart"

def _prepare_request_data_files(model_input_string):
    files = {'data': ('model_input.txt', model_input_string)}
    return files

def summarize_block(input_string):
    files = _prepare_request_data_files(input_string)
    response = requests.post(TORCH_API_ADDRESS, files=files)
    return response.text

def transcribe_chunk(chunk):
    # get length of chunk in seconds
    audio = io.BytesIO(chunk)
    with wave.open(audio) as wopen:
        frames = wopen.getnframes()
        rate = wopen.getframerate()
        duration = frames / float(rate)
    return "TODO: len of audio is {} seconds".format(duration)