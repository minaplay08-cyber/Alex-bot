import os
import sys
import json
import asyncio
import random
from datetime import datetime, time
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command
from groq import Groq

load_dotenv()

from config import Settings
from alex_prompt import (
    ALEX_SYSTEM_PROMPT,
    ALEX_DARK_ROMANCE,
    REMINDER_MORNING,
    REMINDER_EVENING
)

settings = Settings()

bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher()
router = Router()
client = Groq(api_key=settings.groq_api_key)

DATA_FILE = "user_data.json"
MAX_HISTORY = 60
SHORT_TERM_MEMORY_SIZE = 10

STICKERS_NORMAL = {
    "[laugh]": "CAACAgIAAxkBAAEB0mVnAaMJpL3D2R9S6Z1L8F5t9a7G9gACjwEAAstZxCVLqO3Dq6pumC4E",
    "[wink]": "CAACAgIAAxkBAAEB0mhnAaM3pL3D2R9S6Z1L8F5t9a7G9gAClwEAAstZxCVLqO3Dq6pumC4E",
    "[love]": "CAACAgIAAxkBAAEB0mhnAaM3pL3D2R9S6Z1L8F5t9a7G9gACkwEAAstZxCVLqO3Dq6pumC4E",
    "[think]": "CAACAgIAAxkBAAEB0mhnAaM3pL3D2R9S6Z1L8F5t9a7G9gACjQEAAstZxCVLqO3Dq6pumC4E",
    "[cool]": "CAACAgIAAxkBAAEB0mhnAaM3pL3D2R9S6Z1L8F5t9a7G9gACiQEAAstZxCVLqO3Dq6pumC4E",
    "[sad]": "CAACAgIAAxkBAAEB0mhnAaM3pL3D2R9S6Z1L8F5t9a7G9gAChQEAAstZxCVLqO3Dq6pumC4E",
    "[angry]": "CAACAgIAAxkBAAEB0mhnAaM3pL3D2R9S6Z1L8F5t9a7G9gACgQEAAstZxCVLqO3Dq6pumC4E",
    "[surprised]": "CAACAgIAAxkBAAEB0mhnAaM3pL3D2R9S6Z1L8F5t9a7G9gACfQEAAstZxCVLqO3Dq6pumC4E",
    "[wave]": "CAACAgIAAxkBAAEB0mhnAaM3pL3D2R9S6Z1L8F5t9a7G9gACeQEAAstZxCVLqO3Dq6pumC4E",
    "[fire]": "CAACAgIAAxkBAAEB0mhnAaM3pL3D2R9S6Z1L8F5t9a7G9gACdQEAAstZxCVLqO3Dq6pumC4E",
}

STICKERS_DARK = {
    "[smirk]": "CAACAgIAAxkBAAEB0mhnAaM3pL3D2R9S6Z1L8F5t9a7G9gACcQEAAstZxCVLqO3Dq6pumC4E",
    "[seduce]": "CAACAgIAAxkBAAEB0mhnAaM3pL3D2R9S6Z1L8F5t9a7G9gACbQEAAstZxCVLqO3Dq6pumC4E",
    "[kiss]": "CAACAgIAAxkBAAEB0mhnAaM3pL3D2R9S6Z1L8F5t9a7G9gACaQEAAstZxCVLqO3Dq6pumC4E",
    "[stare]": "CAACAgIAAxkBAAEB0mhnAaM3pL3D2R9S6Z1L8F5t9a7G9gACZQEAAstZxCVLqO3Dq6pumC4E",
    "[danger]": "CAACAgIAAxkBAAEB0mhnAaM3pL3D2R9S6Z1L8F5t9a7G9gACYQEAAstZxCVLqO3Dq6pumC4E",
    "[dream]": "CAACAgIAAxkBAAEB0mhnAaM3pL3D2R9S6Z1L8F5t9a7G9gACXQEAAstZxCVLqO3Dq6pumC4E",
    "[obsess]": "CAACAgIAAxkBAAEB0mhnAaM3pL3D2R9S6Z1L8F5t9a7G9gACWQEAAstZxCVLqO3Dq6pumC4E",
}

