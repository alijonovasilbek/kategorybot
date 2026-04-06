import math
from aiogram import Router, F, Bot
from aiogram.types import (Message, CallbackQuery, WebAppInfo,
    InlineKeyboardMarkup, InlineKeyboardButton,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import WEBAPP_URL, ADMIN_IDS, ORDER_GROUP_ID
from database.crud import (get_or_create_user, get_user, update_user_phone,
    update_user_language, get_all_users, get_order, update_order_status,
    update_order_group_message)

router = Router()

TEXTS = {
    "uz": {
        "welcome": "👋 Assalomu alaykum, <b>{name}</b>!\n\nDo'konimizga xush kelibsiz! Quyidagi tugma orqali xarid qiling. 🛍️",
        "open_shop": "🛍️ Do'konni ochish",
        "register_prompt": "📱 Ro'yxatdan o'tish uchun telefon raqamingizni yuboring:",
        "share_phone": "📞 Raqamni ulashish",
        "registered": "✅ Muvaffaqiyatli ro'yxatdan o'tdingiz!\nEndi do'kondan foydalanishingiz mumkin.",
        "language_changed": "✅ Til o'zgartirildi: O'zbek 🇺🇿",
        "no_access": "❌ Ruxsat yo'q!",
    },
    "ru": {
        "welcome": "👋 Здравствуйте, <b>{name}</b>!\n\nДобро пожаловать в наш магазин! Делайте покупки через кнопку ниже. 🛍️",
        "open_shop": "🛍️ Открыть магазин",
        "register_prompt": "📱 Для регистрации отправьте ваш номер телефона:",
        "share_phone": "📞 Поделиться номером",
        "registered": "✅ Вы успешно зарегистрировались!\nТеперь вы можете пользоваться магазином.",
        "language_changed": "✅ Язык изменён: Русский 🇷🇺",
        "no_access": "❌ Нет доступа!",
    }
}

ORDER_STATUS_TEXT = {
    "pending":    "⏳ Kutilmoqda",
    "confirmed":  "✅ Tasdiqlandi",
    "delivering": "🚚 Yetkazilmoqda",
    "delivered":  "📦 Yetkazildi",
    "cancelled":  "❌ Bekor qilindi",
}

class RegisterState(StatesGroup):
    waiting_phone = State()

class BroadcastState(StatesGroup):
    waiting_message = State()
    confirm = State()

def get_lang(user) -> str:
    return user.language if user and user.language else "uz"

def main_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=TEXTS[lang]["open_shop"], web_app=WebAppInfo(url=WEBAPP_URL))
    ]])

# ── /start ────────────────────────────────────────────────────────────────────
@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username
    )
    lang = get_lang(user)
    if not user.is_verified:
        await state.set_state(RegisterState.waiting_phone)
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=TEXTS[lang]["share_phone"], request_contact=True)]],
            resize_keyboard=True, one_time_keyboard=True
        )
        await message.answer(TEXTS[lang]["register_prompt"], reply_markup=kb)
        return
    await message.answer(
        TEXTS[lang]["welcome"].format(name=message.from_user.first_name),
        reply_markup=main_keyboard(lang), parse_mode="HTML"
    )

@router.message(RegisterState.waiting_phone, F.contact)
async def handle_contact(message: Message, state: FSMContext):
    contact = message.contact
    if contact.user_id != message.from_user.id:
        await message.answer("❌ Iltimos, o'z raqamingizni yuboring!")
        return
    await update_user_phone(message.from_user.id, contact.phone_number)
    user = await get_user(message.from_user.id)
    lang = get_lang(user)
    await state.clear()
    await message.answer(TEXTS[lang]["registered"], reply_markup=ReplyKeyboardRemove())
    await message.answer(
        TEXTS[lang]["welcome"].format(name=message.from_user.first_name),
        reply_markup=main_keyboard(lang), parse_mode="HTML"
    )

