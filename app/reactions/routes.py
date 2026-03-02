from flask import Blueprint, flash, redirect, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Activity, ActivityReaction, Challenge, TeamMembership
from app.reactions.forms import ReactionForm


reactions_bp = Blueprint("reactions", __name__)


def user_can_access_activity(activity):
    membership = TeamMembership.query.filter_by(
        team_id=activity.challenge.team_id,
        user_id=current_user.id,
    ).first()
    return membership is not None


@reactions_bp.route("/activity/<int:id>/react", methods=["POST"])
@login_required
def toggle_activity_reaction(id):
    activity = (
        Activity.query.options(joinedload(Activity.challenge).joinedload(Challenge.team))
        .filter_by(id=id)
        .first_or_404()
    )
    if not user_can_access_activity(activity):
        flash("Join the team before reacting to its activity.", "warning")
        return redirect(url_for("teams.detail", slug=activity.challenge.team.slug))

    form = ReactionForm(prefix=f"reaction-{activity.id}")
    if not form.validate_on_submit():
        flash("That reaction is not available.", "danger")
        return redirect(url_for("challenges.detail", id=activity.challenge_id))

    existing_reaction = ActivityReaction.query.filter_by(
        activity_id=activity.id,
        user_id=current_user.id,
        emoji=form.emoji.data,
    ).first()
    if existing_reaction:
        db.session.delete(existing_reaction)
        flash("Reaction removed.", "info")
    else:
        reaction = ActivityReaction(
            activity_id=activity.id,
            user_id=current_user.id,
            emoji=form.emoji.data,
        )
        db.session.add(reaction)
        flash("Reaction added.", "success")

    db.session.commit()
    return redirect(url_for("challenges.detail", id=activity.challenge_id))
