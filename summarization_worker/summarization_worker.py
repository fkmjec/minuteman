import logging
import time
import pika
import json

MAX_RETRIES = 200
INPUT_QUEUE_NAME = "summary_input_queue"

logging.basicConfig(level=logging.INFO)

def callback(ch, method, properties, body):
    deserialized = json.loads(body)
    logger.info(deserialized)

if __name__ == "__main__":
    # we now assume one worker, maybe we will scale to more later
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.info("Starting summarization worker")
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
    channel.queue_declare(INPUT_QUEUE_NAME, durable=True)
    channel.basic_consume(queue=INPUT_QUEUE_NAME, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()