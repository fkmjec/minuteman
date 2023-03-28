import logging
import os

import api_interface
import view_utils
import text_utils
import config
from flask import Flask, jsonify, render_template, request, redirect, url_for
from forms import TranscriptInputForm
from transformers import BartTokenizer

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['FLASK_SECRET_KEY']

# automatically
app_config = config.Config()
torch_interface = api_interface.TorchInterface(app_config)

# FIXME: this should be more structured
tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-xsum")
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
    return redirect(url_for('minuting', session_id=id))


@app.route("/transcribe", methods=["POST"])
def add_transcript():
    logging.debug("Received request to transcribe")
    chunk = request.data
    transcribed_text = torch_interface.transcribe_chunk(chunk)
    return jsonify({"transcript": transcribed_text})