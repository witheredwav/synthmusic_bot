from aiogram.filters.callback_data import CallbackData


class NavCb(CallbackData, prefix="nav"):
    target: str


class PageCb(CallbackData, prefix="page"):
    target: str
    page: int


class EngineerCb(CallbackData, prefix="eng"):
    action: str
    engineer_id: int


class BookingCb(CallbackData, prefix="book"):
    action: str
    value: str


class BookingActionCb(CallbackData, prefix="bact"):
    action: str
    booking_id: int


class ConfirmCb(CallbackData, prefix="confirm"):
    action: str
    token: str = "current"

