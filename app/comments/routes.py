from flask import Blueprint, flash, redirect, url_for
from flask_login import current_user, login_required

from app.comments.forms import CommentForm
from app.extensions import db
from app.models import Activity, ActivityComment, Challenge, ChallengeComment, TeamMembership
from app.notifications.service import notify_challenge_event


comments_bp = Blueprint("comments", __name__)


def user_can_access_team(team_id):
    if not current_user.is_authenticated:
        return False

    membership = TeamMembership.query.filter_by(
        team_id=team_id,
        user_id=current_user.id,
    ).first()
    return membership is not None


@comments_bp.route("/activity/<int:id>/comment", methods=["POST"])
@login_required
def create_activity_comment(id):
    activity = Activity.query.get_or_404(id)
    if not user_can_access_team(activity.challenge.team_id):
        flash("Join the team before commenting on its activity.", "warning")
        return redirect(url_for("teams.detail", slug=activity.challenge.team.slug))

    form = CommentForm(prefix=f"activity-{activity.id}")
    if not form.validate_on_submit():
        flash("Comment could not be posted. Please enter a message.", "danger")
        return redirect(url_for("challenges.detail", id=activity.challenge_id))

    comment = ActivityComment(
        activity_id=activity.id,
        user_id=current_user.id,
        body=form.body.data.strip(),
    )
    db.session.add(comment)
    db.session.commit()

    notify_challenge_event(
        challenge_id=activity.challenge_id,
        actor_user_id=current_user.id,
        title=f"{current_user.display_name} commented on activity",
        body=activity.challenge.title,
        url=f"{url_for('challenges.detail', id=activity.challenge_id)}#activity-comment-{comment.id}",
        tag=f"challenge-{activity.challenge_id}-activity-comment-{comment.id}",
    )

    flash("Your comment has been posted.", "success")
    return redirect(url_for("challenges.detail", id=activity.challenge_id))


@comments_bp.route("/challenges/<int:id>/comment", methods=["POST"])
@login_required
def create_challenge_comment(id):
    challenge = Challenge.query.get_or_404(id)
    if not user_can_access_team(challenge.team_id):
        flash("Join the team before commenting on its challenge.", "warning")
        return redirect(url_for("teams.detail", slug=challenge.team.slug))

    form = CommentForm(prefix=f"challenge-{challenge.id}")
    if not form.validate_on_submit():
        flash("Comment could not be posted. Please enter a message.", "danger")
        return redirect(url_for("challenges.detail", id=challenge.id))

    comment = ChallengeComment(
        challenge_id=challenge.id,
        user_id=current_user.id,
        body=form.body.data.strip(),
    )
    db.session.add(comment)
    db.session.commit()

    notify_challenge_event(
        challenge_id=challenge.id,
        actor_user_id=current_user.id,
        title=f"{current_user.display_name} commented on challenge",
        body=challenge.title,
        url=f"{url_for('challenges.detail', id=challenge.id)}#challenge-comment-{comment.id}",
        tag=f"challenge-{challenge.id}-comment-{comment.id}",
    )

    flash("Your comment has been posted.", "success")
    return redirect(url_for("challenges.detail", id=challenge.id))
