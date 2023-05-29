import logging
import time
import pika
import json
import argparse

parser = argparse.ArgumentParser(description='Transcript recorder')
parser.add_argument('--rabbitmq_host', type=str, default='rabbitmq')
parser.add_argument('--record_to', type=str, default='recording.txt')

MAX_RETRIES = 200
INPUT_QUEUE_NAME = "transcript_queue"

logging.basicConfig(level=logging.INFO)

def callback(ch, method, properties, body):
    deserialized = json.loads(body)
    with open(args.record_to, 'a') as f:
        f.write(body + '\n')
    logger.info(deserialized)

if __name__ == "__main__":
    args = parser.parse_args()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.info("Starting recording worker")
    retries = 0
    logger.info("Waiting for rabbitmq")
    while retries < 20:
        try:
            # FIXME: disabled heartbeats for now, because threading would be way too complex
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=args.rabbitmq_host, heartbeat=0))
            break
        except (pika.exceptions.AMQPConnectionError):
            logger.info(f"Waiting for rabbitmq, retry {retries + 1}")
            retries += 1
            time.sleep(1)
    logger.info("Connected to rabbitmq")
    channel = connection.channel()
    channel.queue_declare(INPUT_QUEUE_NAME, durable=True)
    channel.basic_consume(queue=INPUT_QUEUE_NAME, on_message_callback=callback, auto_ack=False)
    channel.start_consuming()