from flask_wtf import FlaskForm
from wtforms import TextAreaField
from wtforms.validators import InputRequired

# TODO: the updates to the form should be live, perhaps through some JS framework?
class TranscriptInputForm(FlaskForm):
    transcript = TextAreaField(label="transcript", validators=[InputRequired()])
