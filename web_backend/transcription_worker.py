import pika
import api_interface
import logging

def callback(ch, method, properties, body):
    logging.info(" [x] Received %r" % body)

connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
channel = connection.channel()
channel.queue_declare("transcription_queue")
channel.basic_consume(queue='transcription_queue', on_message_callback=callback, auto_ack=True)