# ── /lang ─────────────────────────────────────────────────────────────────────
@router.message(Command("lang"))
async def lang_handler(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
    ]])
    await message.answer("Tilni tanlang / Выберите язык:", reply_markup=kb)

@router.callback_query(F.data.startswith("lang_"))
async def set_lang(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    await update_user_language(callback.from_user.id, lang)
    await callback.message.edit_text(TEXTS[lang]["language_changed"])
    await callback.answer()

# ── /admin ────────────────────────────────────────────────────────────────────
@router.message(Command("admin"))
async def admin_handler(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer(TEXTS["uz"]["no_access"]); return
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⚙️ Admin Panel", web_app=WebAppInfo(url=f"{WEBAPP_URL}/admin.html"))
    ]])
    await message.answer("🔐 Admin paneliga xush kelibsiz:", reply_markup=kb)

# ── /broadcast ────────────────────────────────────────────────────────────────
@router.message(Command("broadcast"))
async def broadcast_cmd(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer(TEXTS["uz"]["no_access"]); return
    await state.set_state(BroadcastState.waiting_message)
    await message.answer(
        "📢 <b>Broadcast xabari</b>\n\nBarcha foydalanuvchilarga yuboriladigan xabarni yozing:\n"
        "<i>(Matn, rasm yoki video bo'lishi mumkin)</i>\n\n/cancel — bekor qilish",
        parse_mode="HTML"
    )

@router.message(BroadcastState.waiting_message)
async def broadcast_preview(message: Message, state: FSMContext):
    await state.update_data(message_id=message.message_id, chat_id=message.chat.id)
    users = await get_all_users()
    verified = [u for u in users if u.is_verified]
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=f"✅ Yuborish ({len(verified)} ta)", callback_data="broadcast_confirm"),
        InlineKeyboardButton(text="❌ Bekor", callback_data="broadcast_cancel"),
    ]])
    await message.answer(
        f"👆 Yuqoridagi xabar <b>{len(verified)}</b> ta foydalanuvchiga yuboriladi.\nTasdiqlaysizmi?",
        reply_markup=kb, parse_mode="HTML"
    )

@router.callback_query(F.data == "broadcast_confirm")
async def do_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()
    users = await get_all_users()
    verified = [u for u in users if u.is_verified]
    sent, failed = 0, 0
    status_msg = await callback.message.edit_text(f"⏳ Yuborilmoqda... 0/{len(verified)}")
    for i, user in enumerate(verified):
        try:
            await bot.copy_message(chat_id=user.telegram_id, from_chat_id=data["chat_id"], message_id=data["message_id"])
            sent += 1
        except:
            failed += 1
        if (i + 1) % 20 == 0:
            try:
                await status_msg.edit_text(f"⏳ Yuborilmoqda... {i+1}/{len(verified)}")
            except: pass
    await status_msg.edit_text(f"✅ Broadcast yakunlandi!\n\n✅ Yuborildi: {sent}\n❌ Xato: {failed}")

@router.callback_query(F.data == "broadcast_cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Broadcast bekor qilindi.")

@router.message(Command("cancel"))
async def cancel_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.")

