from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.enums import (
    BookingStatus,
    BookingType,
    BonusDirection,
    BonusReason,
    ReferralStatus,
    Role,
)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    roles: Mapped[list["UserRole"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    client_profile: Mapped["ClientProfile | None"] = relationship(back_populates="user")
    engineer_profile: Mapped["EngineerProfile | None"] = relationship(back_populates="user")

    def has_role(self, role: Role) -> bool:
        return any(item.role == role for item in self.roles)


class UserRole(TimestampMixin, Base):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role", name="uq_user_roles_user_role"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[Role] = mapped_column(Enum(Role), index=True)

    user: Mapped[User] = relationship(back_populates="roles")


class ClientProfile(TimestampMixin, Base):
    __tablename__ = "client_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    display_name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(64))
    referral_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    referred_by_client_id: Mapped[int | None] = mapped_column(ForeignKey("client_profiles.id"))
    bookings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_bookings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cancelled_bookings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    referrals_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bonus_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped[User] = relationship(back_populates="client_profile")
    referred_by: Mapped["ClientProfile | None"] = relationship(remote_side=[id])
    bookings: Mapped[list["Booking"]] = relationship(back_populates="client")
    bonus_ledger: Mapped[list["BonusLedger"]] = relationship(back_populates="client")


class EngineerProfile(TimestampMixin, Base):
    __tablename__ = "engineer_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    name: Mapped[str] = mapped_column(String(255), default="Sound engineer")
    short_description: Mapped[str] = mapped_column(Text, default="")
    full_description: Mapped[str] = mapped_column(Text, default="")
    photo_file_id: Mapped[str | None] = mapped_column(String(512))
    hourly_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    contact_text: Mapped[str | None] = mapped_column(Text)
    show_contacts: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    accepts_night_requests: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped[User] = relationship(back_populates="engineer_profile")
    work_intervals: Mapped[list["WorkInterval"]] = relationship(
        back_populates="engineer",
        cascade="all, delete-orphan",
    )
    days_off: Mapped[list["DayOff"]] = relationship(
        back_populates="engineer",
        cascade="all, delete-orphan",
    )
    bookings: Mapped[list["Booking"]] = relationship(back_populates="engineer")


class WorkInterval(TimestampMixin, Base):
    __tablename__ = "work_intervals"
    __table_args__ = (
        CheckConstraint("weekday between 0 and 6", name="weekday_range"),
        CheckConstraint("start_time < end_time", name="work_interval_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    engineer_id: Mapped[int] = mapped_column(ForeignKey("engineer_profiles.id", ondelete="CASCADE"))
    weekday: Mapped[int] = mapped_column(Integer, index=True)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    engineer: Mapped[EngineerProfile] = relationship(back_populates="work_intervals")


class DayOff(TimestampMixin, Base):
    __tablename__ = "days_off"
    __table_args__ = (UniqueConstraint("engineer_id", "day", name="uq_days_off_engineer_day"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    engineer_id: Mapped[int] = mapped_column(ForeignKey("engineer_profiles.id", ondelete="CASCADE"))
    day: Mapped[date] = mapped_column(Date, index=True)
    reason: Mapped[str | None] = mapped_column(String(255))
    night_disabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    engineer: Mapped[EngineerProfile] = relationship(back_populates="days_off")


class Booking(TimestampMixin, Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("duration_hours between 1 and 6", name="duration_hours_range"),
        CheckConstraint("starts_at < ends_at", name="booking_period_positive"),
        Index("ix_bookings_engineer_starts", "engineer_id", "starts_at"),
        Index("ix_bookings_client_status", "client_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id"), index=True)
    engineer_id: Mapped[int] = mapped_column(ForeignKey("engineer_profiles.id"), index=True)
    booking_type: Mapped[BookingType] = mapped_column(Enum(BookingType), index=True)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus),
        default=BookingStatus.PENDING_ENGINEER,
        index=True,
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration_hours: Mapped[int] = mapped_column(Integer)
    hourly_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    client_name: Mapped[str] = mapped_column(String(255))
    client_phone: Mapped[str] = mapped_column(String(64))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    attended_marked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reminder_24h_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reminder_2h_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    client: Mapped[ClientProfile] = relationship(back_populates="bookings")
    engineer: Mapped[EngineerProfile] = relationship(back_populates="bookings")


class Referral(TimestampMixin, Base):
    __tablename__ = "referrals"
    __table_args__ = (UniqueConstraint("referred_client_id", name="uq_referrals_referred_client"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    inviter_client_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id"), index=True)
    referred_client_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id"), index=True)
    status: Mapped[ReferralStatus] = mapped_column(
        Enum(ReferralStatus),
        default=ReferralStatus.REGISTERED,
        index=True,
    )
    rewarded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class BonusLedger(TimestampMixin, Base):
    __tablename__ = "bonus_ledger"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id"), index=True)
    booking_id: Mapped[int | None] = mapped_column(ForeignKey("bookings.id"))
    direction: Mapped[BonusDirection] = mapped_column(Enum(BonusDirection), index=True)
    reason: Mapped[BonusReason] = mapped_column(Enum(BonusReason), index=True)
    points: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text)

    client: Mapped[ClientProfile] = relationship(back_populates="bonus_ledger")


class AppSetting(TimestampMixin, Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text)

