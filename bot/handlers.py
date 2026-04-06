from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    WebAppInfo,
)

from config import ADMIN_IDS, ORDER_GROUP_ID, WEBAPP_URL
from database.crud import (
    get_all_users,
    get_or_create_user,
    get_order,
    get_user,
    update_order_group_message,
    update_order_status,
    update_user_language,
    update_user_phone,
)


router = Router()


TEXTS = {
    "uz": {
        "welcome": "Assalomu alaykum, <b>{name}</b>!\n\nDo'konimizga xush kelibsiz.",
        "open_shop": "Do'konni ochish",
        "register_prompt": "Ro'yxatdan o'tish uchun telefon raqamingizni yuboring:",
        "share_phone": "Raqamni ulashish",
        "registered": "Ro'yxatdan o'tdingiz.",
        "language_changed": "Til o'zgartirildi: O'zbek",
        "no_access": "Ruxsat yo'q.",
        "own_phone_only": "Iltimos, o'z raqamingizni yuboring.",
    },
    "ru": {
        "welcome": "Здравствуйте, <b>{name}</b>!\n\nДобро пожаловать в магазин.",
        "open_shop": "Открыть магазин",
        "register_prompt": "Для регистрации отправьте свой номер телефона:",
        "share_phone": "Поделиться номером",
        "registered": "Регистрация завершена.",
        "language_changed": "Язык изменён: Русский",
        "no_access": "Нет доступа.",
        "own_phone_only": "Пожалуйста, отправьте свой номер.",
    },
}


ORDER_STATUS_TEXT = {
    "pending": "Kutilmoqda",
    "confirmed": "Tasdiqlandi",
    "delivering": "Yetkazilmoqda",
    "delivered": "Yetkazildi",
    "cancelled": "Bekor qilindi",
}


class RegisterState(StatesGroup):
    waiting_phone = State()


class BroadcastState(StatesGroup):
    waiting_message = State()


def get_lang(user) -> str:
    return user.language if user and user.language else "uz"


def main_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=TEXTS[lang]["open_shop"], web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
    )
    lang = get_lang(user)

    if not user.is_verified:
        await state.set_state(RegisterState.waiting_phone)
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=TEXTS[lang]["share_phone"], request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await message.answer(TEXTS[lang]["register_prompt"], reply_markup=keyboard)
        return

    await message.answer(
        TEXTS[lang]["welcome"].format(name=message.from_user.first_name),
        reply_markup=main_keyboard(lang),
        parse_mode="HTML",
    )


@router.message(RegisterState.waiting_phone, F.contact)
async def handle_contact(message: Message, state: FSMContext):
    contact = message.contact
    if contact.user_id != message.from_user.id:
        user = await get_user(message.from_user.id)
        await message.answer(TEXTS[get_lang(user)]["own_phone_only"])
        return

    await update_user_phone(message.from_user.id, contact.phone_number)
    user = await get_user(message.from_user.id)
    lang = get_lang(user)
    await state.clear()

    await message.answer(TEXTS[lang]["registered"], reply_markup=ReplyKeyboardRemove())
    await message.answer(
        TEXTS[lang]["welcome"].format(name=message.from_user.first_name),
        reply_markup=main_keyboard(lang),
        parse_mode="HTML",
    )


@router.message(Command("lang"))
async def lang_handler(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="UZ", callback_data="lang_uz"),
                InlineKeyboardButton(text="RU", callback_data="lang_ru"),
            ]
        ]
    )
    await message.answer("Tilni tanlang / Выберите язык:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("lang_"))
async def set_lang(callback: CallbackQuery):
    lang = callback.data.split("_", 1)[1]
    await update_user_language(callback.from_user.id, lang)
    await callback.message.edit_text(TEXTS[lang]["language_changed"])
    await callback.answer()


@router.message(Command("admin"))
async def admin_handler(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer(TEXTS["uz"]["no_access"])
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Admin Panel", web_app=WebAppInfo(url=f"{WEBAPP_URL}/admin.html"))]
        ]
    )
    await message.answer("Admin panel:", reply_markup=keyboard)


@router.message(Command("broadcast"))
async def broadcast_cmd(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer(TEXTS["uz"]["no_access"])
        return

    await state.set_state(BroadcastState.waiting_message)
    await message.answer(
        "Barcha foydalanuvchilarga yuboriladigan xabarni yuboring.\n/cancel - bekor qilish",
        parse_mode="HTML",
    )


@router.message(BroadcastState.waiting_message)
async def broadcast_preview(message: Message, state: FSMContext):
    await state.update_data(message_id=message.message_id, chat_id=message.chat.id)
    users = await get_all_users()
    verified = [user for user in users if user.is_verified]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"Yuborish ({len(verified)} ta)", callback_data="broadcast_confirm"),
                InlineKeyboardButton(text="Bekor", callback_data="broadcast_cancel"),
            ]
        ]
    )
    await message.answer(
        f"Yuqoridagi xabar {len(verified)} ta foydalanuvchiga yuboriladi. Tasdiqlaysizmi?",
        reply_markup=keyboard,
    )


