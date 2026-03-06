import json

from flask import current_app
from pywebpush import WebPushException, webpush

from app.extensions import db
from app.models import (
    Challenge,
    ChallengeMembership,
    ChallengeNotificationSetting,
    PushSubscription,
    TeamNotificationSetting,
)


def send_web_push(subscription_info, payload):
    return webpush(
        subscription_info=subscription_info,
        data=payload,
        vapid_private_key=current_app.config["VAPID_PRIVATE_KEY"],
        vapid_claims={"sub": current_app.config["VAPID_CLAIMS_SUB"]},
    )


def is_gone_subscription(exc):
    if not isinstance(exc, WebPushException):
        return False
    if exc.response is None:
        return False
    return exc.response.status_code in {404, 410}


def resolve_team_notification_enabled(user_id, team_id):
    setting = TeamNotificationSetting.query.filter_by(
        user_id=user_id,
        team_id=team_id,
    ).first()
    if setting is None:
        return True
    return bool(setting.enabled)


def resolve_challenge_notification_enabled(user_id, team_id, challenge_id):
    challenge_setting = ChallengeNotificationSetting.query.filter_by(
        user_id=user_id,
        challenge_id=challenge_id,
    ).first()
    if challenge_setting is not None and challenge_setting.enabled is not None:
        return bool(challenge_setting.enabled), "challenge"

    team_enabled = resolve_team_notification_enabled(user_id, team_id)
    return team_enabled, "team"


def notify_challenge_event(
    *,
    challenge_id,
    actor_user_id,
    title,
    body,
    url,
    tag=None,
):
    if not current_app.config["PUSH_NOTIFICATIONS_ENABLED"]:
        return

    challenge = Challenge.query.filter_by(id=challenge_id).first()
    if challenge is None:
        return

    memberships = ChallengeMembership.query.filter_by(challenge_id=challenge_id).all()
    recipient_user_ids = [m.user_id for m in memberships if m.user_id != actor_user_id]
    if not recipient_user_ids:
        return

    subscriptions = (
        PushSubscription.query.filter(
            PushSubscription.user_id.in_(recipient_user_ids),
            PushSubscription.is_active.is_(True),
        )
        .order_by(PushSubscription.user_id.asc())
        .all()
    )
    if not subscriptions:
        return

    disabled_user_ids = set()
    for user_id in recipient_user_ids:
        enabled, _source = resolve_challenge_notification_enabled(
            user_id,
            challenge.team_id,
            challenge_id,
        )
        if not enabled:
            disabled_user_ids.add(user_id)

    changed = False
    payload = json.dumps(
        {
            "title": title,
            "body": body,
            "url": url,
            "tag": tag or f"challenge-{challenge_id}",
        }
    )
    for subscription in subscriptions:
        if subscription.user_id in disabled_user_ids:
            continue

        subscription_info = {
            "endpoint": subscription.endpoint,
            "keys": {
                "p256dh": subscription.p256dh_key,
                "auth": subscription.auth_key,
            },
        }
        try:
            send_web_push(subscription_info, payload)
        except WebPushException as exc:
            if is_gone_subscription(exc):
                subscription.is_active = False
                changed = True
            else:
                current_app.logger.warning("Push send failed: %s", exc)

    if changed:
        db.session.commit()
