from flask import Flask, render_template
from forms import TranscriptInputForm
from transformers import BartTokenizer
import api_interface
import text_utils
import logging


app = Flask(__name__)
# FIXME: stop commiting this to git!
app.config['SECRET_KEY'] = 'lkajflkejfnlaneom zo3r0194fnoaijl'
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-xsum")

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
            minutes = [api_interface.summarize_block(minute) for minute in minutes]
        else:
            minutes = splits
    return render_template("index.html", title="Minuteman", form=form, output=zip(splits, minutes))
