import json

from flask import Blueprint, current_app, flash, jsonify, redirect, request, url_for
from flask_login import current_user, login_required
from pywebpush import WebPushException

from app.extensions import db
from app.models import (
    Challenge,
    ChallengeNotificationSetting,
    PushSubscription,
    Team,
    TeamMembership,
    TeamNotificationSetting,
)
from app.notifications.forms import ChallengeNotificationForm, TeamNotificationForm
from app.notifications.service import is_gone_subscription, send_web_push


notifications_bp = Blueprint("notifications", __name__)


def push_enabled_or_503():
    if not current_app.config["PUSH_NOTIFICATIONS_ENABLED"]:
        return jsonify({"error": "Push notifications are not configured."}), 503
    return None


def team_membership_or_none(team_id, user_id):
    return TeamMembership.query.filter_by(team_id=team_id, user_id=user_id).first()


@notifications_bp.route("/notifications/push/public-key", methods=["GET"])
@login_required
def public_key():
    unavailable = push_enabled_or_503()
    if unavailable:
        return unavailable
    return jsonify({"publicKey": current_app.config["VAPID_PUBLIC_KEY"]})


@notifications_bp.route("/notifications/push/subscribe", methods=["POST"])
@login_required
def subscribe():
    unavailable = push_enabled_or_503()
    if unavailable:
        return unavailable

    payload = request.get_json(silent=True) or {}
    endpoint = (payload.get("endpoint") or "").strip()
    keys = payload.get("keys") or {}
    p256dh_key = (keys.get("p256dh") or "").strip()
    auth_key = (keys.get("auth") or "").strip()

    if not endpoint or not p256dh_key or not auth_key:
        return jsonify({"error": "Invalid subscription payload."}), 400

    subscription = PushSubscription.query.filter_by(endpoint=endpoint).first()
    if subscription is None:
        subscription = PushSubscription(
            user_id=current_user.id,
            endpoint=endpoint,
            p256dh_key=p256dh_key,
            auth_key=auth_key,
            user_agent=(request.headers.get("User-Agent") or "")[:255],
        )
        db.session.add(subscription)
    else:
        subscription.user_id = current_user.id
        subscription.p256dh_key = p256dh_key
        subscription.auth_key = auth_key
        subscription.user_agent = (request.headers.get("User-Agent") or "")[:255]
        subscription.is_active = True

    db.session.commit()
    return jsonify({"status": "ok"})


@notifications_bp.route("/notifications/push/unsubscribe", methods=["POST"])
@login_required
def unsubscribe():
    payload = request.get_json(silent=True) or {}
    endpoint = (payload.get("endpoint") or "").strip()
    if not endpoint:
        return jsonify({"error": "Endpoint is required."}), 400

    subscription = PushSubscription.query.filter_by(
        endpoint=endpoint,
        user_id=current_user.id,
    ).first()
    if subscription:
        subscription.is_active = False
        db.session.commit()

    return jsonify({"status": "ok"})


@notifications_bp.route("/notifications/push/test", methods=["POST"])
@login_required
def test_push():
    unavailable = push_enabled_or_503()
    if unavailable:
        return unavailable

    subscription = (
        PushSubscription.query.filter_by(user_id=current_user.id, is_active=True)
        .order_by(PushSubscription.updated_at.desc())
        .first()
    )
    if subscription is None:
        return jsonify({"error": "No active push subscription found for user."}), 404

    payload = json.dumps(
        {
            "title": "Team Tracker test",
            "body": "Push setup is working.",
            "url": "/teams",
        }
    )
    subscription_info = {
        "endpoint": subscription.endpoint,
        "keys": {"p256dh": subscription.p256dh_key, "auth": subscription.auth_key},
    }

    try:
        send_web_push(subscription_info, payload)
    except WebPushException as exc:
        if is_gone_subscription(exc):
            subscription.is_active = False
            db.session.commit()
        return jsonify({"error": "Push send failed."}), 502

    return jsonify({"status": "sent"})


@notifications_bp.route("/notifications/settings/team/<slug>", methods=["POST"])
@login_required
def update_team_setting(slug):
    team = Team.query.filter_by(slug=slug).first_or_404()
    membership = team_membership_or_none(team.id, current_user.id)
    if membership is None:
        flash("You must be a team member to update this setting.", "danger")
        return redirect(url_for("teams.detail", slug=team.slug))

    form = TeamNotificationForm(prefix=f"team-notify-{team.id}")
    if not form.validate_on_submit():
        flash("Invalid team notification setting.", "danger")
        return redirect(url_for("teams.detail", slug=team.slug))

    enabled = form.enabled.data == "1"
    setting = TeamNotificationSetting.query.filter_by(
        team_id=team.id,
        user_id=current_user.id,
    ).first()
    if setting is None:
        setting = TeamNotificationSetting(
            team_id=team.id,
            user_id=current_user.id,
            enabled=enabled,
        )
        db.session.add(setting)
    else:
        setting.enabled = enabled

    db.session.commit()
    flash("Team notification preference saved.", "success")
    return redirect(url_for("teams.detail", slug=team.slug))


@notifications_bp.route("/notifications/settings/challenge/<int:id>", methods=["POST"])
@login_required
def update_challenge_setting(id):
    challenge = Challenge.query.filter_by(id=id).first_or_404()
    membership = team_membership_or_none(challenge.team_id, current_user.id)
    if membership is None:
        flash("You must be a team member to update this setting.", "danger")
        return redirect(url_for("challenges.detail", id=challenge.id))

    form = ChallengeNotificationForm(prefix=f"challenge-notify-{challenge.id}")
    if not form.validate_on_submit():
        flash("Invalid challenge notification setting.", "danger")
        return redirect(url_for("challenges.detail", id=challenge.id))

    mode = form.mode.data
    setting = ChallengeNotificationSetting.query.filter_by(
        challenge_id=challenge.id,
        user_id=current_user.id,
    ).first()

    if mode == "inherit":
        if setting is not None:
            db.session.delete(setting)
            db.session.commit()
        flash("Challenge notifications now inherit your team setting.", "success")
        return redirect(url_for("challenges.detail", id=challenge.id))

    enabled = mode == "enabled"
    if setting is None:
        setting = ChallengeNotificationSetting(
            challenge_id=challenge.id,
            user_id=current_user.id,
            enabled=enabled,
        )
        db.session.add(setting)
    else:
        setting.enabled = enabled

    db.session.commit()
    flash("Challenge notification preference saved.", "success")
    return redirect(url_for("challenges.detail", id=challenge.id))
