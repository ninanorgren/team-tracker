from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired


class TeamNotificationForm(FlaskForm):
    enabled = SelectField(
        "Team notifications",
        choices=[("1", "Enabled"), ("0", "Disabled")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Save")


class ChallengeNotificationForm(FlaskForm):
    mode = SelectField(
        "Challenge notifications",
        choices=[
            ("inherit", "Inherit team setting"),
            ("enabled", "Enabled"),
            ("disabled", "Disabled"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Save")
