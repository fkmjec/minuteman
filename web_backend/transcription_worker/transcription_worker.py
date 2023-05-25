import pika
import logging
import audio_chunk
import whisper_online

from mosestokenizer import MosesTokenizer
import os
import time

WHISPER_MODEL = "base.en"
MAX_RABBITMQ_RETRIES = 20

class MeetingTranscriber:
    def __init__(self):
        self.processors = {}

    def add_chunk(self, track_id, chunk):
        if track_id not in self.processors:
            self.processors[track_id] = whisper_online.OnlineASRProcessor("en", backend, tokenizer)
        self.processors[track_id].insert_audio_chunk(chunk)
    
    def get_new_utterances(self):
        for track_id, processor in self.processors.items():
            new_speech = processor.process_iter()
            if new_speech[0] is None:
                continue
            print(f"{track_id}: {new_speech[2]}")

    def is_ready(self):
        return True

class Transcripts:
    def __init__(self):
        self.transcripts = {}
    
    def _add_session(self, session_id):
        self.transcripts[session_id] = MeetingTranscriber()
    
    def add_chunk(self, session_id, track_id, chunk):
        # TODO: if multiprocessing becomes necessary, we will need locks here
        if session_id not in self.transcripts:
            self._add_session(session_id)
        self.transcripts[session_id].add_chunk(track_id, chunk)
        if self.transcripts[session_id].is_ready():
            self.transcripts[session_id].get_new_utterances()


def callback(ch, method, properties, body):
    deserialized = audio_chunk.AudioChunk.deserialize(body)
    transcripts.add_chunk(deserialized.session_id, deserialized.track_id, deserialized.chunk)
    print(" [x] Received %r" % deserialized.session_id)

if __name__ == "__main__":
    # we now assume one worker, maybe we will scale to more later
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    if os.environ['MOCK_ML_MODELS'] == "true":
        backend = whisper_online.FasterWhisperASR("en", modelsize=WHISPER_MODEL, device="cpu")
    else:
        backend = whisper_online.FasterWhisperASR("en", modelsize=WHISPER_MODEL, device="cuda")
    tokenizer = MosesTokenizer("en")
    print("Loaded ASR model")
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
    channel.queue_declare("transcription_queue")
    channel.basic_consume(queue='transcription_queue', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()