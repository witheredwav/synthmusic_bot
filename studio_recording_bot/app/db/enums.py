from enum import StrEnum


class Role(StrEnum):
    CLIENT = "client"
    ENGINEER = "engineer"
    ADMIN = "admin"


class BookingType(StrEnum):
    REGULAR = "regular"
    LONG = "long"
    NIGHT = "night"


class BookingStatus(StrEnum):
    DRAFT = "draft"
    PENDING_ENGINEER = "pending_engineer"
    PENDING_MANUAL = "pending_manual"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED_BY_CLIENT = "cancelled_by_client"
    COMPLETED = "completed"
    ATTENDED = "attended"
    NO_SHOW = "no_show"


class BonusDirection(StrEnum):
    ACCRUAL = "accrual"
    SPEND = "spend"


class BonusReason(StrEnum):
    VISIT = "visit"
    REFERRAL = "referral"
    REWARD_10_POINTS = "reward_10_points"
    REWARD_20_POINTS = "reward_20_points"
    MANUAL = "manual"


class ReferralStatus(StrEnum):
    REGISTERED = "registered"
    BOOKED = "booked"
    CONFIRMED = "confirmed"
    REWARDED = "rewarded"
    CANCELLED = "cancelled"

