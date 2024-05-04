# the global config object for the entire app. Loaded once from env variables
import os


class Config:
    def __init__(self):
        self.mock_ml_models = os.environ["MOCK_ML_MODELS"] == "true"
        # self.torch_backend_url = os.environ["TORCH_BACKEND_URL"]
        self.db_url = os.environ["POSTGRES_DB_URL"]
        # loading the etherpad API key from file
        self.etherpad_api_key = open("APIKEY.txt", "r").read()
        self.etherpad_api_url = os.environ["ETHERPAD_API_URL"]
        self.etherpad_url = os.environ["ETHERPAD_URL"]
        self.torch_management_url = os.environ["TORCHSERVE_MANAGEMENT_URL"]
        # TODO: from variables? by model?
        self.max_input_len = 512
