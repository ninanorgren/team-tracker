from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError


class JoinChallengeForm(FlaskForm):
    submit = SubmitField("Join challenge")


class ChallengeForm(FlaskForm):
    team_id = SelectField("Team", coerce=int, validators=[DataRequired()])
    title = StringField(
        "Title",
        validators=[DataRequired(), Length(max=255)],
    )
    description = TextAreaField(
        "Description",
        validators=[DataRequired(), Length(max=1000)],
    )
    start_date = DateField("Start date", validators=[DataRequired()])
    end_date = DateField("End date", validators=[DataRequired()])
    frequency_per_week = SelectField(
        "Check-ins per week",
        coerce=int,
        validators=[DataRequired(), NumberRange(min=1, max=7)],
        choices=[(value, str(value)) for value in range(1, 8)],
    )
    submit = SubmitField("Create challenge")

    def validate_end_date(self, field):
        if self.start_date.data and field.data and field.data < self.start_date.data:
            raise ValidationError("End date must be on or after the start date.")
