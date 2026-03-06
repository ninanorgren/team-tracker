from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import and_, func
from sqlalchemy.orm import joinedload, selectinload

from app.comments.forms import CommentForm
from app.challenges.forms import ChallengeForm, JoinChallengeForm
from app.extensions import db
from app.models import (
    Activity,
    ActivityComment,
    ActivityReaction,
    Challenge,
    ChallengeNotificationSetting,
    ChallengeComment,
    ChallengeMembership,
    Team,
    TeamMembership,
    User,
)
from app.notifications.forms import ChallengeNotificationForm
from app.notifications.service import (
    resolve_challenge_notification_enabled,
    resolve_team_notification_enabled,
)
from app.reactions.forms import REACTION_EMOJIS, ReactionForm


challenges_bp = Blueprint("challenges", __name__)


def challenge_team_choices():
    teams = (
        Team.query.join(TeamMembership, TeamMembership.team_id == Team.id)
        .filter(TeamMembership.user_id == current_user.id)
        .order_by(Team.name.asc())
        .all()
    )
    return [(team.id, team.name) for team in teams]


def user_can_access_challenge(challenge):
    if not current_user.is_authenticated:
        return False

    membership = TeamMembership.query.filter_by(
        team_id=challenge.team_id,
        user_id=current_user.id,
    ).first()
    return membership is not None


def scoreboard_for_challenge(challenge):
    return (
        db.session.query(
            User.id.label("user_id"),
            User.display_name.label("display_name"),
            func.count(Activity.id).label("score"),
        )
        .select_from(ChallengeMembership)
        .join(User, User.id == ChallengeMembership.user_id)
        .outerjoin(
            Activity,
            and_(
                Activity.challenge_id == ChallengeMembership.challenge_id,
                Activity.user_id == ChallengeMembership.user_id,
                Activity.is_checked.is_(True),
                Activity.activity_date >= challenge.start_date,
                Activity.activity_date <= challenge.end_date,
            ),
        )
        .filter(
            ChallengeMembership.challenge_id == challenge.id,
        )
        .group_by(User.id, User.display_name)
        .order_by(func.count(Activity.id).desc(), User.display_name.asc())
        .all()
    )


@challenges_bp.route("/challenges/create", methods=["GET", "POST"])
@login_required
def create():
    form = ChallengeForm()
    form.team_id.choices = challenge_team_choices()

    if not form.team_id.choices:
        flash("Create a team before creating a challenge.", "warning")
        return redirect(url_for("teams.index"))

    requested_team_id = request.args.get("team", type=int)
    if request.method == "GET" and requested_team_id:
        team_ids = {team_id for team_id, _ in form.team_id.choices}
        if requested_team_id in team_ids:
            form.team_id.data = requested_team_id

    if form.validate_on_submit():
        challenge = Challenge(
            team_id=form.team_id.data,
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            frequency_per_week=form.frequency_per_week.data,
        )
        db.session.add(challenge)
        db.session.flush()

        membership = ChallengeMembership(
            challenge_id=challenge.id,
            user_id=current_user.id,
        )
        db.session.add(membership)
        db.session.commit()

        flash(f"{challenge.title} has been created.", "success")
        return redirect(url_for("challenges.detail", id=challenge.id))

    return render_template("challenges/create.html", form=form)