@router.callback_query(F.data == "broadcast_confirm")
async def do_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()

    users = await get_all_users()
    verified = [user for user in users if user.is_verified]
    sent = 0
    failed = 0

    await callback.message.edit_text(f"Yuborilmoqda... 0/{len(verified)}")
    for index, user in enumerate(verified, start=1):
        try:
            await bot.copy_message(
                chat_id=user.telegram_id,
                from_chat_id=data["chat_id"],
                message_id=data["message_id"],
            )
            sent += 1
        except Exception:
            failed += 1

        if index % 20 == 0:
            try:
                await callback.message.edit_text(f"Yuborilmoqda... {index}/{len(verified)}")
            except Exception:
                pass

    await callback.message.edit_text(
        f"Broadcast yakunlandi.\n\nYuborildi: {sent}\nXato: {failed}"
    )
    await callback.answer()


@router.callback_query(F.data == "broadcast_cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Broadcast bekor qilindi.")
    await callback.answer()


@router.message(Command("cancel"))
async def cancel_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.")


@router.callback_query(F.data.startswith("order_accept_") | F.data.startswith("order_reject_"))
async def handle_order_action(callback: CallbackQuery, bot: Bot):
    _, action, order_id_raw = callback.data.split("_", 2)
    order_id = int(order_id_raw)

    order = await get_order(order_id)
    if not order:
        await callback.answer("Buyurtma topilmadi.")
        return

    if order.status != "pending":
        await callback.answer(f"Buyurtma allaqachon: {ORDER_STATUS_TEXT.get(order.status, order.status)}")
        return

    if action == "accept":
        new_status = "confirmed"
        user_text = (
            f"Buyurtmangiz tasdiqlandi.\n\n"
            f"Buyurtma #{order.id}\n"
            f"Summa: {order.total_price:,.0f} so'm"
        )
    else:
        new_status = "cancelled"
        user_text = (
            f"Buyurtmangiz bekor qilindi.\n\n"
            f"Buyurtma #{order.id}\n"
            f"Qo'shimcha ma'lumot uchun biz bilan bog'laning."
        )

    await update_order_status(order_id, new_status)

    admin_name = callback.from_user.full_name
    new_text = (
        f"{callback.message.text}\n\n"
        f"{admin_name} tomonidan {ORDER_STATUS_TEXT[new_status].lower()}"
    )
    try:
        await callback.message.edit_text(new_text, reply_markup=None)
    except Exception:
        pass

    if order.user and order.user.telegram_id:
        try:
            await bot.send_message(order.user.telegram_id, user_text)
        except Exception:
            pass

    await callback.answer(f"Buyurtma {ORDER_STATUS_TEXT[new_status].lower()}")


async def send_order_to_group(bot: Bot, order, user):
    if not ORDER_GROUP_ID:
        return

    items_text = "\n".join(
        [
            f"  - {item.product.title_uz if item.product else '?'} x{item.quantity} = {item.price * item.quantity:,.0f} so'm"
            for item in order.items
        ]
    )
    delivery_text = (
        f"Yetkazib berish: {order.delivery_price:,.0f} so'm ({order.distance_km:.1f} km)"
        if order.delivery_price
        else "Yetkazib berish: bepul"
    )
    coupon_text = (
        f"\nKupon: {order.coupon_code} (-{order.discount_amount:,.0f} so'm)"
        if order.coupon_code
        else ""
    )
    total_final = order.total_price + order.delivery_price - order.discount_amount
    customer_name = user.full_name or "Noma'lum"

    text = (
        f"YANGI BUYURTMA #{order.id}\n\n"
        f"Mijoz: {customer_name}\n"
        f"Telefon: {user.phone or '-'}\n"
        f"Telegram: @{user.username or '-'}\n\n"
        f"Mahsulotlar:\n{items_text}\n\n"
        f"Mahsulotlar summasi: {order.total_price:,.0f} so'm\n"
        f"{delivery_text}{coupon_text}\n"
        f"Jami: {total_final:,.0f} so'm\n\n"
        f"Manzil: {order.address or '-'}\n"
        f"Izoh: {order.comment or '-'}\n\n"
        f"{order.created_at.strftime('%d.%m.%Y %H:%M')}"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Qabul qilish", callback_data=f"order_accept_{order.id}"),
                InlineKeyboardButton(text="Rad etish", callback_data=f"order_reject_{order.id}"),
            ]
        ]
    )

    try:
        msg = await bot.send_message(ORDER_GROUP_ID, text, reply_markup=keyboard)
        await update_order_group_message(order.id, msg.message_id)
    except Exception as exc:
        print(f"Guruhga yuborishda xato: {exc}")


async def notify_status_change(bot: Bot, user_telegram_id: int, order_id: int, status: str):
    status_messages = {
        "confirmed": "Buyurtmangiz tasdiqlandi va tayyorlanmoqda.",
        "delivering": "Buyurtmangiz yetkazib berilmoqda.",
        "delivered": "Buyurtmangiz yetkazib berildi.",
        "cancelled": "Buyurtmangiz bekor qilindi.",
    }
    text = status_messages.get(status)
    if text:
        try:
            await bot.send_message(user_telegram_id, f"{text}\n\nBuyurtma #{order_id}")
        except Exception:
            pass
