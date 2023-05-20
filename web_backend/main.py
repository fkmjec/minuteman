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
from extensions import db

app = Flask(__name__)
# load config from env variables
app_config = config.Config()
app.config['SECRET_KEY'] = os.environ['FLASK_SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = app_config.db_url
db.init_app(app)

# initialize global interfaces with config from env vars
torch_interface = api_interface.TorchInterface(app_config)
db_interface = DBInterface(app_config)
editor_interface = etherpad_interface.PadInterface(app_config)
tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-xsum")

# FIXME: this should be more structured
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers

def update_minutes(session_id, transcript, past_minutes):
    splits = text_utils.split_by_trsc_separator(transcript)
    last_split = splits[-1]
    minutes = [torch_interface.summarize_block(split) for split in splits]
    i = 0
    chars_before = 0
    for minute, split in zip(minutes[0:-1], splits[0:-1]):
        # app.logger.info(split)
        split_len = len(split)
        line_id = session_id + "-" + str(i)
        # FIXME: this is going to be slow
        already_generated = False
        for past_minute in past_minutes:
            m_id = past_minute[0]
            if m_id == line_id:
                already_generated = True
        if already_generated:
            editor_interface.update_summ_line(session_id, minute, line_id)
        else:
            editor_interface.add_summ_line(session_id, minute, line_id, chars_before, chars_before + split_len + 1)
        i += 1
        chars_before += split_len + 1
    
    # append new line if it has one full segment
    last_splits = text_utils.split_to_lens(last_split, app_config.max_input_len, tokenizer)
    if len(last_splits) > 1:
        last_minute = torch_interface.summarize_block(last_splits[0])
        last_line_id = session_id + "-" + str(i)
        editor_interface.add_summ_line(session_id, last_minute, last_line_id, chars_before, chars_before + len(last_splits[0]) + 1)


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
    transcript = editor_interface.get_transcript(session_id)
    past_minutes = editor_interface.get_minutes(session_id)
    update_minutes(session_id, transcript, past_minutes)
    # we get the transcript here because it could have been edited by users
    return jsonify({"transcript": transcribed_text})


# API endpoint for notification from the pad that either a summary or a transcript was edited by the user
# called from the ep_minuteman plugin
@app.route("/pad_change/<pad_id>", methods=["POST"])
def pad_change(pad_id):
    # check that the pad is of the transcript kind
    try:
        session_id, session_type = editor_interface.session_id_from_pad(pad_id)
        # TODO: use an enum here
        if db_interface.session_exists(session_id) and session_type == "trsc":
            # TODO: throttle requests.
            # we only need to react to transcript changes as reacting to summary changes would lead to infinite loops
            transcript = editor_interface.get_transcript(session_id)
            past_minutes = editor_interface.get_minutes(session_id)
            update_minutes(session_id, transcript, past_minutes)
            # return ok response
            return jsonify({"status_code": 200, "message": "ok"})
        else:
            return jsonify({"status_code": 200, "message": "ok"})
    except ValueError as va:
        logging.debug("Got valueChange from another editor! People seem to be using it liberally!")
        return jsonify({"status_code": 200, "message": "ok"})