@challenges_bp.route("/challenges/<int:id>")
def detail(id):
    challenge = (
        Challenge.query.options(
            joinedload(Challenge.team),
            selectinload(Challenge.comments).joinedload(ChallengeComment.user),
            selectinload(Challenge.memberships).joinedload(ChallengeMembership.user),
        )
        .filter_by(id=id)
        .first_or_404()
    )
    if not user_can_access_challenge(challenge):
        flash("Join the team before viewing its challenges.", "warning")
        return redirect(url_for("teams.detail", slug=challenge.team.slug))

    join_form = JoinChallengeForm()
    is_member = any(membership.user_id == current_user.id for membership in challenge.memberships)
    activities = (
        Activity.query.options(
            joinedload(Activity.user),
            selectinload(Activity.comments).joinedload(ActivityComment.user),
            selectinload(Activity.reactions).joinedload(ActivityReaction.user),
        )
        .filter_by(challenge_id=challenge.id)
        .order_by(Activity.activity_date.desc(), Activity.created_at.desc())
        .limit(20)
        .all()
    )
    scoreboard = scoreboard_for_challenge(challenge)
    challenge_comment_form = CommentForm(prefix=f"challenge-{challenge.id}")
    activity_comment_forms = {
        activity.id: CommentForm(prefix=f"activity-{activity.id}") for activity in activities
    }
    activity_reaction_forms = {}
    reaction_summaries = {}
    current_user_id = current_user.id if current_user.is_authenticated else None
    for activity in activities:
        activity_reaction_forms[activity.id] = ReactionForm(prefix=f"reaction-{activity.id}")
        reaction_summaries[activity.id] = {
            emoji: {"count": 0, "reacted": False} for emoji in REACTION_EMOJIS
        }
        for reaction in activity.reactions:
            if reaction.emoji not in reaction_summaries[activity.id]:
                continue
            reaction_summaries[activity.id][reaction.emoji]["count"] += 1
            if current_user_id is not None and reaction.user_id == current_user_id:
                reaction_summaries[activity.id][reaction.emoji]["reacted"] = True

    challenge_notification_form = ChallengeNotificationForm(prefix=f"challenge-notify-{challenge.id}")
    challenge_setting = ChallengeNotificationSetting.query.filter_by(
        challenge_id=challenge.id,
        user_id=current_user.id,
    ).first()
    if challenge_setting is None:
        challenge_notification_form.mode.data = "inherit"
        challenge_notification_mode = "inherit"
    elif challenge_setting.enabled:
        challenge_notification_form.mode.data = "enabled"
        challenge_notification_mode = "enabled"
    else:
        challenge_notification_form.mode.data = "disabled"
        challenge_notification_mode = "disabled"

    effective_notifications_enabled, effective_notifications_source = (
        resolve_challenge_notification_enabled(
            current_user.id,
            challenge.team_id,
            challenge.id,
        )
    )
    team_notifications_enabled = resolve_team_notification_enabled(
        current_user.id,
        challenge.team_id,
    )

    return render_template(
        "challenges/detail.html",
        challenge=challenge,
        join_form=join_form,
        is_member=is_member,
        activities=activities,
        scoreboard=scoreboard,
        challenge_comment_form=challenge_comment_form,
        activity_comment_forms=activity_comment_forms,
        activity_reaction_forms=activity_reaction_forms,
        reaction_summaries=reaction_summaries,
        reaction_emojis=REACTION_EMOJIS,
        challenge_notification_form=challenge_notification_form,
        challenge_notification_mode=challenge_notification_mode,
        effective_notifications_enabled=effective_notifications_enabled,
        effective_notifications_source=effective_notifications_source,
        team_notifications_enabled=team_notifications_enabled,
    )


@challenges_bp.route("/challenges/<int:id>/join", methods=["POST"])
@login_required
def join(id):
    challenge = Challenge.query.filter_by(id=id).first_or_404()
    if not user_can_access_challenge(challenge):
        flash("Join the team before joining its challenges.", "warning")
        return redirect(url_for("teams.detail", slug=challenge.team.slug))

    form = JoinChallengeForm()
    if not form.validate_on_submit():
        flash("Unable to join the challenge. Please try again.", "danger")
        return redirect(url_for("challenges.detail", id=challenge.id))

    existing_membership = ChallengeMembership.query.filter_by(
        challenge_id=challenge.id,
        user_id=current_user.id,
    ).first()
    if existing_membership:
        flash("You are already part of this challenge.", "info")
        return redirect(url_for("challenges.detail", id=challenge.id))

    membership = ChallengeMembership(
        challenge_id=challenge.id,
        user_id=current_user.id,
    )
    db.session.add(membership)
    db.session.commit()

    flash(f"You joined {challenge.title}.", "success")
    return redirect(url_for("challenges.detail", id=challenge.id))
