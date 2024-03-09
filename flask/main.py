import atexit
import copy
import logging
import os
import struct
import time
from logging import getLogger

import config
import etherpad_interface
import numpy as np
import pika
import view_utils
from extensions import db
from models import DBInterface

from flask import Flask, abort, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)
# load config from env variables
app_config = config.Config()
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]
app.config["SQLALCHEMY_DATABASE_URI"] = app_config.db_url
db.init_app(app)

# initialize global interfaces with config from env vars
db_interface = DBInterface(app_config)
editor_interface = etherpad_interface.PadInterface(app_config)

# initialize loggers
gunicorn_logger = logging.getLogger("gunicorn.error")
app.logger.handlers = gunicorn_logger.handlers
logger = getLogger(__name__)

default_session_config = view_utils.SessionConfig(200, False, "bart", False)

MAX_RABBITMQ_RETRIES = 200


def get_rabbitmq_connection():
    retries = 0
    while retries < MAX_RABBITMQ_RETRIES:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host="rabbitmq")
            )
            logger.info("Connected to RabbitMQ")
            return connection
        except Exception as e:
            retries += 1
            logger.debug(e)
            logger.error(
                f"Failed to connect to RabbitMQ, retrying in 5s, retry no. {retries}."
            )
            time.sleep(5)
    raise Exception("Could not connect to rabbitmq")


connection = get_rabbitmq_connection()
channel = connection.channel()
channel.queue_declare("audio_chunk_queue")


def cleanup():
    channel.close()
    connection.close()


atexit.register(cleanup)


@app.route("/minuting/<session_id>", methods=["GET", "POST"])
def minuting(session_id):
    if not db_interface.session_exists(session_id):
        abort(404)
    return render_template(
        "index.html",
        title="Minuteman",
        session_id=session_id,
        etherpad_url=app_config.etherpad_url,
    )


# creates a new minuting session, initializes the editors, sets up basic config
@app.route("/new_minuting/", methods=["POST"])
def new_minuting():
    debug = request.form.get("debug_mode_toggle")
    debug = debug == "on"
    config = copy.deepcopy(default_session_config)
    config.debug = debug
    # for local debugging purposes
    if not app_config.mock_ml_models:
        default_model = view_utils.get_torchserve_available_models(
            app_config.torch_management_url
        )[0]
    else:
        default_model = "bart"
    config.summ_model_id = default_model
    id = view_utils.get_random_id(20)
    editor_interface.create_session(id, config)
    db_interface.create_minuteman_session(id, view_utils.get_current_time())
    return redirect(url_for("minuting", session_id=id))


@app.route("/", methods=["GET"])
def about():
    return render_template("about.html")


@app.route("/minuting/<session_id>/set_chunk_len/", methods=["POST"])
def set_chunk_len(session_id):
    chunk_len = request.form.get("chunk_len")
    editor_interface.set_chunk_len(session_id, chunk_len)
    return jsonify({"status_code": 200, "message": "ok"})


@app.route("/minuting/<session_id>/set_summ_model/", methods=["POST"])
def set_summ_model(session_id):
    print("setting summ model")
    summ_model = request.form.get("summ_model")
    # local debugging purposes
    if not app_config.mock_ml_models:
        model_selection = view_utils.get_torchserve_available_models(
            app_config.torch_management_url
        )
    else:
        model_selection = ["bart", "t5", "gpt2"]
    if summ_model not in model_selection:
        return jsonify({"status_code": 400, "message": "Unavailable model"})
    else:
        editor_interface.set_summ_model(session_id, summ_model)
        return jsonify({"status_code": 200, "message": "ok"})


@app.route("/minuting/<session_id>/transcribe/", methods=["POST"])
def transcribe(session_id):
    float_array = []
    timestamp = view_utils.datetime_from_iso(request.form.get("timestamp"))
    author = request.form.get("author")
    recorder_id = request.form.get("recorder_id")
    chunk = request.files.get("chunk")
    binary_data = chunk.read()

    for i in range(0, len(binary_data), 4):
        float_value = struct.unpack("<f", binary_data[i : i + 4])[0]
        float_array.append(float_value)

    float_array = np.array(float_array)
    chunk = view_utils.create_audio_chunk(
        session_id, author, recorder_id, timestamp, float_array
    )

    global channel
    if not channel.is_open:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare("audio_chunk_queue")

    channel.basic_publish(
        exchange="",
        routing_key="audio_chunk_queue",
        body=view_utils.serialize_dict(chunk),
    )
    return jsonify({"status_code": 200, "message": "ok"})


@app.route("/minuting/<session_id>/get_state/", methods=["GET"])
def get_state(session_id):
    try:
        session_config = editor_interface.get_session_config(session_id)
    except ValueError:
        # This is here as a placeholder for old sessions, so that the error messages
        # do not cover up all other output
        pass
    if not app_config.mock_ml_models:
        model_selection = view_utils.get_torchserve_available_models(
            app_config.torch_management_url
        )
    else:
        # mocking for development purposes
        model_selection = ["bart", "t5", "gpt2"]
    return jsonify(
        {
            "status_code": 200,
            "message": "ok",
            "config": session_config,
            "model_selection": model_selection,
        }
    )
