import argparse
import json
import logging
import time

import pika
import transcript

parser = argparse.ArgumentParser(
    description="Mock transcript creation by sending utterances to a queue"
)
parser.add_argument("--rabbitmq_host", type=str, default="rabbitmq")
parser.add_argument("--session_id", type=str, required=True)
parser.add_argument("--transcript_path", type=str, required=True)
parser.add_argument(
    "--simulate_conversation",
    action="store_true",
    required=True,
    help="Append utterances in roughly the same time they probably took to say",
)


MAX_RETRIES = 200
WORDS_PER_MINUTE = 300
INPUT_QUEUE_NAME = "transcript_queue"

logging.basicConfig(level=logging.INFO)


def load_transcript(path):
    with open(path, "r") as f:
        string = f.read()
        trsc = transcript.Transcript.from_automin(string)
        return trsc


def send_utterances(trsc, channel, session_id, simulate_conversation):
    seq = 0
    for role, utterance in zip(trsc.roles, trsc.utterances):
        utterance_text = f"{role}: {utterance}\n"
        timestamp = time.time()
        utterance_obj = {
            "utterance": utterance_text,
            "session_id": session_id,
            "timestamp": str(timestamp),
            "seq": seq,
        }
        channel.queue_declare("transcript_queue", durable=True)
        channel.basic_publish(
            exchange="", routing_key="transcript_queue", body=json.dumps(utterance_obj)
        )
        seq += 1
        if simulate_conversation:
            words = len(utterance.split(" "))
            len_in_sec = words / WORDS_PER_MINUTE * 60
            time.sleep(len_in_sec)
        else:
            time.sleep(1)


if __name__ == "__main__":
    # we now assume one worker, maybe we will scale to more later
    logger = logging.getLogger(__name__)
    args = parser.parse_args()
    logger.setLevel(logging.INFO)
    logger.info("Starting summarization worker")
    retries = 0
    while retries < 20:
        try:
            # FIXME: disabled heartbeats for now, because threading would be way too complex
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=args.rabbitmq_host, heartbeat=0)
            )
            break
        except pika.exceptions.AMQPConnectionError:
            logger.info(f"Waiting for rabbitmq, retry {retries + 1}")
            retries += 1
            time.sleep(1)
    channel = connection.channel()
    trsc = load_transcript(args.transcript_path)
    send_utterances(trsc, channel, args.session_id, args.simulate_conversation)
