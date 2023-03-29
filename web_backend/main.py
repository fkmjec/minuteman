import logging
import os

import api_interface
import view_utils
import text_utils
import config
from models import DBInterface
from flask import Flask, jsonify, render_template, request, redirect, url_for
from forms import TranscriptInputForm
from transformers import BartTokenizer

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['FLASK_SECRET_KEY']

# initialize global interfaces with config from env vars
app_config = config.Config()
torch_interface = api_interface.TorchInterface(app_config)
db_interface = DBInterface(app_config)
tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-xsum")

# FIXME: this should be more structured
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel("DEBUG")

@app.route("/minuting/<session_id>", methods=["GET", "POST"])
def minuting(session_id):
    form = TranscriptInputForm()

    minutes = []
    splits = []
    if form.validate_on_submit():
        splits = text_utils.split_to_lens(form.transcript.data, app_config.max_input_len, tokenizer)
        minutes = [torch_interface.summarize_block(split) for split in splits]
    return render_template("index.html", title="Minuteman", form=form, output=zip(splits, minutes))


@app.route("/", methods=["GET"])
def index():
    id = view_utils.get_random_id(20)
    db_interface.create_minuteman_session(id, view_utils.get_current_time())
    return redirect(url_for('minuting', session_id=id))


@app.route("/transcribe/<session_id>", methods=["POST"])
def add_transcript(session_id):
    logging.debug("Received request to transcribe")
    timestamp = request.form.get("timestamp")
    chunk = request.form.get("chunk")
    transcribed_text = torch_interface.transcribe_chunk(chunk)
    return jsonify({"transcript": transcribed_text})