# ── Guruh: buyurtma qabul/rad ─────────────────────────────────────────────────
@router.callback_query(F.data.startswith("order_accept_") | F.data.startswith("order_reject_"))
async def handle_order_action(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split("_")
    action = parts[1]   # accept | reject
    order_id = int(parts[2])

    order = await get_order(order_id)
    if not order:
        await callback.answer("❌ Buyurtma topilmadi!"); return

    if order.status not in ("pending",):
        await callback.answer(f"ℹ️ Buyurtma allaqachon: {ORDER_STATUS_TEXT.get(order.status, order.status)}")
        return

    if action == "accept":
        new_status = "confirmed"
        emoji = "✅"
        user_text = f"✅ Buyurtmangiz tasdiqlandi!\n\n📦 Buyurtma #{order.id}\n💰 Summa: {order.total_price:,.0f} so'm\n\nYaqinda yetkazib beramiz! 🚚"
    else:
        new_status = "cancelled"
        emoji = "❌"
        user_text = f"❌ Buyurtmangiz bekor qilindi.\n\n📦 Buyurtma #{order.id}\nQo'shimcha ma'lumot uchun biz bilan bog'laning."

    await update_order_status(order_id, new_status)

    # Guruh xabarini yangilash
    admin_name = callback.from_user.full_name
    new_text = callback.message.text + f"\n\n{emoji} <b>{admin_name}</b> tomonidan {ORDER_STATUS_TEXT[new_status].lower()}"
    try:
        await callback.message.edit_text(new_text, parse_mode="HTML", reply_markup=None)
    except: pass

    # Foydalanuvchiga xabar
    if order.user and order.user.telegram_id:
        try:
            await bot.send_message(order.user.telegram_id, user_text)
        except: pass

    await callback.answer(f"{emoji} Buyurtma {ORDER_STATUS_TEXT[new_status].lower()}")


async def send_order_to_group(bot: Bot, order, user):
    """Yangi buyurtmani guruhga yuborish"""
    if not ORDER_GROUP_ID:
        return
    items_text = "\n".join([
        f"  • {i.product.title_uz if i.product else '?'} x{i.quantity} = {i.price * i.quantity:,.0f} so'm"
        for i in order.items
    ])
    delivery_text = f"🚚 Yetkazib berish: {order.delivery_price:,.0f} so'm ({order.distance_km:.1f} km)" if order.delivery_price else "🚚 Yetkazib berish: bepul"
    coupon_text = f"\n🏷️ Kupon: {order.coupon_code} (-{order.discount_amount:,.0f} so'm)" if order.coupon_code else ""
    text = (
        f"🛒 <b>YANGI BUYURTMA #{order.id}</b>\n\n"
        f"👤 Mijoz: {user.full_name or 'Noma\\'lum'}\n"
        f"📞 Telefon: {user.phone or '—'}\n"
        f"💬 Telegram: @{user.username or '—'}\n\n"
        f"📦 <b>Mahsulotlar:</b>\n{items_text}\n\n"
        f"💰 Mahsulotlar: {order.total_price:,.0f} so'm\n"
        f"{delivery_text}{coupon_text}\n"
        f"💳 <b>Jami: {order.total_price + order.delivery_price - order.discount_amount:,.0f} so'm</b>\n\n"
        f"📍 Manzil: {order.address or '—'}\n"
        f"💬 Izoh: {order.comment or '—'}\n\n"
        f"🕐 {order.created_at.strftime('%d.%m.%Y %H:%M')}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"order_accept_{order.id}"),
        InlineKeyboardButton(text="❌ Rad etish",    callback_data=f"order_reject_{order.id}"),
    ]])
    try:
        msg = await bot.send_message(ORDER_GROUP_ID, text, parse_mode="HTML", reply_markup=kb)
        await update_order_group_message(order.id, msg.message_id)
    except Exception as e:
        print(f"Guruhga yuborishda xato: {e}")


async def notify_status_change(bot: Bot, user_telegram_id: int, order_id: int, status: str):
    """Buyurtma holati o'zganganda foydalanuvchiga xabar"""
    status_messages = {
        "confirmed":  "✅ Buyurtmangiz tasdiqlandi va tayyorlanmoqda!",
        "delivering": "🚚 Buyurtmangiz yetkazib berilmoqda!",
        "delivered":  "📦 Buyurtmangiz yetkazib berildi! Xarid uchun rahmat! ❤️",
        "cancelled":  "❌ Buyurtmangiz bekor qilindi. Savollar uchun biz bilan bog'laning.",
    }
    text = status_messages.get(status)
    if text:
        try:
            await bot.send_message(user_telegram_id, f"{text}\n\n📋 Buyurtma #{order_id}")
        except: pass
