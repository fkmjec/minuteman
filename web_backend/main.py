import logging

import api_interface
import text_utils
from flask import Flask, jsonify, render_template, request
from forms import TranscriptInputForm
from transformers import BartTokenizer

app = Flask(__name__)
# FIXME: stop commiting this to git!
app.config['SECRET_KEY'] = 'lkajflkejfnlaneom zo3r0194fnoaijl'

tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-xsum")
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel("DEBUG")

MAX_INPUT_LEN = 512
USE_BACKEND_MODEL = True

@app.route("/", methods=["GET", "POST"])
def index():
    form = TranscriptInputForm()

    minutes = []
    splits = []
    if form.validate_on_submit():
        splits = text_utils.split_to_lens(form.transcript.data, MAX_INPUT_LEN, tokenizer)
        if USE_BACKEND_MODEL:
            minutes = [api_interface.summarize_block(split) for split in splits]
        else:
            minutes = splits
    return render_template("index.html", title="Minuteman", form=form, output=zip(splits, minutes))


@app.route("/transcribe", methods=["POST"])
def transcribe():
    logging.debug("Received request to transcribe")
    # we assume the chunk is a ~30 second wav file
    # print(request.data)
    chunk = request.data
    logging.debug("Making request to Whisper API")
    transcribed_text = api_interface.transcribe_chunk(chunk)
    logging.debug(f"Response from Whisper API: {transcribed_text}")
    return jsonify({"transcript": transcribed_text})