import json
import logging
import os
import threading
import time
from queue import Queue

import api_interface
import pika
import requests


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger


LOGGER = get_logger(__name__)

MAX_RABBITMQ_RETRIES = 200
INPUT_QUEUE_NAME = "summary_input_queue"
OUTPUT_QUEUE_NAME = "summary_result_queue"
TORCH_BACKEND_URL = os.environ["TORCH_BACKEND_URL"]
MOCK_ML_MODELS = os.environ["MOCK_ML_MODELS"] == "true"
REQUEST_SEQ = 0

logging.basicConfig(level=logging.INFO)
logging.getLogger("pika").setLevel(logging.WARNING)



def summarize(api_obj, input_string, model):
    return api_obj.summarize_block(input_string, model)


def send_summarized(session_id, summary_seq, summary_text, channel):
    summary = {
        "session_id": session_id,
        "summary_seq": summary_seq,
        "summary_text": summary_text,
    }
    try:
        channel.basic_publish(
            exchange="", routing_key=OUTPUT_QUEUE_NAME, body=json.dumps(summary)
        )
    except Exception:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare(OUTPUT_QUEUE_NAME, durable=True)
        channel.basic_publish(
            exchange="", routing_key=OUTPUT_QUEUE_NAME, body=json.dumps(summary)
        )


def process_input(api_obj, body, channel):
    deserialized = json.loads(body)
    model = deserialized["model"]
    session_id = deserialized["session_id"]
    summary_seq = deserialized["summary_seq"]
    text = deserialized["text"].strip()

    if len(text) <= 50:
        return

    result = f"{summarize(api_obj, text, model)}".strip()

    if len(result) <= 10:
        return

    print(f"Sending summarization for en: {result}")

    # LOGGER.info("Sending summarization for en")
    # LOGGER.info(f"summarization: {result}")
    send_summarized(session_id + "_" + "en", summary_seq, result, channel)

    sentences_to_translate = [
        sent.strip() for sent in result.split(".") if len(sent.strip()) > 0
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
            LOGGER.error(e)
            time.sleep(i)

    for language in translations:
        print(f"Sending summarization for {language}: {translations[language]}")
        send_summarized(
            session_id + "_" + language,
            summary_seq,
            translations[language],
            channel,
        )


def init_worker(queue):
    torch_interface = api_interface.TorchInterface(TORCH_BACKEND_URL, MOCK_ML_MODELS)

    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.queue_declare(OUTPUT_QUEUE_NAME, durable=True)

    try:
        while True:
            body = queue.get()
            process_input(torch_interface, body, channel)
    finally:
        channel.close()
        connection.close()


def callback(ch, method, properties, body):
    queue.put(body)
    ch.basic_ack(delivery_tag=method.delivery_tag)


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
                LOGGER.debug(e)
                LOGGER.error(
                    f"Failed to connect to RabbitMQ, retrying in 5s, retry no. {retries}."
                )
            time.sleep(5)
    raise Exception("Could not connect to rabbitmq")


if __name__ == "__main__":
    LOGGER.info("Starting summarization worker")
    connection = get_rabbitmq_connection()
    queue = Queue()
    threading.Thread(target=init_worker, args=(queue,), daemon=True).start()
    channel = connection.channel()
    channel.queue_declare(INPUT_QUEUE_NAME, durable=True)
    channel.basic_consume(queue=INPUT_QUEUE_NAME, on_message_callback=callback)
    channel.start_consuming()
