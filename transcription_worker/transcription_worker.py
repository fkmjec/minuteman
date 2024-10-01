import json
import logging
import os
import threading
import time
from queue import Queue

import audio_chunk
import faster_whisper
import numpy as np
import pika
import requests
from faster_whisper import WhisperModel, vad
from pika.adapters.blocking_connection import BlockingChannel

WHISPER_MODEL = os.environ["WHISPER_MODEL"]
MAX_RABBITMQ_RETRIES = 200
SILERO_VAD_MODEL = "silero_vad.onnx"
VAD_CHUNK_SIZE = 512
MAX_PROB_THR = 0.935
SAMPLING_RATE = 16000
MAX_CHUNKS = 15

logging.basicConfig(level=logging.INFO)
logging.getLogger("pika").setLevel(logging.WARNING)
logging.getLogger("faster_whisper").setLevel(logging.WARNING)


class TranscribableAudio:
    def __init__(self, audio, seq):
        self.audio = audio
        self.seq = seq


class SpeechDetector:
    def __init__(self, model_path):
        self.model = vad.SileroVADModel(model_path)

    def detect_speech(self, audio: np.array, logger):
        state, context = self.model.get_initial_states(batch_size=1)
        max_prob = 0
        for i in range(0, len(audio), VAD_CHUNK_SIZE):
            chunk = audio[i : i + VAD_CHUNK_SIZE]

            if len(chunk) < VAD_CHUNK_SIZE:
                chunk = np.pad(chunk, (0, int(VAD_CHUNK_SIZE - len(chunk))))
            speech_prob, state, _ = self.model(
                x=chunk, state=state, context=context, sr=SAMPLING_RATE
            )
            if speech_prob[0][0] > max_prob:
                max_prob = speech_prob
        if max_prob > MAX_PROB_THR:
            logger.info(f"Speech probability in current audio sequence: {max_prob}")
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
        self.seq = 0

    def add_chunk(self, recorder_id, chunk, contains_speech):
        if recorder_id not in self.tracks:
            self.tracks[recorder_id] = TrackTranscriber()
        has_audio, pushable_audio = self.tracks[recorder_id].update(
            chunk, contains_speech
        )
        if has_audio:
            transcribable_chunk = TranscribableAudio(pushable_audio, self.seq)
            self.seq += 1
            return transcribable_chunk
        else:
            return None


class Transcripts:
    def __init__(self):
        self.meetings = {}

    def _add_session(self, session_id):
        self.meetings[session_id] = MeetingTranscriber()

    def add_chunk(self, session_id, recorder_id, chunk, contains_speech):
        # NOTE: if multiprocessing becomes necessary, we will need locks here
        if session_id not in self.meetings:
            self._add_session(session_id)
        return self.meetings[session_id].add_chunk(recorder_id, chunk, contains_speech)


def handle_request(
    body,
    channel: BlockingChannel,
    connection,
    speech_detector,
    backend: WhisperModel,
    transcripts,
    logger,
):
    deserialized = audio_chunk.AudioChunk.deserialize(body)

    session_id = deserialized.get_session_id()
    recorder_id = deserialized.get_recorder_id()

    author = deserialized.get_author()
    timestamp = deserialized.get_timestamp()

    chunk = deserialized.get_chunk()
    chunk = chunk.astype(np.float32)

    contains_speech = speech_detector.detect_speech(chunk, logger)
    transcribable_audio = transcripts.add_chunk(
        session_id, recorder_id, chunk, contains_speech
    )

    if transcribable_audio is not None:
        transcript, _ = backend.transcribe(
            transcribable_audio.audio, language=None, task="translate"
        )

        utterance_text = ""
        for i, segment in enumerate(transcript):
            utterance_text += segment.text + " "
            logger.info(f"Transcript {i}: {segment.text}")

        if len(utterance_text) > 0:
            # send English first
            utterance = (
                {
                    "utterance": f"{author}: {utterance_text}\n",
                    "session_id": session_id + "_" + "en",
                    "timestamp": str(timestamp),
                    "seq": transcribable_audio.seq,
                },
            )
            send_utterance(
                utterance,
                connection,
                channel,
                logger,
            )

            sentences_to_translate = [
                sent.strip()
                for sent in utterance_text.split(".")
                if len(sent.strip()) > 0
            ]
            for i in range(10):
                try:
                    translations = requests.post(
                        "http://translation-worker:7778/translate",
                        json.dumps(sentences_to_translate),
                        headers={"Content-Type": "application/json"},
                    ).json()
                    break
                except Exception as e:
                    logger.error(e)
                    time.sleep(i)

            for language in translations:
                utterance = (
                    {
                        "utterance": f"{author}: {translations[language]}\n",
                        "session_id": session_id + "_" + language,
                        "timestamp": str(timestamp),
                        "seq": transcribable_audio.seq,
                    },
                )
                send_utterance(
                    utterance,
                    connection,
                    channel,
                    logger,
                )


def send_utterance(utterance, connection, channel, logger):
    try:
        channel.basic_publish(
            exchange="",
            routing_key="transcript_queue",
            body=json.dumps(utterance),
        )
    except Exception:
        connection = get_rabbitmq_connection()
        channel = connection.channel()

        channel.basic_publish(
            exchange="",
            routing_key="transcript_queue",
            body=json.dumps(utterance),
        )


def init_worker(queue, transcripts):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    speech_detector = SpeechDetector(SILERO_VAD_MODEL)
    # backend = faster_whisper.WhisperModel("/whisper_model", local_files_only=True)
    backend = faster_whisper.WhisperModel(
        "/whisper_model", local_files_only=True, device="cuda", device_index=[0, 1]
    )

    while not backend.model:
        logger.debug("Waiting for backend model to load")
        time.sleep(5)

    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.queue_declare("transcript_queue", durable=True)

    try:
        while True:
            body = queue.get()
            handle_request(
                body, channel, connection, speech_detector, backend, transcripts, logger
            )
    except Exception as e:
        logger.error(e, exc_info=True)
    finally:
        channel.close()
        connection.close()


def get_rabbitmq_connection():
    retries = 0
    while retries < MAX_RABBITMQ_RETRIES:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host="rabbitmq")
            )
            return connection
        except Exception as e:
            retries += 1
            if retries >= 5:
                logger.debug(e)
                logger.error(
                    f"Failed to connect to RabbitMQ, retrying in 5s, retry no. {retries}."
                )
            time.sleep(5)
    raise Exception("Could not connect to rabbitmq")


def callback(ch, method, properties, body):
    queue.put(body)
    ch.basic_ack(delivery_tag=method.delivery_tag)


if __name__ == "__main__":
    logger = logging.getLogger(__name__)

    transcripts = Transcripts()
    queue = Queue()
    threading.Thread(target=init_worker, args=(queue, transcripts), daemon=True).start()

    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare("audio_chunk_queue")
        channel.basic_consume(queue="audio_chunk_queue", on_message_callback=callback)
        channel.start_consuming()
    finally:
        channel.close()
        connection.close()
