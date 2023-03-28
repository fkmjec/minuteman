# the global config object for the entire app. Loaded once from env variables
import os

class Config():
    def __init__(self):
        self.mock_ml_models = os.environ["MOCK_ML_MODELS"] == "true"
        self.torch_backend_url = os.environ["TORCH_BACKEND_URL"]
        self.db_url = os.environ["POSTGRES_DB_URL"]
        self.flask_app_url = os.environ["FLASK_APP_URL"]
        # TODO: from variables? by model?
        self.max_input_len = 512