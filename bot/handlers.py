import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import WEBAPP_URL, ADMIN_IDS
from database.crud import get_or_create_user, get_user, update_user_phone, update_user_language

router = Router()

TEXTS = {
    "uz": {
        "welcome": "👋 Assalomu alaykum, {name}!\n\nDo'konimizga xush kelibsiz! Quyidagi menyu orqali xarid qiling.",
        "open_shop": "🛍️ Do'konni ochish",
        "register_prompt": "📱 Ro'yxatdan o'tish uchun telefon raqamingizni yuboring:",
        "share_phone": "📞 Raqamni ulashish",
        "registered": "✅ Muvaffaqiyatli ro'yxatdan o'tdingiz!\nEndi do'kondan foydalanishingiz mumkin.",
        "language_changed": "✅ Til o'zgartirildi: O'zbek",
    },
    "ru": {
        "welcome": "👋 Здравствуйте, {name}!\n\nДобро пожаловать в наш магазин! Делайте покупки через меню ниже.",
        "open_shop": "🛍️ Открыть магазин",
        "register_prompt": "📱 Для регистрации отправьте ваш номер телефона:",
        "share_phone": "📞 Поделиться номером",
        "registered": "✅ Вы успешно зарегистрировались!\nТеперь вы можете пользоваться магазином.",
        "language_changed": "✅ Язык изменён: Русский",
    }
}

class RegisterState(StatesGroup):
    waiting_phone = State()

def get_lang(user) -> str:
    return user.language if user and user.language else "uz"

def main_keyboard(lang: str, webapp_url: str) -> InlineKeyboardMarkup:
    text = TEXTS[lang]["open_shop"]
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=text, web_app=WebAppInfo(url=webapp_url))
    ]])

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
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=TEXTS[lang]["share_phone"], request_contact=True)]],
            resize_keyboard=True, one_time_keyboard=True
        )
        await message.answer(TEXTS[lang]["register_prompt"], reply_markup=keyboard)
        return

    kb = main_keyboard(lang, WEBAPP_URL)
    await message.answer(TEXTS[lang]["welcome"].format(name=message.from_user.first_name), reply_markup=kb)

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
    kb = main_keyboard(lang, WEBAPP_URL)
    await message.answer(TEXTS[lang]["welcome"].format(name=message.from_user.first_name), reply_markup=kb)

@router.message(Command("lang"))
async def lang_handler(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
        ]
    ])
    await message.answer("Tilni tanlang / Выберите язык:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("lang_"))
async def set_lang(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    await update_user_language(callback.from_user.id, lang)
    await callback.message.edit_text(TEXTS[lang]["language_changed"])
    await callback.answer()

@router.message(Command("admin"))
async def admin_handler(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Ruxsat yo'q!")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⚙️ Admin Panel", web_app=WebAppInfo(url=f"{WEBAPP_URL}/admin"))
    ]])
    await message.answer("🔐 Admin paneliga xush kelibsiz:", reply_markup=kb)
