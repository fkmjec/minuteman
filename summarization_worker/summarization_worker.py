import logging
import time
import pika
import json
import os
import api_interface

MAX_RETRIES = 200
INPUT_QUEUE_NAME = "summary_input_queue"
OUTPUT_QUEUE_NAME = "summary_result_queue"
TORCH_BACKEND_URL = os.environ["TORCH_BACKEND_URL"]
MOCK_ML_MODELS = os.environ["MOCK_ML_MODELS"] == "true"
REQUEST_SEQ = 0

logging.basicConfig(level=logging.INFO)

def summarize(input_string):
    torch_interface = api_interface.TorchInterface(TORCH_BACKEND_URL, MOCK_ML_MODELS)
    # TODO: check length of input string in tokens
    return torch_interface.summarize_block(input_string)


def send_summarized(session_id, summary_seq, summary_text):
    summary = {
        "session_id": session_id,
        "summary_seq": summary_seq,
        "summary_text": summary_text
    }
    channel.queue_declare(OUTPUT_QUEUE_NAME, durable=True)
    channel.basic_publish(exchange='', routing_key=OUTPUT_QUEUE_NAME, body=json.dumps(summary))


def callback(ch, method, properties, body):
    #TODO: move computation to a worker thread
    deserialized = json.loads(body)
    session_id = deserialized["session_id"]
    summary_seq = deserialized["summary_seq"]
    text = deserialized["text"]
    user_edit = deserialized["user_edit"]
    result = f"{summary_seq}/{user_edit}: {summarize(text)}\n"
    send_summarized(session_id, summary_seq, result)
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
    torch_interface = api_interface.TorchInterface(TORCH_BACKEND_URL, MOCK_ML_MODELS)
    channel = connection.channel()
    channel.queue_declare(INPUT_QUEUE_NAME, durable=True)
    channel.basic_consume(queue=INPUT_QUEUE_NAME, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()