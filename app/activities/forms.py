from datetime import date

from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError


class ActivityForm(FlaskForm):
    activity_date = DateField("Date", validators=[DataRequired()], default=date.today)
    is_checked = BooleanField("Count this as a completed check-in", default=True)
    note = TextAreaField("Note", validators=[Length(max=1000)])
    submit = SubmitField("Save activity")

    def __init__(self, *args, challenge=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.challenge = challenge

    def validate_activity_date(self, field):
        if not self.challenge:
            return

        if field.data < self.challenge.start_date or field.data > self.challenge.end_date:
            raise ValidationError("Activity date must be within the challenge date range.")
