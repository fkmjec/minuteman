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

# import transformers
from faster_whisper import vad
from pika.adapters.blocking_connection import BlockingChannel

WHISPER_MODEL = os.environ["WHISPER_MODEL"]
MAX_RABBITMQ_RETRIES = 200
SILERO_VAD_MODEL = "silero_vad.onnx"
VAD_CHUNK_SIZE = 512
MAX_PROB_THR = 0.9
SAMPLING_RATE = 16000
MAX_CHUNKS = 7

logging.basicConfig(level=logging.INFO)


class TranscribableAudio:
    def __init__(self, audio, seq):
        self.audio = audio
        self.seq = seq


class SpeechDetector:
    def __init__(self, model_path):
        self.model = vad.SileroVADModel(model_path)

    def detect_speech(self, audio: np.array):
        state = self.model.get_initial_state(1)
        max_prob = 0
        for i in range(0, len(audio), VAD_CHUNK_SIZE):
            chunk = audio[i : i + VAD_CHUNK_SIZE]

            if len(chunk) < VAD_CHUNK_SIZE:
                chunk = np.pad(chunk, (0, int(VAD_CHUNK_SIZE - len(chunk))))
            speech_prob, state = self.model(chunk, state, SAMPLING_RATE)
            if speech_prob[0][0] > max_prob:
                max_prob = speech_prob
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
        self.seq = 0

    def add_chunk(self, recorder_id, chunk, contains_speech):
        if recorder_id not in self.tracks:
            self.tracks[recorder_id] = TrackTranscriber()
        has_audio, pushable_audio = self.tracks[recorder_id].update(
            chunk, contains_speech
        )
        # TODO: create transcriptions when the whole meeting is ready
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
    backend,
    transcripts,
    logger,
    # translator,
    # sp,
):
    deserialized = audio_chunk.AudioChunk.deserialize(body)

    session_id = deserialized.get_session_id()
    recorder_id = deserialized.get_recorder_id()

    author = deserialized.get_author()
    timestamp = deserialized.get_timestamp()

    chunk = deserialized.get_chunk()
    chunk = chunk.astype(np.float32)

    contains_speech = speech_detector.detect_speech(chunk)
    transcribable_audio = transcripts.add_chunk(
        session_id, recorder_id, chunk, contains_speech
    )

    if transcribable_audio is not None:
        transcript, _ = backend.transcribe(
            transcribable_audio.audio, language=None, task="translate"
        )
        # backend.insert_audio_chunk(transcribable_audio.audio)

        # try:
        #     _, _, text = backend.process_iter()
        # except AssertionError:
        #     logger.error(
        #         "WhisperOnline: Assertion error",
        #     )
        #     return

        # if not len(text):
        #     logger.info("WhisperOnline: No text returned")
        #     return
        # utterance_text = text

        utterance_text = ""
        for i, segment in enumerate(transcript):
            utterance_text += segment.text + " "
            logger.debug(f"Transcript {i}: {segment.text}")

        # # Source and target language codes
        # src_lang = "eng_Latn"
        # tgt_lang = "ces_Latn"

        # beam_size = 4

        # source_sentences = [sent.strip() for sent in utterance_text.split(".") if len(sent.strip()) > 0]
        # target_prefix = [[tgt_lang]] * len(source_sentences)

        # # Sub-word the source sentences
        # source_sents_subworded = sp.encode_as_pieces(source_sentences)
        # source_sents_subworded = [[src_lang] + sent + ["</s>"] for sent in source_sents_subworded]
        # print("First sub-worded source sentence:", source_sents_subworded[0], sep="\n")

        # # Translate the source sentences
        # translations_subworded = translator.translate_batch(source_sents_subworded, batch_type="tokens", max_batch_size=2024, beam_size=beam_size, target_prefix=target_prefix)
        # translations_subworded = [translation.hypotheses[0] for translation in translations_subworded]
        # for translation in translations_subworded:
        #     if tgt_lang in translation:
        #         translation.remove(tgt_lang)

        # # De-sub-word the target sentences
        # translations = sp.decode(translations_subworded)
        # print("First sentence and translation:", source_sentences, translations, sep="\n")

        # utterance_text = " ".join(translations).replace("  ", " ").strip()
        utterance_text = f"{author}: {utterance_text}\n"

        if len(utterance_text) > 0:
            utterance = {
                "utterance": utterance_text,
                "session_id": session_id,
                "timestamp": str(timestamp),
                "seq": transcribable_audio.seq,
            }
            try:
                channel.basic_publish(
                    exchange="",
                    routing_key="transcript_queue",
                    body=json.dumps(utterance),
                )
            except Exception as e:
                logger.error(e)
                logger.info("Reconnecting to RabbitMQ")

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
    backend = faster_whisper.WhisperModel(WHISPER_MODEL)

    # asr = FasterWhisperASR(lan="auto", modelsize="large-v2")
    # asr.set_translate_task()
    # backend = OnlineASRProcessor(asr)

    while not backend.model:
        logger.info("Waiting for backend model to load")
        time.sleep(5)

    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.queue_declare("transcript_queue", durable=True)

    # import ctranslate2
    # import sentencepiece as spm

    # # [Modify] Set paths to the CTranslate2 and SentencePiece models
    # ct_model_path = "nllb-200-3.3B-int8"
    # sp_model_path = "flores200_sacrebleu_tokenizer_spm.model"

    # device = "cuda"  # or "cpu"

    # # Load the source SentencePiece model
    # sp = spm.SentencePieceProcessor()
    # sp.load(sp_model_path)

    # translator = ctranslate2.Translator(ct_model_path, device=device)

    try:
        while True:
            body = queue.get()
            handle_request(
                body,
                channel,
                connection,
                speech_detector,
                backend,
                transcripts,
                logger,
                # translator,
                # sp,
            )
    except Exception as e:
        logger.error(e)
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
    # setting up logging
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
