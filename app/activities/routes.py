from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload, selectinload

from app.comments.forms import CommentForm
from app.activities.forms import ActivityForm
from app.extensions import db
from app.models import Activity, ActivityComment, Challenge, ChallengeMembership


activities_bp = Blueprint("activities", __name__)


def get_joined_challenge_or_404(challenge_id):
    challenge = Challenge.query.filter_by(id=challenge_id).first_or_404()
    membership = ChallengeMembership.query.filter_by(
        challenge_id=challenge.id,
        user_id=current_user.id,
    ).first()
    if not membership:
        return None
    return challenge


@activities_bp.route("/challenges/<int:id>/checkin", methods=["GET", "POST"])
@login_required
def checkin(id):
    challenge = get_joined_challenge_or_404(id)
    if challenge is None:
        flash("Join this challenge before logging an activity.", "warning")
        return redirect(url_for("challenges.detail", id=id))

    form = ActivityForm(challenge=challenge)
    if form.validate_on_submit():
        existing_activity = Activity.query.filter_by(
            challenge_id=challenge.id,
            user_id=current_user.id,
            activity_date=form.activity_date.data,
        ).first()
        if existing_activity:
            flash("You already have an activity for that date. Edit it instead.", "info")
            return redirect(url_for("activities.edit", id=existing_activity.id))

        activity = Activity(
            challenge_id=challenge.id,
            user_id=current_user.id,
            activity_date=form.activity_date.data,
            is_checked=form.is_checked.data,
            note=form.note.data.strip(),
        )
        db.session.add(activity)
        db.session.commit()

        flash("Your activity has been logged.", "success")
        return redirect(url_for("challenges.detail", id=challenge.id))

    return render_template("activities/checkin.html", form=form, challenge=challenge)


@activities_bp.route("/activity/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    activity = (
        Activity.query.options(
            joinedload(Activity.challenge),
            joinedload(Activity.user),
            joinedload(Activity.challenge).joinedload(Challenge.team),
            selectinload(Activity.comments).joinedload(ActivityComment.user),
        )
        .filter_by(id=id, user_id=current_user.id)
        .first_or_404()
    )
    form = ActivityForm(obj=activity, challenge=activity.challenge)
    if form.validate_on_submit():
        existing_activity = (
            Activity.query.filter_by(
                challenge_id=activity.challenge_id,
                user_id=current_user.id,
                activity_date=form.activity_date.data,
            )
            .filter(Activity.id != activity.id)
            .first()
        )
        if existing_activity:
            flash("You already have another activity for that date.", "danger")
            return redirect(url_for("activities.edit", id=activity.id))

        activity.activity_date = form.activity_date.data
        activity.is_checked = form.is_checked.data
        activity.note = form.note.data.strip()
        db.session.commit()

        flash("Your activity has been updated.", "success")
        return redirect(url_for("challenges.detail", id=activity.challenge_id))

    comment_form = CommentForm(prefix=f"activity-{activity.id}")
    return render_template(
        "activities/edit.html",
        form=form,
        activity=activity,
        comment_form=comment_form,
    )
