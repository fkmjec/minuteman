import pika
import logging
import threading
import dateutil

import audio_chunk
import whisper_online
import faster_whisper

import onnxruntime
import numpy as np
from mosestokenizer import MosesTokenizer
from faster_whisper import vad
import os
import json
import time

WHISPER_MODEL = os.environ["WHISPER_MODEL"]
MAX_RABBITMQ_RETRIES = 200
SILERO_VAD_MODEL = "silero_vad.onnx"
VAD_CHUNK_SIZE = 512
MAX_PROB_THR = 0.95
SAMPLING_RATE = 16000
MAX_CHUNKS = 15

logging.basicConfig(level=logging.INFO)

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
        logger.info(f"probability:{max_prob}")
        if max_prob > MAX_PROB_THR:
            return True
        return False

class TrackTranscriber:
    """
    A class for transcribing a single audio track transmitted from a javascript TrackRecorder.
    It holds a continuous segment of audio in its chunks list. All of the segment should contain
    speech. The user of the object is responsible for keeping that invariant.
    """
    def __init__(self):
        self.chunks = []
        self.pushable_audio = None
    
    def _push_chunk(self, new_chunk):
        self.chunks.append(new_chunk)
        if len(self.chunks) > 1:
            return self.chunks[-2]
    
    def _is_ready(self):
        return len(self.chunks) >= 1

    def update(self, new_chunk, contains_speech):
        pushable_audio = None
        has_audio = False
        if contains_speech:
            self._push_chunk(new_chunk)
            if len(self.chunks) > MAX_CHUNKS:
                pushable_audio = self._flush()
                has_audio = True
        elif self._is_ready():
            pushable_audio = self._flush()
            has_audio = True
        return has_audio, pushable_audio
    
    def _flush(self):
        audio = np.concatenate(self.chunks, dtype=np.float32)
        self.chunks = []
        return audio

class MeetingTranscriber:
    """
    A wrapper class for a meeting transcription. Currently, it has no significant functionality
    beyond holding a dictionary of TrackTranscribers, one for each track in the meeting.
    Ideally, it should keep a state of all the tracks and then create a transcript only when
    all of them are ready and the utterances can be sorted by beginning time. This will
    be implemented if there is time to do so.
    """
    def __init__(self):
        self.tracks = {}

    def add_chunk(self, recorder_id, chunk, contains_speech):
        if recorder_id not in self.tracks:
            self.tracks[recorder_id] = TrackTranscriber()
        has_audio, pushable_audio = self.tracks[recorder_id].update(chunk, contains_speech)
        # TODO: create transcriptions when the whole meeting is ready
        return has_audio, pushable_audio
    
class Transcripts:
    def __init__(self):
        self.meetings = {}
    
    def _add_session(self, session_id):
        self.meetings[session_id] = MeetingTranscriber()
    
    def add_chunk(self, session_id, recorder_id, chunk, contains_speech):
        # TODO: if multiprocessing becomes necessary, we will need locks here
        if session_id not in self.meetings:
            self._add_session(session_id)
        return self.meetings[session_id].add_chunk(recorder_id, chunk, contains_speech)

def callback(ch, method, properties, body):
    # TODO: move this handler function to a separate thread as not to block pika queues
    deserialized = audio_chunk.AudioChunk.deserialize(body)
    session_id = deserialized.get_session_id()
    recorder_id = deserialized.get_recorder_id()
    author = deserialized.get_author()
    timestamp = deserialized.get_timestamp()
    chunk = deserialized.get_chunk()
    chunk = chunk.astype(np.float32)
    contains_speech = speech_detector.detect_speech(chunk)
    has_audio, audio = transcripts.add_chunk(session_id, recorder_id, chunk, contains_speech)
    if has_audio:
        logger.debug("Transcribing audio")
        transcript, info = backend.transcribe(audio, language="en")
        utterance_text = ""
        for i, segment in enumerate(transcript):
            utterance_text += segment.text + " "
            logger.debug(f"Transcript {i}: {segment.text}")
        if len(utterance_text) > 0:
            utterance = {
                "author": author,
                "utterance": utterance_text,
                "session_id": session_id,
                "timestamp": str(timestamp)
            }
            channel.queue_declare("transcript_queue", durable=True)
            channel.basic_publish(exchange='', routing_key='transcript_queue', body=json.dumps(utterance))
    logger.info(" [x] Received %r" % deserialized.get_session_id())

if __name__ == "__main__":
    # we now assume one worker, maybe we will scale to more later
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.info("Starting transcription worker")
    logger.info("Loading whisper model")
    backend = faster_whisper.WhisperModel(WHISPER_MODEL)
    # warm up the model
    logger.info("Warming up whisper model")
    backend.transcribe(np.zeros(1000, dtype=np.float32))
    logger.info("Loading speech detector")
    speech_detector = SpeechDetector(SILERO_VAD_MODEL)
    transcripts = Transcripts()
    retries = 0
    logger.info("Waiting for rabbitmq")
    while retries < 20:
        try:
            # FIXME: disabled heartbeats for now, because threading would be way too complex
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', heartbeat=0))
            break
        except (pika.exceptions.AMQPConnectionError):
            logger.info(f"Waiting for rabbitmq, retry {retries + 1}")
            retries += 1
            time.sleep(1)
    logger.info("Connected to rabbitmq")
    channel = connection.channel()
    channel.queue_declare("audio_chunk_queue")
    channel.basic_consume(queue='audio_chunk_queue', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()