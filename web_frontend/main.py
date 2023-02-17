from flask import Flask, render_template
from forms import TranscriptInputForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lkajflkejfnlaneom zo3r0194fnoaijl'


@app.route("/", methods=["GET", "POST"])
def index():
    form = TranscriptInputForm()

    minutes = ""
    if form.validate_on_submit():
        # send to the model
        minutes = form.transcript.data
    return render_template("index.html", title="Minuteman", form=form, minutes=minutes)
