import re

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import and_, func
from sqlalchemy.orm import joinedload, selectinload

from app.extensions import db
from app.models import Activity, Challenge, Team, TeamMembership, TeamNotificationSetting, User
from app.notifications.forms import TeamNotificationForm
from app.notifications.service import resolve_team_notification_enabled
from app.teams.forms import JoinTeamForm, TeamDescriptionForm, TeamForm


teams_bp = Blueprint("teams", __name__)


def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "team"


def build_unique_slug(name):
    base_slug = slugify(name)
    slug = base_slug
    counter = 2

    while Team.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


def scoreboard_for_team(team):
    return (
        db.session.query(
            User.id.label("user_id"),
            User.display_name.label("display_name"),
            func.count(Activity.id).label("score"),
        )
        .select_from(TeamMembership)
        .join(User, User.id == TeamMembership.user_id)
        .outerjoin(
            Challenge,
            Challenge.team_id == TeamMembership.team_id,
        )
        .outerjoin(
            Activity,
            and_(
                Activity.challenge_id == Challenge.id,
                Activity.user_id == TeamMembership.user_id,
                Activity.is_checked.is_(True),
            ),
        )
        .filter(TeamMembership.team_id == team.id)
        .group_by(User.id, User.display_name)
        .order_by(func.count(Activity.id).desc(), User.display_name.asc())
        .all()
    )


@teams_bp.route("/teams/create", methods=["GET", "POST"])
@login_required
def create():
    form = TeamForm()
    if form.validate_on_submit():
        team = Team(
            name=form.name.data.strip(),
            slug=build_unique_slug(form.name.data),
            description=form.description.data.strip(),
            created_by_user_id=current_user.id,
        )
        db.session.add(team)
        db.session.flush()

        membership = TeamMembership(team_id=team.id, user_id=current_user.id)
        db.session.add(membership)
        db.session.commit()

        flash(f"{team.name} has been created.", "success")
        return redirect(url_for("teams.detail", slug=team.slug))

    return render_template("teams/create.html", form=form)


@teams_bp.route("/teams")
def index():
    teams = (
        Team.query.options(joinedload(Team.created_by), selectinload(Team.memberships))
        .order_by(Team.name.asc())
        .all()
    )
    joined_team_ids = set()
    if current_user.is_authenticated:
        joined_team_ids = {
            membership.team_id
            for membership in TeamMembership.query.filter_by(user_id=current_user.id).all()
        }

    return render_template(
        "teams/index.html",
        teams=teams,
        joined_team_ids=joined_team_ids,
    )


@teams_bp.route("/teams/<slug>")
def detail(slug):
    team = (
        Team.query.options(
            joinedload(Team.created_by),
            selectinload(Team.memberships).joinedload(TeamMembership.user),
        )
        .filter_by(slug=slug)
        .first_or_404()
    )
    join_form = JoinTeamForm()
    is_member = False
    if current_user.is_authenticated:
        is_member = (
            TeamMembership.query.filter_by(
                team_id=team.id,
                user_id=current_user.id,
            ).first()
            is not None
        )
    if is_member:
        team = (
            Team.query.options(
                joinedload(Team.created_by),
                selectinload(Team.challenges).selectinload(Challenge.memberships),
                selectinload(Team.memberships).joinedload(TeamMembership.user),
            )
            .filter_by(id=team.id)
            .first_or_404()
        )
        scoreboard = scoreboard_for_team(team)
        team_notification_form = TeamNotificationForm(prefix=f"team-notify-{team.id}")
        team_notification_form.enabled.data = (
            "1" if resolve_team_notification_enabled(current_user.id, team.id) else "0"
        )
    else:
        scoreboard = []
        team_notification_form = None

    return render_template(
        "teams/detail.html",
        team=team,
        join_form=join_form,
        is_member=is_member,
        scoreboard=scoreboard,
        team_notification_form=team_notification_form,
    )


@teams_bp.route("/teams/<slug>/edit", methods=["GET", "POST"])
@login_required
def edit(slug):
    team = Team.query.filter_by(slug=slug).first_or_404()
    membership = TeamMembership.query.filter_by(
        team_id=team.id,
        user_id=current_user.id,
    ).first()

    if not membership:
        flash("You must be a team member to edit this description.", "danger")
        return redirect(url_for("teams.detail", slug=team.slug))

    form = TeamDescriptionForm(obj=team)
    if form.validate_on_submit():
        team.description = form.description.data.strip()
        db.session.commit()
        flash("Team description has been updated.", "success")
        return redirect(url_for("teams.detail", slug=team.slug))

    return render_template(
        "teams/edit.html",
        team=team,
        form=form,
    )


@teams_bp.route("/teams/<slug>/join", methods=["POST"])
@login_required
def join(slug):
    team = Team.query.filter_by(slug=slug).first_or_404()
    form = JoinTeamForm()
    if not form.validate_on_submit():
        flash("Unable to join the team. Please try again.", "danger")
        return redirect(url_for("teams.detail", slug=team.slug))

    existing_membership = TeamMembership.query.filter_by(
        team_id=team.id,
        user_id=current_user.id,
    ).first()
    if existing_membership:
        flash("You are already a member of this team.", "info")
        return redirect(url_for("teams.detail", slug=team.slug))

    membership = TeamMembership(team_id=team.id, user_id=current_user.id)
    db.session.add(membership)
    db.session.commit()

    flash(f"You joined {team.name}.", "success")
    return redirect(url_for("teams.detail", slug=team.slug))
