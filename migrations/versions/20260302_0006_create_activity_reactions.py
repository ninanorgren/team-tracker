"""create activity reactions

Revision ID: 20260302_0006
Revises: 20260302_0005
Create Date: 2026-03-02 00:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260302_0006"
down_revision = "20260302_0005"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "activity_reactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("activity_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("emoji", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["activity_id"], ["activities.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("activity_id", "user_id", "emoji"),
    )


def downgrade():
    op.drop_table("activity_reactions")