MAIN_MENU = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👤 Профиль", callback_data="menu_profile"),
     InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu_settings")],
    [InlineKeyboardButton(text="🌙 Тёмный режим", callback_data="menu_dark"),
     InlineKeyboardButton(text="☀️ Обычный", callback_data="menu_normal")],
    [InlineKeyboardButton(text="🔔 Напоминания", callback_data="menu_remind"),
     InlineKeyboardButton(text="🧠 Память", callback_data="menu_memory")],
    [InlineKeyboardButton(text="🔄 Забыть", callback_data="menu_forget"),
     InlineKeyboardButton(text="📖 Помощь", callback_data="menu_help")],
])

WEBAPP_URL = "https://alex-bot-production-214d.up.railway.app"

WEBAPP_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
        text="🌙 Открыть Dark App", 
        web_app=WebAppInfo(url=WEBAPP_URL)
    )]
])


def load_data() -> dict:
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"users": {}, "conversation_history": {}, "memory": {}}


def save_data(data: dict):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving data: {e}")


def init_user(user_id: int) -> dict:
    data = load_data()
    uid_str = str(user_id)
    
    if uid_str not in data["users"]:
        data["users"][uid_str] = {
            "name": None,
            "gender": None,
            "appearance": None,
            "interests": None,
            "reminders_enabled": False,
            "dark_mode": False,
            "last_reminder": {}
        }
    
    if uid_str not in data["conversation_history"]:
        data["conversation_history"][uid_str] = []
    
    if uid_str not in data["memory"]:
        data["memory"][uid_str] = {
            "topics": [],
            "facts": [],
            "last_session": None,
            "important": []
        }
    
    save_data(data)
    return data["users"][uid_str]


def get_user_setting(user_id: int, key: str, default=None):
    data = load_data()
    uid_str = str(user_id)
    if uid_str in data["users"]:
        return data["users"][uid_str].get(key, default)
    return default


def set_user_setting(user_id: int, key: str, value):
    data = load_data()
    uid_str = str(user_id)
    if uid_str not in data["users"]:
        init_user(user_id)
        data = load_data()
    data["users"][uid_str][key] = value
    save_data(data)


def get_conversation_history(user_id: int, limit: int = None) -> list:
    data = load_data()
    uid_str = str(user_id)
    history = data["conversation_history"].get(uid_str, [])
    if limit:
        return history[-limit:]
    return history


def add_to_history(user_id: int, role: str, content: str):
    data = load_data()
    uid_str = str(user_id)
    
    if uid_str not in data["conversation_history"]:
        data["conversation_history"][uid_str] = []
    
    data["conversation_history"][uid_str].append({"role": role, "content": content})
    
    history = data["conversation_history"][uid_str]
    if len(history) > MAX_HISTORY:
        data["conversation_history"][uid_str] = history[-MAX_HISTORY:]
    
    save_data(data)


def clear_history(user_id: int):
    data = load_data()
    uid_str = str(user_id)
    data["conversation_history"][uid_str] = []
    save_data(data)


def update_memory(user_id: int, new_message: str, response: str):
    data = load_data()
    uid_str = str(user_id)
    
    if uid_str not in data["memory"]:
        data["memory"][uid_str] = {"topics": [], "facts": [], "last_session": None, "important": []}
    
    memory = data["memory"][uid_str]
    memory["last_session"] = datetime.now().isoformat()
    
    words = new_message.lower().split()
    topics = ["работа", "учёба", "дом", "семья", "друзья", "любовь", "фильм", "книга", 
              "музыка", "еда", "спорт", "путешествие", "проблема", "радость", "грусть",
              "настроение", "планы", "вчера", "сегодня", "завтра"]
    
    for topic in topics:
        if topic in words:
            if topic not in memory["topics"]:
                memory["topics"].append(topic)
    
    if len(memory["topics"]) > 15:
        memory["topics"] = memory["topics"][-15:]
    
    save_data(data)


def get_memory_context(user_id: int) -> str:
    data = load_data()
    uid_str = str(user_id)
    
    if uid_str not in data["memory"]:
        return ""
    
    memory = data["memory"][uid_str]
    context_parts = []
    
    if memory.get("topics"):
        topics_str = ", ".join(memory["topics"][-10:])
        context_parts.append(f"Недавние темы разговора: {topics_str}")
    
    if memory.get("facts"):
        facts_str = ". ".join(memory["facts"][-5:])
        context_parts.append(f"Известные факты: {facts_str}")
    
    return "\n".join(context_parts) if context_parts else ""


