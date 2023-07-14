import logging
import os
import struct

import etherpad_interface
import view_utils
import config
from models import DBInterface
from flask import Flask, jsonify, render_template, request, redirect, url_for, abort
from extensions import db
import numpy as np
import copy
import pika


app = Flask(__name__)
# load config from env variables
app_config = config.Config()
app.config['SECRET_KEY'] = os.environ['FLASK_SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = app_config.db_url
db.init_app(app)

# initialize global interfaces with config from env vars
db_interface = DBInterface(app_config)
editor_interface = etherpad_interface.PadInterface(app_config)

# initialize loggers
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers

# FIXME: what is the default summarization model? we do not know automatically yet
default_session_config = view_utils.SessionConfig(200, False, "bart")

@app.route("/minuting/<session_id>", methods=["GET", "POST"])
def minuting(session_id):
    if not db_interface.session_exists(session_id):
        abort(404)
    return render_template("index.html", title="Minuteman", session_id=session_id, etherpad_url=app_config.etherpad_url)


# creates a new minuting session, initializes the editors, sets up basic config
@app.route("/new_minuting/", methods=["POST"])
def new_minuting():
    debug = request.form.get("debug_mode_toggle")
    debug = debug == "on"
    config = copy.deepcopy(default_session_config)
    config.debug = debug
    id = view_utils.get_random_id(20)
    db_interface.create_minuteman_session(id, view_utils.get_current_time())
    editor_interface.create_session(id, config)
    return redirect(url_for('minuting', session_id=id))


@app.route("/", methods=["GET"])
def about():
    return render_template("about.html")


@app.route("/minuting/<session_id>/set_chunk_len/", methods=["POST"])
def set_chunk_len(session_id):
    chunk_len = request.form.get("chunk_len")
    editor_interface.set_chunk_len(session_id, chunk_len)
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
        float_value = struct.unpack('<f', binary_data[i:i+4])[0]
        float_array.append(float_value)

    float_array = np.array(float_array)
    chunk = view_utils.create_audio_chunk(session_id, author, recorder_id, timestamp, float_array)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.queue_declare("audio_chunk_queue")
    channel.basic_publish(exchange='', routing_key='audio_chunk_queue', body=view_utils.serialize_dict(chunk))
    connection.close()
    return jsonify({"status_code": 200, "message": "ok"})


@app.route("/minuting/<session_id>/get_state/", methods=["GET"])
def get_state(session_id):
    session_config = editor_interface.get_session_config(session_id)
    if not app_config.mock_ml_models:
        model_selection = view_utils.get_torchserve_available_models(app_config.torch_management_url)
    else:
        # mocking for development purposes
        model_selection = ["bart", "t5", "gpt2"]

    return jsonify({"status_code": 200, "message": "ok", "config": session_config, "model_selection": model_selection})
