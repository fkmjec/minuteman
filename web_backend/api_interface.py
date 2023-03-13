import requests

# TODO: this belongs somewhere systematic
TORCH_API_ADDRESS = "http://torchserve:8080/predictions/bart"

def _prepare_request_data_files(model_input_string):
    files = {'data': ('model_input.txt', model_input_string)}
    return files

def summarize_block(input_string):
    files = _prepare_request_data_files(input_string)
    response = requests.post(TORCH_API_ADDRESS, files=files)
    return response