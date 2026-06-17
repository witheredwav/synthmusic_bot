"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-17
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    role = sa.Enum("CLIENT", "ENGINEER", "ADMIN", name="role")
    booking_type = sa.Enum("REGULAR", "LONG", "NIGHT", name="bookingtype")
    booking_status = sa.Enum(
        "DRAFT",
        "PENDING_ENGINEER",
        "PENDING_MANUAL",
        "CONFIRMED",
        "REJECTED",
        "CANCELLED_BY_CLIENT",
        "COMPLETED",
        "ATTENDED",
        "NO_SHOW",
        name="bookingstatus",
    )
    referral_status = sa.Enum(
        "REGISTERED",
        "BOOKED",
        "CONFIRMED",
        "REWARDED",
        "CANCELLED",
        name="referralstatus",
    )
    bonus_direction = sa.Enum("ACCRUAL", "SPEND", name="bonusdirection")
    bonus_reason = sa.Enum(
        "VISIT",
        "REFERRAL",
        "REWARD_10_POINTS",
        "REWARD_20_POINTS",
        "MANUAL",
        name="bonusreason",
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(255)),
        sa.Column("first_name", sa.String(255)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("telegram_id", name="uq_users_telegram_id"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])

    op.create_table(
        "user_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", role, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "role", name="uq_user_roles_user_role"),
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_role", "user_roles", ["role"])

    op.create_table(
        "client_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("display_name", sa.String(255)),
        sa.Column("phone", sa.String(64)),
        sa.Column("referral_code", sa.String(64), nullable=False),
        sa.Column("referred_by_client_id", sa.Integer(), sa.ForeignKey("client_profiles.id")),
        sa.Column("bookings_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_bookings_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cancelled_bookings_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("referrals_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bonus_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_client_profiles_user_id"),
        sa.UniqueConstraint("referral_code", name="uq_client_profiles_referral_code"),
    )
    op.create_index("ix_client_profiles_referral_code", "client_profiles", ["referral_code"])

    op.create_table(
        "engineer_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("short_description", sa.Text(), nullable=False, server_default=""),
        sa.Column("full_description", sa.Text(), nullable=False, server_default=""),
        sa.Column("photo_file_id", sa.String(512)),
        sa.Column("hourly_rate", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("contact_text", sa.Text()),
        sa.Column("show_contacts", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_visible", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("accepts_night_requests", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_engineer_profiles_user_id"),
    )

    op.create_table(
        "work_intervals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("engineer_id", sa.Integer(), sa.ForeignKey("engineer_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("weekday between 0 and 6", name="ck_work_intervals_weekday_range"),
        sa.CheckConstraint("start_time < end_time", name="ck_work_intervals_work_interval_positive"),
    )
    op.create_index("ix_work_intervals_weekday", "work_intervals", ["weekday"])

    op.create_table(
        "days_off",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("engineer_id", sa.Integer(), sa.ForeignKey("engineer_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(255)),
        sa.Column("night_disabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("engineer_id", "day", name="uq_days_off_engineer_day"),
    )
    op.create_index("ix_days_off_day", "days_off", ["day"])

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("client_profiles.id"), nullable=False),
        sa.Column("engineer_id", sa.Integer(), sa.ForeignKey("engineer_profiles.id"), nullable=False),
        sa.Column("booking_type", booking_type, nullable=False),
        sa.Column("status", booking_status, nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_hours", sa.Integer(), nullable=False),
        sa.Column("hourly_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("total_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("client_name", sa.String(255), nullable=False),
        sa.Column("client_phone", sa.String(64), nullable=False),
        sa.Column("rejection_reason", sa.Text()),
        sa.Column("attended_marked_at", sa.DateTime(timezone=True)),
        sa.Column("reminder_24h_sent_at", sa.DateTime(timezone=True)),
        sa.Column("reminder_2h_sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("duration_hours between 1 and 6", name="ck_bookings_duration_hours_range"),
        sa.CheckConstraint("starts_at < ends_at", name="ck_bookings_booking_period_positive"),
    )
    op.create_index("ix_bookings_client_id", "bookings", ["client_id"])
    op.create_index("ix_bookings_engineer_id", "bookings", ["engineer_id"])
    op.create_index("ix_bookings_status", "bookings", ["status"])
    op.create_index("ix_bookings_starts_at", "bookings", ["starts_at"])
    op.create_index("ix_bookings_ends_at", "bookings", ["ends_at"])
    op.create_index("ix_bookings_engineer_starts", "bookings", ["engineer_id", "starts_at"])
    op.create_index("ix_bookings_client_status", "bookings", ["client_id", "status"])
    op.execute(
        """
        ALTER TABLE bookings
        ADD CONSTRAINT no_engineer_booking_overlap
        EXCLUDE USING gist (
            engineer_id WITH =,
            tstzrange(starts_at, ends_at, '[)') WITH &&
        )
        WHERE (status IN ('PENDING_ENGINEER', 'PENDING_MANUAL', 'CONFIRMED'))
        """
    )

    op.create_table(
        "referrals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("inviter_client_id", sa.Integer(), sa.ForeignKey("client_profiles.id"), nullable=False),
        sa.Column("referred_client_id", sa.Integer(), sa.ForeignKey("client_profiles.id"), nullable=False),
        sa.Column("status", referral_status, nullable=False),
        sa.Column("rewarded_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("referred_client_id", name="uq_referrals_referred_client"),
    )
    op.create_index("ix_referrals_inviter_client_id", "referrals", ["inviter_client_id"])
    op.create_index("ix_referrals_referred_client_id", "referrals", ["referred_client_id"])
    op.create_index("ix_referrals_status", "referrals", ["status"])

    op.create_table(
        "bonus_ledger",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("client_profiles.id"), nullable=False),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id")),
        sa.Column("direction", bonus_direction, nullable=False),
        sa.Column("reason", bonus_reason, nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_bonus_ledger_client_id", "bonus_ledger", ["client_id"])
    op.create_index("ix_bonus_ledger_direction", "bonus_ledger", ["direction"])
    op.create_index("ix_bonus_ledger_reason", "bonus_ledger", ["reason"])

    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(128), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("app_settings")
    op.drop_table("bonus_ledger")
    op.drop_table("referrals")
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS no_engineer_booking_overlap")
    op.drop_table("bookings")
    op.drop_table("days_off")
    op.drop_table("work_intervals")
    op.drop_table("engineer_profiles")
    op.drop_table("client_profiles")
    op.drop_table("user_roles")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS bonusreason")
    op.execute("DROP TYPE IF EXISTS bonusdirection")
    op.execute("DROP TYPE IF EXISTS referralstatus")
    op.execute("DROP TYPE IF EXISTS bookingstatus")
    op.execute("DROP TYPE IF EXISTS bookingtype")
    op.execute("DROP TYPE IF EXISTS role")

