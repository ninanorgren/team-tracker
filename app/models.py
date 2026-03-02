from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager


def utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )
    created_teams = db.relationship(
        "Team",
        back_populates="created_by",
        foreign_keys="Team.created_by_user_id",
    )
    team_memberships = db.relationship(
        "TeamMembership",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    teams = db.relationship(
        "Team",
        secondary="team_memberships",
        back_populates="members",
        viewonly=True,
    )
    challenge_memberships = db.relationship(
        "ChallengeMembership",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    challenges = db.relationship(
        "Challenge",
        secondary="challenge_memberships",
        back_populates="members",
        viewonly=True,
    )
    activities = db.relationship(
        "Activity",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    activity_comments = db.relationship(
        "ActivityComment",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    challenge_comments = db.relationship(
        "ChallengeComment",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    activity_reactions = db.relationship(
        "ActivityReaction",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Team(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )
    created_by = db.relationship(
        "User",
        back_populates="created_teams",
        foreign_keys=[created_by_user_id],
    )
    memberships = db.relationship(
        "TeamMembership",
        back_populates="team",
        cascade="all, delete-orphan",
    )
    members = db.relationship(
        "User",
        secondary="team_memberships",
        back_populates="teams",
        viewonly=True,
    )
    challenges = db.relationship(
        "Challenge",
        back_populates="team",
        cascade="all, delete-orphan",
    )


class TeamMembership(db.Model):
    __tablename__ = "team_memberships"
    __table_args__ = (db.UniqueConstraint("team_id", "user_id"),)

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    joined_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    team = db.relationship("Team", back_populates="memberships")
    user = db.relationship("User", back_populates="team_memberships")


class Challenge(db.Model):
    __tablename__ = "challenges"

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    frequency_per_week = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )
    team = db.relationship("Team", back_populates="challenges")
    memberships = db.relationship(
        "ChallengeMembership",
        back_populates="challenge",
        cascade="all, delete-orphan",
    )
    members = db.relationship(
        "User",
        secondary="challenge_memberships",
        back_populates="challenges",
        viewonly=True,
    )
    activities = db.relationship(
        "Activity",
        back_populates="challenge",
        cascade="all, delete-orphan",
    )
    comments = db.relationship(
        "ChallengeComment",
        back_populates="challenge",
        cascade="all, delete-orphan",
    )


class ChallengeMembership(db.Model):
    __tablename__ = "challenge_memberships"
    __table_args__ = (db.UniqueConstraint("challenge_id", "user_id"),)

    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    joined_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    challenge = db.relationship("Challenge", back_populates="memberships")
    user = db.relationship("User", back_populates="challenge_memberships")


class Activity(db.Model):
    __tablename__ = "activities"
    __table_args__ = (db.UniqueConstraint("challenge_id", "user_id", "activity_date"),)

    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    activity_date = db.Column(db.Date, nullable=False)
    is_checked = db.Column(db.Boolean, nullable=False, default=True)
    note = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )
    challenge = db.relationship("Challenge", back_populates="activities")
    user = db.relationship("User", back_populates="activities")
    comments = db.relationship(
        "ActivityComment",
        back_populates="activity",
        cascade="all, delete-orphan",
    )
    reactions = db.relationship(
        "ActivityReaction",
        back_populates="activity",
        cascade="all, delete-orphan",
    )


class ActivityComment(db.Model):
    __tablename__ = "activity_comments"

    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("activities.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )
    activity = db.relationship("Activity", back_populates="comments")
    user = db.relationship("User", back_populates="activity_comments")


class ChallengeComment(db.Model):
    __tablename__ = "challenge_comments"

    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )
    challenge = db.relationship("Challenge", back_populates="comments")
    user = db.relationship("User", back_populates="challenge_comments")


class ActivityReaction(db.Model):
    __tablename__ = "activity_reactions"
    __table_args__ = (db.UniqueConstraint("activity_id", "user_id", "emoji"),)

    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("activities.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    emoji = db.Column(db.String(16), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    activity = db.relationship("Activity", back_populates="reactions")
    user = db.relationship("User", back_populates="activity_reactions")