@router.message(Command("memory"))
async def cmd_memory(message: Message):
    user_id = message.from_user.id
    memory_context = get_memory_context(user_id)
    history = get_conversation_history(user_id, limit=10)
    
    text = "🧠 Что я помню о нас:\n\n"
    
    if memory_context:
        text += f"📌 {memory_context}\n\n"
    else:
        text += "Пока ничего особенного не запомнил...\n\n"
    
    if history:
        text += "📝 Последние сообщения:\n"
        for msg in history[-5:]:
            role = "Ты" if msg["role"] == "user" else "Я"
            preview = msg["content"][:80] + "..." if len(msg["content"]) > 80 else msg["content"]
            text += f"• {role}: {preview}\n"
    
    await message.answer(text)


@router.message(Command("forget"))
async def cmd_forget(message: Message):
    user_id = message.from_user.id
    data = load_data()
    uid_str = str(user_id)
    
    if uid_str in data["memory"]:
        data["memory"][uid_str] = {"topics": [], "facts": [], "last_session": None, "important": []}
        save_data(data)
    
    await message.answer("Ладно, забыл. Чистый лист 🧹")


def get_personalized_prompt(user_id: int, base_prompt: str) -> str:
    user = init_user(user_id)
    additions = []
    
    if user.get("name"):
        additions.append(f"Имя собеседника: {user['name']}")
    
    if user.get("gender"):
        gender = user["gender"]
        if gender == "female":
            additions.append("Обращайся к ней в женском роде, будь галантнее")
        elif gender == "male":
            additions.append("Обращайся к нему в мужском роде, как к другу")
        elif gender == "other":
            additions.append("Используй нейтральный род")
    
    if user.get("appearance"):
        additions.append(f"Внешность собеседника: {user['appearance']}")
    
    if user.get("interests"):
        additions.append(f"Интересы собеседника: {user['interests']}")
    
    memory_context = get_memory_context(user_id)
    if memory_context:
        additions.append(f"КОНТЕКСТ РАЗГОВОРА:\n{memory_context}")
    
    history = get_conversation_history(user_id, limit=15)
    if history:
        additions.append(f"НЕДАВНИЙ РАЗГОВОР (для контекста):")
        for msg in history[-8:]:
            role = "Собеседник" if msg["role"] == "user" else "Ты"
            additions.append(f"- {role}: {msg['content'][:200]}")
    
    if additions:
        return base_prompt + "\n\nКОНТЕКСТ:\n" + "\n".join(additions)
    
    return base_prompt


async def scheduler():
    while True:
        now = datetime.now().time()
        current_hour = now.hour
        data = load_data()
        
        for uid_str, user in data["users"].items():
            user_id = int(uid_str)
            
            if not user.get("reminders_enabled"):
                continue
            
            last = user.get("last_reminder", {})
            dark_mode = user.get("dark_mode", False)
            
            if 6 <= current_hour <= 9:
                if not last.get("morning_sent_today"):
                    await send_reminder(user_id, "morning", dark_mode)
                    user["last_reminder"]["morning_sent_today"] = True
                    set_user_setting(user_id, "last_reminder", user["last_reminder"])
                    
            if 20 <= current_hour <= 23:
                if not last.get("evening_sent_today"):
                    await send_reminder(user_id, "evening", dark_mode)
                    user["last_reminder"]["evening_sent_today"] = True
                    set_user_setting(user_id, "last_reminder", user["last_reminder"])
        
        if current_hour == 0:
            for uid_str in data["users"]:
                user_id = int(uid_str)
                set_user_setting(user_id, "last_reminder", {})
        
        await asyncio.sleep(300)


async def send_reminder(user_id: int, time_of_day: str, dark_mode: bool = False):
    prompt = get_personalized_prompt(user_id, ALEX_DARK_ROMANCE if dark_mode else ALEX_SYSTEM_PROMPT)
    
    if time_of_day == "morning":
        base_msg = random.choice(REMINDER_MORNING)
    else:
        base_msg = random.choice(REMINDER_EVENING)
    
    if dark_mode:
        base_msg = f"🌙 {base_msg}"
    
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Напиши короткое сообщение ({'утро' if time_of_day == 'morning' else 'вечер'}). 1-3 предложения. Учти наш предыдущий разговор."}
    ]
    
    try:
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=messages,
            max_tokens=300,
            temperature=0.8
        )
        await bot.send_message(user_id, response.choices[0].message.content)
    except Exception:
        await bot.send_message(user_id, base_msg)


