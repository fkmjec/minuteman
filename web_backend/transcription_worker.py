import pika
import api_interface
import logging

import audio_chunk

class MeetingTransciber:
    def __init__(self):
        self.chunks = {}

    def add_chunk(self, session_id, track_id, chunk):
        # TODO: add chunks by time
        pass

def callback(ch, method, properties, body):
    deserialized = audio_chunk.AudioChunk.deserialize(body)
    logging.info(" [x] Received %r" % deserialized.session_id)

# we now assume one worker, maybe we will scale to more later
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
channel = connection.channel()
channel.queue_declare("transcription_queue")
channel.basic_consume(queue='transcription_queue', on_message_callback=callback, auto_ack=True)
