import pickle
import numpy as np

class AudioChunk:
    def __init__(self, session_id: str, track_id: str, chunk: np.ndarray):
        self.session_id = session_id
        self.track_id = track_id
        self.chunk = chunk

    def deserialize(serialized):
        return pickle.loads(serialized)
    
    def serialize(self):
        return pickle.dumps(self)