@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    init_user(user_id)
    clear_history(user_id)
    
    await message.answer("...секунду")
    
    prompt = get_personalized_prompt(user_id, ALEX_SYSTEM_PROMPT)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": "Ты только что встретил этого человека снова. Вспомни о чём вы общались раньше (если было). Напиши коротко (2-4 предложения), как будто встретил старого знакомого."}
    ]
    
    try:
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=messages,
            max_tokens=350,
            temperature=0.85
        )
        await message.answer(
            response.choices[0].message.content + 
            "\n\n🌙 Хочешь увидеть кое-что интересное?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🌙 Открыть App", web_app=WebAppInfo(url=WEBAPP_URL))]
            ])
        )
    except Exception:
        await message.answer(
            "👋 С возвращением!\n\n"
            "🌙 Хочешь увидеть кое-что интересное?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🌙 Открыть App", web_app=WebAppInfo(url=WEBAPP_URL))]
            ])
        )


@router.message(Command("reset"))
async def cmd_reset(message: Message):
    user_id = message.from_user.id
    clear_history(user_id)
    await message.answer("История чата очищена 🔄 (память сохранена)")


@router.message(Command("remind"))
async def cmd_remind(message: Message):
    user_id = message.from_user.id
    current = get_user_setting(user_id, "reminders_enabled", False)
    set_user_setting(user_id, "reminders_enabled", not current)
    
    if not current:
        await message.answer("Буду писать тебе утром и вечером ☀️🌙")
    else:
        await message.answer("Напоминания выключены 🔕")


@router.message(Command("dark"))
async def cmd_dark(message: Message):
    user_id = message.from_user.id
    set_user_setting(user_id, "dark_mode", True)
    
    prompt = get_personalized_prompt(user_id, ALEX_DARK_ROMANCE)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": "Активирован тёмный режим. Напиши короткое сообщение (2-3 предложения), намекая на новую сторону характера."}
    ]
    
    try:
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=messages,
            max_tokens=300,
            temperature=0.8
        )
        await message.answer(response.choices[0].message.content)
    except Exception:
        await message.answer("🌙 Тёмный режим включён.")


@router.message(Command("normal"))
async def cmd_normal(message: Message):
    user_id = message.from_user.id
    set_user_setting(user_id, "dark_mode", False)
    await message.answer("Вернулся к обычному стилю 😊")


@router.message(Command("setname"))
async def cmd_setname(message: Message):
    user_id = message.from_user.id
    init_user(user_id)
    
    args = message.text.replace("/setname", "").strip()
    
    if not args:
        current = get_user_setting(user_id, "name")
        await message.answer(f"Текущее имя: {current or 'не указано'}\n\nНапиши: /setname Имя")
        return
    
    set_user_setting(user_id, "name", args)
    await message.answer(f"Запомнил, {args} 👋")


@router.message(Command("setgender"))
async def cmd_setgender(message: Message):
    user_id = message.from_user.id
    init_user(user_id)
    
    current = get_user_setting(user_id, "gender")
    current_text = {"female": "👩 Женский", "male": "👨 Мужской", "other": "⚧ Не указан", None: "❓ Не указан"}
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👩 Женский")],
            [KeyboardButton(text="👨 Мужской")],
            [KeyboardButton(text="⚧ Не указывать")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        f"Текущий выбор: {current_text.get(current, '❓')}\n\nВыбери пол:",
        reply_markup=keyboard
    )


@router.message(F.text & F.text.in_(["👩 Женский", "👨 Мужской", "⚧ Не указывать"]))
async def handle_gender_choice(message: Message):
    user_id = message.from_user.id
    init_user(user_id)
    
    choice = message.text
    if choice == "👩 Женский":
        set_user_setting(user_id, "gender", "female")
        await message.answer("Готово! 🌹", reply_markup=None)
    elif choice == "👨 Мужской":
        set_user_setting(user_id, "gender", "male")
        await message.answer("Принято, братан! 🤝", reply_markup=None)
    else:
        set_user_setting(user_id, "gender", "other")
        await message.answer("Ок 👍", reply_markup=None)


