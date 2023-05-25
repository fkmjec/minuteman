import pickle
import numpy as np

class AudioChunk:
    def __init__(self, session_id: str = None, recorder_id: str = None, chunk: np.ndarray = None):
        self._data = {}
        self._data["session_id"] = session_id
        self._data["recorder_id"] = recorder_id
        self._data["chunk"] = chunk

    def get_session_id(self):
        return self._data["session_id"]
    
    def get_recorder_id(self):
        return self._data["recorder_id"]
    
    def get_chunk(self):
        return self._data["chunk"]
    
    def deserialize(serialized):
        chunk = AudioChunk()
        chunk._data = pickle.loads(serialized)
        return chunk
    
    def serialize(self):
        return pickle.dumps(self._data)
