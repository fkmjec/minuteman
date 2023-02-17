from flask import Flask, render_template
from forms import TranscriptInputForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lkajflkejfnlaneom zo3r0194fnoaijl'


@app.route("/", methods=["GET", "POST"])
def index():
    form = TranscriptInputForm()
    return render_template("index.html", title="Minuteman", form=form)
