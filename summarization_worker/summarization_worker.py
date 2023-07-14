import logging
import time
import pika
import json
import os
import api_interface
import threading
from queue import Queue
import transcript
import transformers

MAX_RETRIES = 200
INPUT_QUEUE_NAME = "summary_input_queue"
OUTPUT_QUEUE_NAME = "summary_result_queue"
TORCH_BACKEND_URL = os.environ["TORCH_BACKEND_URL"]
MOCK_ML_MODELS = os.environ["MOCK_ML_MODELS"] == "true"
REQUEST_SEQ = 0

logging.basicConfig(level=logging.INFO)

def summarize(api_obj, input_string, model):
    # TODO: check length of input string in tokens
    return api_obj.summarize_block(input_string, model)


def send_summarized(session_id, summary_seq, summary_text):
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    summary = {
        "session_id": session_id,
        "summary_seq": summary_seq,
        "summary_text": summary_text
    }
    channel.queue_declare(OUTPUT_QUEUE_NAME, durable=True)
    channel.basic_publish(exchange='', routing_key=OUTPUT_QUEUE_NAME, body=json.dumps(summary))
    connection.close()


def process_input(api_obj, body, logger, tokenizer):
    #TODO: move computation to a worker thread
    deserialized = json.loads(body)
    model = deserialized["model"]
    session_id = deserialized["session_id"]
    summary_seq = deserialized["summary_seq"]
    text = deserialized["text"]
    trsc = transcript.Transcript.from_automin(text)
    trsc.kartik_clean()
    result = f"{summarize(api_obj, trsc, model)}"
    send_summarized(session_id, summary_seq, result)
    logger.info(deserialized)


def init_worker(queue):
    torch_interface = api_interface.TorchInterface(TORCH_BACKEND_URL, MOCK_ML_MODELS)
    # FIXME: tokenizer depends on the model, so this needs to be handled better
    tokenizer = transformers.BartTokenizer.from_pretrained("facebook/bart-large-xsum")
    while True:
        body = queue.get()
        process_input(torch_interface, body, logger, tokenizer)


def callback(ch, method, properties, body):
    queue.put(body)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def get_logger(name):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    return logger


def get_rabbitmq_connection():
    retries = 0
    while retries < MAX_RETRIES:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
            return connection
        except (pika.exceptions.AMQPConnectionError):
            logger.info(f"Waiting for rabbitmq, retry {retries + 1}")
            retries += 1
            time.sleep(1)
    raise Exception("Could not connect to rabbitmq")


if __name__ == "__main__":
    logger = get_logger(__name__)
    logger.info("Starting summarization worker")
    logger.info("Waiting for rabbitmq")
    connection = get_rabbitmq_connection()
    logger.info("Connected to rabbitmq")
    queue = Queue()
    threading.Thread(target=init_worker, args=(queue,), daemon=True).start()
    channel = connection.channel()
    channel.queue_declare(INPUT_QUEUE_NAME, durable=True)
    channel.basic_consume(queue=INPUT_QUEUE_NAME, on_message_callback=callback)
    channel.start_consuming()