import logging
import os

import api_interface
import etherpad_interface
import view_utils
import text_utils
import config
from models import DBInterface
from flask import Flask, jsonify, render_template, request, redirect, url_for, abort
from forms import TranscriptInputForm
from transformers import BartTokenizer

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['FLASK_SECRET_KEY']

# initialize global interfaces with config from env vars
app_config = config.Config()
torch_interface = api_interface.TorchInterface(app_config)
db_interface = DBInterface(app_config)
editor_interface = etherpad_interface.PadInterface(app_config)
tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-xsum")

# FIXME: this should be more structured
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel("DEBUG")

@app.route("/minuting/<session_id>", methods=["GET", "POST"])
def minuting(session_id):
    if not db_interface.session_exists(session_id):
        abort(404)
    # past_utterances = db_interface.get_past_utterances(session_id)
    return render_template("index.html", title="Minuteman", session_id=session_id)


@app.route("/", methods=["GET"])
def index():
    id = view_utils.get_random_id(20)
    db_interface.create_minuteman_session(id, view_utils.get_current_time())
    editor_interface.create_pad_stack(id)
    print(id)
    return redirect(url_for('minuting', session_id=id))


@app.route("/transcribe/<session_id>", methods=["POST"])
def add_transcript(session_id):
    logging.debug("Received request to transcribe")
    timestamp = view_utils.datetime_from_iso(request.form.get("timestamp"))
    author = request.form.get("author")
    chunk = request.files.get("chunk")
    transcribed_text = torch_interface.transcribe_chunk(chunk)
    db_interface.store_utterance(session_id, transcribed_text, timestamp, author)

    editor_interface.add_trsc_line(session_id, view_utils.get_formatted_utterance(author, transcribed_text))
    # we get the transcript here because it could have been edited by users
    transcript = editor_interface.get_transcript(session_id)
    splits = text_utils.split_to_lens(transcript, app_config.max_input_len, tokenizer)
    minutes = [torch_interface.summarize_block(split) for split in splits]
    i = 0
    for minute in minutes:
        line_id = session_id + "-" + str(i)
        editor_interface.add_summ_line(session_id, minute, line_id)
    return jsonify({"transcript": transcribed_text})