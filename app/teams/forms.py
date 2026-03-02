from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


class JoinTeamForm(FlaskForm):
    submit = SubmitField("Join team")


class TeamForm(FlaskForm):
    name = StringField(
        "Team name",
        validators=[DataRequired(), Length(max=120)],
    )
    description = TextAreaField(
        "Description",
        validators=[DataRequired(), Length(max=1000)],
    )
    submit = SubmitField("Create team")