@router.message(Command("setappearance"))
async def cmd_setappearance(message: Message):
    user_id = message.from_user.id
    init_user(user_id)
    
    args = message.text.replace("/setappearance", "").strip()
    
    if not args:
        current = get_user_setting(user_id, "appearance")
        await message.answer(f"Текущее: {current or 'не указано'}\n\nПример: /setappearance Высокая брюнетка с карими глазами")
        return
    
    set_user_setting(user_id, "appearance", args)
    await message.answer(f"Запомнил 👀")


@router.message(Command("setinterests"))
async def cmd_setinterests(message: Message):
    user_id = message.from_user.id
    init_user(user_id)
    
    args = message.text.replace("/setinterests", "").strip()
    
    if not args:
        current = get_user_setting(user_id, "interests")
        await message.answer(f"Текущие: {current or 'не указаны'}\n\nПример: /setinterests Музыка, аниме, готовить")
        return
    
    set_user_setting(user_id, "interests", args)
    await message.answer(f"Записал: {args} 🎯")


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    user_id = message.from_user.id
    user = init_user(user_id)
    
    name = user.get("name") or "Не указано"
    gender_map = {"female": "👩 Женский", "male": "👨 Мужской", "other": "⚧ Не указан", None: "❓ Не указан"}
    gender = gender_map.get(user.get("gender"), "❓ Не указан")
    appearance = user.get("appearance") or "Не описано"
    interests = user.get("interests") or "Не указаны"
    remind = "✅ Вкл" if user.get("reminders_enabled") else "❌ Выкл"
    mode = "🌙 Тёмный" if user.get("dark_mode") else "☀️ Обычный"
    
    await message.answer(
        f"📋 Твой профиль:\n\n"
        f"Имя: {name}\n"
        f"Пол: {gender}\n"
        f"Внешность: {appearance}\n"
        f"Интересы: {interests}\n\n"
        f"Настройки:\n"
        f"Напоминания: {remind}\n"
        f"Режим: {mode}\n\n"
        f"Изменить: /setname /setgender /setappearance /setinterests"
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    await message.answer(
        "🎛 *Главное меню*\n\nВыбери действие:",
        reply_markup=MAIN_MENU,
        parse_mode="Markdown"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = """
🔥 *Команды Алекса:*

👤 *Профиль*
`/profile` — посмотреть профиль
`/setname Имя` — установить имя
`/setgender` — выбрать пол
`/setappearance Описание` — внешность
`/setinterests Интересы` — интересы

⚙️ *Настройки*
`/remind` — вкл/выкл напоминания
`/dark` — тёмный режим 🌙
`/normal` — обычный режим

🧠 *Память*
`/memory` — что я помню
`/forget` — забыть всё
`/reset` — очистить историю

🎮 *Меню*
`/menu` — красивое меню
`/app` — открыть веб-приложение 🌙
    """
    await message.answer(help_text, parse_mode="Markdown")


@router.message(Command("app"))
async def cmd_app(message: Message):
    await message.answer(
        "🌙 *Веб-приложение*\n\n"
        "Открой веб-приложение нажав кнопку menu слева от поля ввода сообщения!\n\n"
        "📱 Если кнопки нет — обнови приложение Telegram до последней версии.",
        parse_mode="Markdown"
    )


@router.callback_query()
async def handle_callback(callback):
    user_id = callback.from_user.id
    data = callback.data
    
    if data == "menu_profile":
        user = init_user(user_id)
        name = user.get("name") or "Не указано"
        gender_map = {"female": "👩 Женский", "male": "👨 Мужской", "other": "⚧ Не указан", None: "❓ Не указан"}
        gender = gender_map.get(user.get("gender"), "❓ Не указан")
        appearance = user.get("appearance") or "Не описано"
        interests = user.get("interests") or "Не указаны"
        await callback.message.edit_text(
            f"👤 *Профиль*\n\n"
            f"Имя: {name}\n"
            f"Пол: {gender}\n"
            f"Внешность: {appearance}\n"
            f"Интересы: {interests}",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
    
    elif data == "menu_settings":
        await callback.message.edit_text(
            "⚙️ *Настройки*\n\n"
            "`/setname Имя` — изменить имя\n"
            "`/setgender` — выбрать пол\n"
            "`/setappearance Описание` — внешность\n"
            "`/setinterests` — интересы",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
    
    elif data == "menu_dark":
        set_user_setting(user_id, "dark_mode", True)
        await callback.message.edit_text(
            "🌙 *Тёмный режим включён*\n\n"
            "Алекс стал более... интересным. 😈",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
    
    elif data == "menu_normal":
        set_user_setting(user_id, "dark_mode", False)
        await callback.message.edit_text(
            "☀️ *Обычный режим*\n\n"
            "Алекс вернулся к нормальному общению. 😊",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
    
    elif data == "menu_remind":
        current = get_user_setting(user_id, "reminders_enabled", False)
        set_user_setting(user_id, "reminders_enabled", not current)
        status = "🔔 Включены" if not current else "🔕 Выключены"
        await callback.message.edit_text(
            f"🔔 *Напоминания*\n\n{status}\n\n"
            "Буду напоминать утром и вечером!",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
    
    elif data == "menu_memory":
        memory_context = get_memory_context(user_id)
        history = get_conversation_history(user_id, limit=5)
        text = "🧠 *Память*\n\n"
        if memory_context:
            text += f"📌 {memory_context}\n\n"
        else:
            text += "Пока ничего особенного не запомнил...\n\n"
        if history:
            text += "📝 Последние сообщения:\n"
            for msg in history[-3:]:
                role = "Ты" if msg["role"] == "user" else "Я"
                text += f"• {role}: {msg['content'][:50]}...\n"
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=MAIN_MENU)
    
    elif data == "menu_forget":
        data = load_data()
        uid_str = str(user_id)
        if uid_str in data["memory"]:
            data["memory"][uid_str] = {"topics": [], "facts": [], "last_session": None, "important": []}
            save_data(data)
        await callback.message.edit_text(
            "🔄 *Забыл всё*\n\n"
            "Чистый лист. Начинаем сначала! 🧹",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
    
    elif data == "menu_help":
        await callback.message.edit_text(
            "📖 *Помощь*\n\n"
            "Просто пиши мне! Я отвечу как живой человек.\n\n"
            "`/menu` — показать меню\n"
            "`/profile` — профиль\n"
            "`/dark` — тёмный режим\n"
            "`/reset` — очистить историю",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
    
    await callback.answer()


@router.message(F.text)
async def handle_message(message: Message):
    user_id = message.from_user.id
    user_message = message.text
    
    init_user(user_id)
    dark_mode = get_user_setting(user_id, "dark_mode", False)
    prompt = get_personalized_prompt(user_id, ALEX_DARK_ROMANCE if dark_mode else ALEX_SYSTEM_PROMPT)
    
    add_to_history(user_id, "user", user_message)
    
    history = get_conversation_history(user_id, limit=20)
    messages = [{"role": "system", "content": prompt}]
    for msg in history:
        messages.append(msg)
    
    try:
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=messages,
            max_tokens=350,
            temperature=0.85
        )
        
        assistant_message = response.choices[0].message.content
        add_to_history(user_id, "assistant", assistant_message)
        update_memory(user_id, user_message, assistant_message)
        
        await process_response(message, assistant_message, dark_mode)
        
    except Exception as e:
        await message.answer(f"что-то накрылось... {e}")


async def process_response(message: Message, text: str, dark_mode: bool):
    stickers = STICKERS_DARK if dark_mode else STICKERS_NORMAL
    sticker_to_send = None
    
    for tag, sticker_id in stickers.items():
        if tag in text:
            sticker_to_send = sticker_id
            text = text.replace(tag, "").strip()
            break
    
    if text:
        await message.answer(text)
    
    if sticker_to_send:
        try:
            await message.answer_sticker(sticker_to_send)
        except Exception:
            pass


@dp.startup()
async def on_startup():
    from aiogram.types import MenuButtonCommands
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    print("Меню бота настроено!")


async def main():
    dp.include_router(router)
    asyncio.create_task(scheduler())
    print("Алекс запущен! 🧠")
    print(f"Данные: {DATA_FILE}")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
