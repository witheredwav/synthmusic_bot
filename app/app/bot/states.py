from aiogram.fsm.state import State, StatesGroup


class BookingFlow(StatesGroup):
    month = State()
    day = State()
    engineer = State()
    time = State()
    name = State()
    phone = State()
    duration = State()
    final_confirm = State()


class NightBookingFlow(StatesGroup):
    engineer = State()
    day = State()
    time = State()
    duration = State()
    final_confirm = State()


class AdminRoleFlow(StatesGroup):
    role = State()
    telegram_id = State()
    confirm = State()


class RejectBookingFlow(StatesGroup):
    booking_id = State()
    reason = State()
    confirm = State()

