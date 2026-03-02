from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


class CommentForm(FlaskForm):
    body = TextAreaField(
        "Comment",
        validators=[DataRequired(), Length(max=1000)],
    )
    submit = SubmitField("Post comment")
