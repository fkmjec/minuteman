import pika
import logging
import audio_chunk
import whisper_online

import onnxruntime
import numpy as np
from mosestokenizer import MosesTokenizer
from faster_whisper import vad
import os
import json
import time

WHISPER_MODEL = "base.en"
MAX_RABBITMQ_RETRIES = 20
SILERO_VAD_MODEL = "silero_vad.onnx"
VAD_CHUNK_SIZE = 512
MAX_PROB_THR = 0.5
SAMPLING_RATE = 16000
MAX_CHUNKS = 15

class SpeechDetector:
    def __init__(self, model_path):
        self.model = vad.SileroVADModel(model_path)
    
    def detect_speech(self, audio: np.array):
        state = self.model.get_initial_state(1)
        max_prob = 0
        for i in range(0, len(audio), VAD_CHUNK_SIZE):
            chunk = audio[i:i + VAD_CHUNK_SIZE]

            if len(chunk) < VAD_CHUNK_SIZE:
                chunk = np.pad(chunk, (0, int(VAD_CHUNK_SIZE - len(chunk))))
            speech_prob, state = self.model(chunk, state, SAMPLING_RATE)
            if speech_prob[0][0] > max_prob:
                max_prob = speech_prob
        if max_prob > MAX_PROB_THR:
            return True
        return False

class TrackTranscriber:
    def __init__(self, name):
        self.name = name
        self.chunks = []
    
    def push_chunk(self, new_chunk):
        self.chunks.append(new_chunk.astype(np.float32))
    
    def is_ready(self, speech_detector):
        if len(self.chunks) > 0:
            # is ready if all chunks contain speech except the last one
            return not speech_detector.detect_speech(self.chunks[-1]) or len(self.chunks) > MAX_CHUNKS
        return False
    
    def flush(self):
        audio = np.concatenate(self.chunks, dtype=np.float32)
        self.chunks = []
        return audio

class MeetingTranscriber:
    def __init__(self):
        self.tracks = {}

    def add_chunk(self, recorder_id, name, chunk):
        if recorder_id not in self.tracks:
            self.tracks[recorder_id] = TrackTranscriber(name)
        return self.tracks[recorder_id].push_chunk(chunk)
    
class Transcripts:
    def __init__(self):
        self.meetings = {}
    
    def _add_session(self, session_id):
        self.meetings[session_id] = MeetingTranscriber()
    
    def add_chunk(self, session_id, recorder_id, chunk):
        # TODO: if multiprocessing becomes necessary, we will need locks here
        if session_id not in self.meetings:
            self._add_session(session_id)
        self.meetings[session_id].add_chunk(recorder_id, "hek", chunk)
    
    def is_ready(self, session_id, recorder_id, speech_detector):
        if session_id not in self.meetings:
            raise ValueError("Meeting not found")
        if recorder_id not in self.meetings[session_id].tracks:
            raise ValueError("Track not found")
        return self.meetings[session_id].tracks[recorder_id].is_ready(speech_detector)

def callback(ch, method, properties, body):
    deserialized = audio_chunk.AudioChunk.deserialize(body)
    session_id = deserialized.get_session_id()
    recorder_id = deserialized.get_recorder_id()
    chunk = deserialized.get_chunk()
    transcripts.add_chunk(session_id, recorder_id, chunk)
    if transcripts.is_ready(session_id, recorder_id, speech_detector):
        audio = transcripts.meetings[session_id].tracks[recorder_id].flush()
        transcript = backend.transcribe(audio)
        if len(transcript) > 0:
            channel.queue_declare("transcript_queue", durable=True)
            utterance = {"name": "TODO name", "utterance": transcript[0].text}
            channel.basic_publish(exchange='', routing_key='transcript_queue', body=json.dumps(utterance))
    print(" [x] Received %r" % deserialized.get_session_id())

if __name__ == "__main__":
    # we now assume one worker, maybe we will scale to more later
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    if os.environ['MOCK_ML_MODELS'] == "true":
        backend = whisper_online.FasterWhisperASR("en", modelsize=WHISPER_MODEL, device="cpu")
    else:
        backend = whisper_online.FasterWhisperASR("en", modelsize=WHISPER_MODEL, device="cuda")
    tokenizer = MosesTokenizer("en")
    speech_detector = SpeechDetector(SILERO_VAD_MODEL)
    transcripts = Transcripts()
    retries = 0
    while retries < 20:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
            break
        except (pika.exceptions.AMQPConnectionError):
            print(f"Waiting for rabbitmq, retry {retries + 1}")
            retries += 1
            time.sleep(1)
        
    channel = connection.channel()
    channel.queue_declare("audio_chunk_queue")
    channel.basic_consume(queue='audio_chunk_queue', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()