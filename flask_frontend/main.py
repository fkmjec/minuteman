import logging
import os
import struct

import etherpad_interface
import view_utils
import config
from models import DBInterface
from flask import Flask, jsonify, render_template, request, redirect, url_for, abort
from forms import TranscriptInputForm
from extensions import db
import numpy as np
import pika

TARGET_SAMPLE_RATE = 16000
SRC_SAMPLE_RATE = 44100.0

app = Flask(__name__)
# load config from env variables
app_config = config.Config()
app.config['SECRET_KEY'] = os.environ['FLASK_SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = app_config.db_url
db.init_app(app)

# initialize global interfaces with config from env vars
db_interface = DBInterface(app_config)
editor_interface = etherpad_interface.PadInterface(app_config)

# FIXME: this should be more structured
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers


@app.route("/minuting/<session_id>", methods=["GET", "POST"])
def minuting(session_id):
    if not db_interface.session_exists(session_id):
        abort(404)
    # past_utterances = db_interface.get_past_utterances(session_id)
    return render_template("index.html", title="Minuteman", session_id=session_id, etherpad_url=app_config.etherpad_url)


@app.route("/", methods=["GET"])
def index():
    id = view_utils.get_random_id(20)
    db_interface.create_minuteman_session(id, view_utils.get_current_time())
    editor_interface.create_pad_stack(id)
    return redirect(url_for('minuting', session_id=id))


# placeholder endpoint for the development of the new ASR api
@app.route("/transcribe/<session_id>", methods=["POST"])
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
    # float_array = signal.resample_poly(float_array, TARGET_SAMPLE_RATE)
    print(len(float_array))
    chunk = view_utils.create_audio_chunk(session_id, author, recorder_id, timestamp, float_array)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.queue_declare("audio_chunk_queue")
    channel.basic_publish(exchange='', routing_key='audio_chunk_queue', body=view_utils.serialize_dict(chunk))
    connection.close()
    return jsonify({"status_code": 200, "message": "ok"})
