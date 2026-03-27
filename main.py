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
    [InlineKeyboardButton(text="🎉 Развлечения", callback_data="menu_fun"),
     InlineKeyboardButton(text="📖 Помощь", callback_data="menu_help")],
    [InlineKeyboardButton(text="🔄 Забыть", callback_data="menu_forget")],
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
            model="llama-3.3-70b-versatile",
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
            model="llama-3.3-70b-versatile",
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
            model="llama-3.3-70b-versatile",
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
`/stats` — твоя статистика 📊

⚙️ *Настройки*
`/remind` — вкл/выкл напоминания
`/dark` — тёмный режим 🌙
`/normal` — обычный режим

🧠 *Память*
`/memory` — что я помню
`/forget` — забыть всё
`/reset` — очистить историю

🎉 *Развлечения*
`/fun` — меню развлечений
`/fortune` — гадание 🎱
`/joke` — анекдот 😂
`/quiz` — викторина 🧠
`/rps` — камень-ножницы-бумага 🎮
`/magic Вопрос` — магический шар 🔮
`/roast` — троллинг 🔥
`/insult` — оскорбления 😈
`/compliment` — комплимент ✨
`/rate Что` — оценка 🎯
`/truth` — правда 🤫
`/would_you` — ты бы когда-нибудь? 🤔
`/personality` — тип личности 🎭
`/wisdom` — мудрость дня 🌟
`/dice` — бросить кубик 🎲
`/slot` — игровой автомат 🎰
`/pick в1, в2, в3` — выбор за тебя 🎯
`/whowin а vs б` — кто круже ⚔️
`/hot` — насколько ты горячий 🔥
`/horoscope` — гороскоп 🔮
`/motivation` — мотивация 💪
`/meme` — мем дня 🖼️
`/coin` — подбросить монетку 🪙
`/randomnum` — случайное число 🎱
`/reverse текст` — реверс текста 🔄

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
            "`/reset` — очистить историю\n"
            "`/fun` — развлечения",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
    
    elif data == "menu_fun":
        fun_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎱 Гадание", callback_data="fun_fortune")],
            [InlineKeyboardButton(text="😂 Анекдот", callback_data="fun_joke")],
            [InlineKeyboardButton(text="🧠 Викторина", callback_data="fun_quiz")],
            [InlineKeyboardButton(text="🎮 РПС", callback_data="fun_rps")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_back")],
        ])
        await callback.message.edit_text(
            "🎉 *Развлечения*\n\n"
            "Выбери что хочешь:",
            parse_mode="Markdown",
            reply_markup=fun_keyboard
        )
    
    elif data == "fun_fortune":
        fortunes = [
            "🎱 Сегодня звёзды говорят... забей, они врут. Но попробуй что-то новое.",
            "🎱 Осторожно: кроличья нога сегодня не сработает. Но ты справишься.",
            "🎱 Совет дня: если сомневаешься — не сомневайся.",
            "🎱 Ты сегодня будешь либо прав, либо узнаешь что-то новое.",
            "🎱 Небо говорит: пора действовать. Или хотя бы поспать.",
            "🎱 Внимание: сегодняшний день — эксперимент. Удача включена.",
            "🎱 Звёзды намекают: не ешь тот сомнительный стритфуд.",
            "🎱 Сегодня тот день, когда всё может пойти... ну ты понял.",
        ]
        fun_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Ещё гадание", callback_data="fun_fortune")],
            [InlineKeyboardButton(text="🔙 К развлечениям", callback_data="menu_fun")],
        ])
        await callback.message.edit_text(random.choice(fortunes), reply_markup=fun_keyboard)
    
    elif data == "fun_joke":
        jokes = [
            "— Как называется фитнес для программистов?\n— Скрипты.\n— 😐",
            "— Что сказал SQL, когда его обидели?\n— ALTER TABLE feelings DROP COLUMN trust",
            "— Почему Python не пошёл на свидание?\n— Боялся, что его бросят (IndentationError)",
            "Почему дедлайны так называются? Потому что ближе к ним — тем мёртвее проект.",
            "Есть 10 типов людей: те, кто понимает двоичный код, и те, кто нет. 👀",
            "— Чем отличается Linux от винды?\n— Винда: 'У тебя мало памяти'\n— Линукс: 'Иди гуляй'",
            "— Что делает кошка на Vim?\n— :q!",
            "Жизнь как npm: установишь лишнее — проект не собирается.",
        ]
        fun_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="😂 Ещё анекдот", callback_data="fun_joke")],
            [InlineKeyboardButton(text="🔙 К развлечениям", callback_data="menu_fun")],
        ])
        await callback.message.edit_text(random.choice(jokes), reply_markup=fun_keyboard)
    
    elif data == "fun_quiz":
        quiz = random.choice(QUIZ_QUESTIONS)
        fun_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🧠 Ответ", callback_data="fun_quiz_answer")],
            [InlineKeyboardButton(text="🔄 Новая викторина", callback_data="fun_quiz")],
            [InlineKeyboardButton(text="🔙 К развлечениям", callback_data="menu_fun")],
        ])
        await callback.message.edit_text(f"🧠 *Викторина!*\n\n{quiz['q']}", parse_mode="Markdown", reply_markup=fun_keyboard)
    
    elif data == "fun_quiz_answer":
        quiz = random.choice(QUIZ_QUESTIONS)
        fun_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Новая викторина", callback_data="fun_quiz")],
            [InlineKeyboardButton(text="🔙 К развлечениям", callback_data="menu_fun")],
        ])
        await callback.message.edit_text(f"Ответ: *{quiz['a']}* 😏", parse_mode="Markdown", reply_markup=fun_keyboard)
    
    elif data == "fun_rps":
        await callback.message.edit_text(
            "🎮 *Камень-Ножницы-Бумага*\n\n"
            "Напиши мне `/rps` и начнём игру!",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
    
    elif data == "menu_back":
        await callback.message.edit_text(
            "🎛 *Главное меню*\n\nВыбери действие:",
            reply_markup=MAIN_MENU,
            parse_mode="Markdown"
        )
    
    await callback.answer()


@router.message(F.text & ~F.text.startswith("/"))
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
            model="llama-3.3-70b-versatile",
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


RPS_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🪨 Камень"), KeyboardButton(text="✂️ Ножницы"), KeyboardButton(text="📄 Бумага")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

QUIZ_QUESTIONS = [
    {"q": "Что сказал ноль восьмёрке?", "a": "классная фигура!"},
    {"q": "Почему программисты путают Хэллоуин и Рождество?", "a": "потому что OCT 31 = DEC 25"},
    {"q": "Что делает коала на работе?", "a": "ничего, его за это любят"},
    {"q": "Какой рост у Теслы?", "a": "1.98 — уровень амбиций"},
    {"q": "Что общего между кофе и марихуаной?", "a": "оба заставляют тебя видеть странные вещи"},
    {"q": "Почему пианино не может выиграть в казино?", "a": "оно не знает правил, но всё равно пытается"},
    {"q": "Что сказал гриб, когда его спросили 'как дела'?", "a": "споро!"},
    {"q": "Почему пельмени победили в войне?", "a": "они всех обернули вокруг пальца"},
]

RPS_CHOICES = ["🪨 Камень", "✂️ Ножницы", "📄 Бумага"]


@router.message(Command("fortune"))
async def cmd_fortune(message: Message):
    fortunes = [
        "🎱 Сегодня звёзды говорят... забей, они врут. Но попробуй что-то новое.",
        "🎱 Осторожно: кроличья нога сегодня не сработает. Но ты справишься.",
        "🎱 Совет дня: если сомневаешься — не сомневайся.",
        "🎱 Ты сегодня будешь либо прав, либо узнаешь что-то новое.",
        "🎱 Оракул молчит... ладно, шучу. Будь увереннее.",
        "🎱 Небо говорит: пора действовать. Или хотя бы поспать.",
        "🎱 Внимание: сегодняшний день — эксперимент. Удача включена.",
        "🎱 Звёзды намекают: не ешь тот сомнительный стритфуд.",
        "🎱 Совет: если кто-то напрягает — возможно, это ты напрягаешь.",
        "🎱 Сегодня тот день, когда всё может пойти... ну ты понял.",
    ]
    await message.answer(random.choice(fortunes))


@router.message(Command("joke"))
async def cmd_joke(message: Message):
    jokes = [
        "— Как называется фитнес для программистов?\n— Скрипты.\n— 😐",
        "— Что сказал SQL, когда его обидели?\n— ALTER TABLE feelings DROP COLUMN trust",
        "— Почему Python не пошёл на свидание?\n— Боялся, что его бросят (IndentationError)",
        "Почему дедлайны так называются? Потому что ближе к ним — тем мёртвее проект.",
        "Есть 10 типов людей: те, кто понимает двоичный код, и те, кто нет. 👀",
        "— Чем отличается Linux от винды?\n— Винда: 'У тебя мало памяти'\n— Линукс: 'У тебя идеальный день, иди гуляй'",
        "— Как успокоить программиста?\n— Сказать, что баг на самом деле фича.",
        "Жизнь как npm: установишь лишнее — проект не собирается. Удалишь нужное — всё сломалось.",
        "— Что делает кошка на Vim?\n— :q!",
        "Лучший комментарий в коде: 'Это работает, не трогай' © Дед-разработчик",
    ]
    await message.answer(random.choice(jokes))


@router.message(Command("quiz"))
async def cmd_quiz(message: Message):
    quiz = random.choice(QUIZ_QUESTIONS)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📖 Ответ")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
    set_user_setting(message.from_user.id, "quiz_active", True)
    set_user_setting(message.from_user.id, "quiz_answer", quiz["a"])
    
    await message.answer(f"🧠 Викторина!\n\n{quiz['q']}", reply_markup=keyboard)


@router.message(F.text == "📖 Ответ")
async def handle_quiz_answer(message: Message):
    if get_user_setting(message.from_user.id, "quiz_active"):
        answer = get_user_setting(message.from_user.id, "quiz_answer", "...")
        set_user_setting(message.from_user.id, "quiz_active", False)
        
        responses = [
            f"Правильный ответ: {answer} 😏",
            f"Ответ: {answer} Не знал? Не страшно.",
            f"{answer} — вот так вот.",
        ]
        await message.answer(random.choice(responses), reply_markup=None)


@router.message(Command("rps"))
async def cmd_rps(message: Message):
    set_user_setting(message.from_user.id, "rps_active", True)
    await message.answer(
        "🎮 Камень-Ножницы-Бумага!\n\nВыбирай:",
        reply_markup=RPS_KEYBOARD
    )


@router.message(F.text.in_(RPS_CHOICES))
async def handle_rps(message: Message):
    if not get_user_setting(message.from_user.id, "rps_active"):
        return
    
    user_choice = message.text
    ai_choice = random.choice(RPS_CHOICES)
    
    results = {
        ("🪨 Камень", "✂️ Ножницы"): "win",
        ("🪨 Камень", "📄 Бумага"): "lose",
        ("✂️ Ножницы", "📄 Бумага"): "win",
        ("✂️ Ножницы", "🪨 Камень"): "lose",
        ("📄 Бумага", "🪨 Камень"): "win",
        ("📄 Бумага", "✂️ Ножницы"): "lose",
    }
    
    if user_choice == ai_choice:
        result_text = "🤝 Ничья!"
    elif results.get((user_choice, ai_choice)) == "win":
        result_text = "😂 Твой ход победил! Я проиграл."
    else:
        result_text = "😈 Мой ход победил! Ты проиграл."
    
    await message.answer(
        f"🎮 Результат:\n\nТы: {user_choice}\nЯ: {ai_choice}\n\n{result_text}",
        reply_markup=None
    )
    set_user_setting(message.from_user.id, "rps_active", False)


@router.message(F.text == "🔙 Назад")
async def handle_back(message: Message):
    set_user_setting(message.from_user.id, "rps_active", False)
    set_user_setting(message.from_user.id, "quiz_active", False)
    await message.answer("Вернулся в чат 👋", reply_markup=None)


@router.message(Command("fun"))
async def cmd_fun(message: Message):
    fun_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎱 Гадание", callback_data="fun_fortune")],
        [InlineKeyboardButton(text="🧠 Викторина", callback_data="fun_quiz")],
        [InlineKeyboardButton(text="😂 Анекдот", callback_data="fun_joke")],
        [InlineKeyboardButton(text="🎮 РПС", callback_data="fun_rps")],
    ])
    await message.answer("🎉 *Развлечения:*\n\nВыбирай что хочешь:", reply_markup=fun_keyboard, parse_mode="Markdown")


@router.message(Command("magic"))
async def cmd_magic(message: Message):
    args = message.text.replace("/magic", "").strip()
    if not args:
        await message.answer("Напиши /magic Вопрос\n\nПример: /magic Стоит ли мне идти на работу?")
        return
    
    predictions = [
        "Безусловно да. Или нет. Кто знает...",
        "Звёзды говорят — попробуй. Но осторожно.",
        "Мой хрустальный шар показывает... пофиг.",
        "Ответ: зависит от того, сколько ты готов потерять.",
        "Да. Но потом пожалеешь. Или нет.",
        "Не сегодня. Подожди неделю.",
        "А ты как думаешь? 🤔",
        "Скорее да, чем нет. Но это не точно.",
    ]
    await message.answer(f"🔮 *{args}*\n\n{random.choice(predictions)}", parse_mode="Markdown")


@router.message(Command("roast"))
async def cmd_roast(message: Message):
    roasts = [
        "Ты так уверен в себе... это мило. Или жалко. Не помню.",
        "Твой IQ где-то между температурой кипения и точкой замерзания.",
        "Если бы глупость была работой, ты был бы генеральным директором.",
        "Ты как виндоус — все знают что надо обновиться, но никто не хочет.",
        "С твоей логикой ты мог бы доказать что небо зелёное.",
        "Красивая внешность? Нет. Интересная личность? Тоже нет. Но ты стараешься! 💀",
        "Ты типичный человек, который говорит 'я не типичный человек'.",
        "У тебя столько извилин, что некоторые из них точно порвались.",
        "Ты знаешь, что единственное что ты можешь контролировать — это кнопка громкости?",
        "Зато ты не скучный... ладно, шучу. Ты скучный. Но хотя бы честно. 😂",
    ]
    user_name = get_user_setting(message.from_user.id, "name")
    name = f" {user_name}" if user_name else ""
    await message.answer(f"🔥 *Поджигаю*{name}...\n\n{random.choice(roasts)}", parse_mode="Markdown")


@router.message(Command("insult"))
async def cmd_insult(message: Message):
    insults = [
        "Ты как обезьяна с гранатой — опасно и непредсказуемо.",
        "Если бы ты был продуктом — тебя бы вернули.",
        "Ты тратишь больше кислорода чем приносишь пользы.",
        "Тебе нужно зеркало? Нет, подожди... оно не виновато.",
        "Ты как кальций — вроде нужен, но в таком количестве — перебор.",
        "Однажды ты встанешь на колено и... нет, не для предложения. Просто упадёшь.",
        "Ты думаешь что ты центр вселенной? Остальные так не считают.",
        "Человек-пазл, но половины деталей не хватает.",
        "Ты либо плывёшь, либо тонешь. Судя по всему — второе.",
        "Бог дал тебе лицо, а ты решил его не использовать. 😏",
    ]
    await message.answer(f"😈 *Атака!* 😈\n\n{random.choice(insults)}", parse_mode="Markdown")


@router.message(Command("compliment"))
async def cmd_compliment(message: Message):
    compliments = [
        "Не буду врать — ты в целом норм. Гордись.",
        "У тебя есть что-то... это \"что-то\" — харизма. Используй пока не поздно.",
        "Знаешь, ты не такой уж и плохой. Я удивлён, если честно.",
        "Ты один из тех людей, с кем можно реально поговорить. Редкость.",
        "В тебе есть глубина. Большинство не замечает, но она есть.",
        "Ты умеешь слушать — это бесит, но уважаю.",
        "Не каждый может быть таким... ладно, не каждый тупой. Это тоже талант.",
        "Ты в порядке. Серьёзно, это редкий комплимент от меня.",
        "С тобой интересно спорить — ты хотя бы аргументы приводишь.",
        "Есть в тебе что-то... притягательное. Не хочу разбираться что именно. 😏",
    ]
    user_name = get_user_setting(message.from_user.id, "name")
    name = f" {user_name}" if user_name else ""
    await message.answer(f"✨ *Комплимент от Алекса*{name}!\n\n{random.choice(compliments)}", parse_mode="Markdown")


@router.message(Command("rate"))
async def cmd_rate(message: Message):
    args = message.text.replace("/rate", "").strip()
    if not args:
        await message.answer("Использование: /rate Что оценить\n\nПример: /rate котики\n/rate моя жизнь")
        return
    
    rating = random.randint(3, 10)
    stars = "⭐" * rating + "☆" * (10 - rating)
    
    comments = {
        10: "Шикарно! Я в восторге! 🔥",
        9: "Почти идеально. Почти.",
        8: "Неплохо, очень неплохо!",
        7: "Сойдёт. Я бы взял.",
        6: "Нормально. Не шедевр, но и не треш.",
        5: "Золотая середина. Без слёз и без восторга.",
        4: "Могло быть лучше. Намного лучше.",
        3: "Оценил. С трудом.",
    }
    
    await message.answer(f"🎯 *Оценка*\n\n{args}\n\n{rating}/10 {stars}\n\n{comments.get(rating, 'Ну...')}", parse_mode="Markdown")


TRUTH_QUESTIONS = [
    "Когда в последний раз ты плакал и из-за чего?",
    "Какая твоя самая большая нереализованная мечта?",
    "О чём ты жалеешь больше всего в жизни?",
    "Кому ты никогда не можешь сказать 'нет' и почему?",
    "Какая твоя самая тёмная мысль, которую ты никому не рассказывал?",
    "Когда в последний раз ты врал? О чём?",
    "Что ты делаешь когда никто не видит?",
    "Какой секрет ты скрываешь ото всех?",
    "Кого ты на самом деле ненавидишь, но делаешь вид что любишь?",
    "О чём ты думаешь перед сном каждую ночь?",
    "Какую привычку ты стыдишься но не можешь бросить?",
    "Когда ты в последний раз чувствовал себя по-настоящему счастливым?",
]


@router.message(Command("truth"))
async def cmd_truth(message: Message):
    await message.answer(
        f"🤫 *Правда или действие: ПРАВДА*\n\n"
        f"{random.choice(TRUTH_QUESTIONS)}\n\n"
        f"Отвечай честно. Или не отвечай. Но знай — я буду судить. 😏",
        parse_mode="Markdown"
    )


WOULD_YOU_QUESTIONS = [
    "Ты бы когда-нибудь поехал в космос, даже если бы не вернулся?",
    "Ты бы бросил(а) всё и уехал(а) в другую страну один/одна?",
    "Ты бы вернулся(ась) к бывшему/бывшей, если бы узнал(а) что это судьба?",
    "Ты бы отказался от интернета навсегда ради миллиона долларов?",
    "Ты бы сказал правду начальнику что думаешь о нём?",
    "Ты бы променял(а) всех друзей на одного идеального человека?",
    "Ты бы хотел(а) узнать дату своей смерти, если бы мог?",
    "Ты бы солгал(а) в резюме ради мечты работы?",
    "Ты бы бросил(а) семью ради любви всей жизни?",
    "Ты бы украл(а) миллион, если бы знал(а) что не поймают?",
    "Ты бы отказался от мяса навсегда ради того кого любишь?",
    "Ты бы променял(а) свой голос на абсолютный слух?",
]


@router.message(Command("would_you"))
async def cmd_would_you(message: Message):
    await message.answer(
        f"🤔 *Ты бы когда-нибудь...?*\n\n"
        f"{random.choice(WOULD_YOU_QUESTIONS)}\n\n"
        f"Отвечай 'да', 'нет' или 'зависит от ситуации'. Мнения не принимаются. 😏",
        parse_mode="Markdown"
    )


PERSONALITY_TYPES = {
    "Хаотичный мудрец 🌪️": "Ты непредсказуемый, но в глубине души знаешь что делаешь. Наверное.",
    "Социальный вампир 🧛": "Ты заряжаешься от общения, но иногда просто хочешь тишины. И поспать.",
    "Перфекционист-неврастеник 😤": "Ты хочешь всё сделать идеально, но идеал недостижим. Смирись. Или нет.",
    "Тусовщик-одиночка 🎭": "Ты в центре внимания, но ночью планируешь побег в горы.",
    "Оптимистичный реалист 🌅": "Ты видишь мир как он есть, но всё равно веришь что будет хорошо.",
    "Циничный романтик 💔": "Ты разочарован в любви, но всё ещё надеешься. Мило. И грустно.",
    "Планетолог 🪐": "Ты думаешь о вселенной и чувствуешь себя маленьким. Это нормально.",
    "Внутренний ребёнок 👶": "Ты взрослый снаружи, но внутри всё ещё веришь в чудеса и деда мороза.",
}


@router.message(Command("personality"))
async def cmd_personality(message: Message):
    personality = random.choice(list(PERSONALITY_TYPES.items()))
    await message.answer(
        f"🎭 *Твой тип личности по Алексу:*\n\n"
        f"_{personality[0]}_\n\n"
        f"{personality[1]}\n\n"
        f"Не благодари. 😏",
        parse_mode="Markdown"
    )


@router.message(Command("wisdom"))
async def cmd_wisdom(message: Message):
    wisdoms = [
        "Жизнь — это не поиск себя. Это создание себя. Или хотя бы попытка.",
        "Не бойся перемен. Бойся остаться в том, что уже не работает.",
        "Иногда лучший ответ — это пойти спать.",
        "Делай так, чтобы потом не было стыдно. Или делай и не парься. Оба работают.",
        "Не каждый, кто улыбается, счастлив. Но тебе не обязательно об этом знать.",
        "Самые важные решения — те, где нет правильного ответа.",
        "Ты не обязан быть хорошим во всём. Достаточно быть хорошим в чём-то одном.",
        "Лучшее время начать — вчера. Второе лучшее — сейчас.",
        "Не сравнивай свою главу 1 с чьей-то главой 20.",
        "Иногда 'нет' — это полное предложение. Используй его.",
        "Не все люди, которые тебя ранили, заслуживают прощения. Но ты заслуживаешь покоя.",
        "Жизнь коротка. Если не получается — попробуй по-другому. Или забей. Кто остановит?",
    ]
    await message.answer(
        f"🌟 *Мудрость дня от Алекса:*\n\n"
        f"_{random.choice(wisdoms)}_\n\n"
        f"Запомни или забудь. Твоя жизнь.",
        parse_mode="Markdown"
    )


@router.message(Command("dice"))
async def cmd_dice(message: Message):
    dice = random.randint(1, 6)
    emoji = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"][dice - 1]
    await message.answer(f"🎲 Бросок!\n\n{emoji} — *{dice}*", parse_mode="Markdown")


@router.message(Command("slot"))
async def cmd_slot(message: Message):
    symbols = ["🍒", "🍋", "🍊", "🍇", "💎", "⭐", "🎰", "7️⃣"]
    
    roll = lambda: random.choice(symbols)
    result = [roll(), roll(), roll()]
    result_str = " | ".join(result)
    
    if result[0] == result[1] == result[2]:
        win_text = "\n\n🎉 ДЖЕКПОТ!!! 🎉"
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        win_text = "\n\n✨ Близко! Ещё разок?"
    else:
        win_text = "\n\n💸 Мимо... Попробуй ещё."
    
    await message.answer(
        f"🎰 *Игровой автомат!*\n\n"
        f"{result_str}\n"
        f"─────────────"
        f"{win_text}",
        parse_mode="Markdown"
    )


@router.message(Command("pick"))
async def cmd_pick(message: Message):
    args = message.text.replace("/pick", "").strip()
    if not args or "," not in args:
        await message.answer(
            "🎯 *Алекс выбирает!*\n\n"
            "Использование: /pick вариант1, вариант2, вариант3\n\n"
            "Пример: /pick пицца, шаурма, борщ",
            parse_mode="Markdown"
        )
        return
    
    options = [opt.strip() for opt in args.split(",") if opt.strip()]
    if len(options) < 2:
        await message.answer("Нужно минимум 2 варианта!")
        return
    
    choice = random.choice(options)
    
    reactions = [
        "Я выбираю...",
        "Думаю...",
        "Мой вердикт:",
        "Очевидный выбор:",
        "Без вопросов:",
    ]
    
    await message.answer(
        f"🎯 *Алекс выбирает!*\n\n"
        f"{random.choice(reactions)}\n\n"
        f"👉 *{choice}*\n\n"
        f"Не благодари. 😏",
        parse_mode="Markdown"
    )


@router.message(Command("whowin"))
async def cmd_whowin(message: Message):
    args = message.text.replace("/whowin", "").strip()
    if not args or " vs " not in args.lower() and " или " not in args.lower():
        await message.answer(
            "⚔️ *Кто круче?*\n\n"
            "Использование: /whowin кофе vs чай\n"
            "Или: /whowin понедельник или пятница",
            parse_mode="Markdown"
        )
        return
    
    for sep in [" vs ", " VS ", " или ", " Или "]:
        if sep in args:
            parts = args.split(sep)
            break
    
    if len(parts) != 2:
        await message.answer("Формат: /whowin вариант1 vs вариант2")
        return
    
    option1, option2 = parts[0].strip(), parts[1].strip()
    
    roll = random.random()
    if roll < 0.4:
        winner, loser = option1, option2
    elif roll < 0.8:
        winner, loser = option2, option1
    else:
        await message.answer(
            f"⚔️ *{option1} vs {option2}*\n\n"
            f"🤝 Ничья! Оба хороши по-своему.",
            parse_mode="Markdown"
        )
        return
    
    votes1 = random.randint(1, 100)
    votes2 = 100 - votes1
    
    await message.answer(
        f"⚔️ *{option1} vs {option2}*\n\n"
        f"🏆 Победитель: *{winner}*!\n\n"
        f"{option1}: {'█' * (votes1 // 5)}{'░' * (20 - votes1 // 5)} {votes1}%\n"
        f"{option2}: {'█' * (votes2 // 5)}{'░' * (20 - votes2 // 5)} {votes2}%",
        parse_mode="Markdown"
    )


@router.message(Command("hot"))
async def cmd_hot(message: Message):
    rating = random.randint(60, 100)
    bars = "🔥" * (rating // 10) + "🖤" * (10 - rating // 10)
    
    comments = {
        (90, 100): "Да ты просто бомба! 🔥🔥🔥",
        (80, 89): "Огонь! Не каждый день такого встретишь.",
        (70, 79): "Вполне горячо. Можно смотреть.",
        (60, 69): "Ну... среднячок. Но есть потенциал.",
    }
    
    for (low, high), comment in comments.items():
        if low <= rating <= high:
            text = comment
            break
    
    await message.answer(
        f"🔥 *Твой горячий рейтинг:*\n\n"
        f"{rating}/100\n"
        f"{bars}\n\n"
        f"{text}",
        parse_mode="Markdown"
    )


ZODIAC_SIGNS = ["овен", "телец", "близнецы", "рак", "лев", "дева", "весы", "скорпион", "стрелец", "козерог", "водолей", "рыбы"]

@router.message(Command("horoscope"))
async def cmd_horoscope(message: Message):
    sign = None
    args = message.text.replace("/horoscope", "").strip().lower()
    
    for s in ZODIAC_SIGNS:
        if s in args:
            sign = s
            break
    
    if not sign:
        sign = random.choice(ZODIAC_SIGNS)
    
    horoscopes = [
        "Сегодня звёзды благоволят... ладно, они просто не против. Действуй!",
        "Осторожно: что-то хорошее может случиться. Будь готов.",
        "Неожиданный поворот! Но хороший. Наверное.",
        "День перемен. Или просто вторник. Неважно — решай сам.",
        "Твоя интуиция сегодня на высоте. Слушай внутренний голос.",
        "Кто-то оценит твои старания. Или нет. Но ты старайся.",
        "Отличный день для новых начинаний. Или для того чтобы забить.",
        "Звёзды говорят: пора рискнуть. Но не больше чем обычно.",
        "Сегодня будет продуктивно... или лениво. Зависит от тебя.",
        "Судьба даёт знак. Заметишь — хорошо. Нет — ну и ладно.",
    ]
    
    await message.answer(
        f"🔮 *Гороскоп для {sign.capitalize()}*\n\n"
        f"{random.choice(horoscopes)}\n\n"
        f"_Не воспринимай всерьёз. Или воспринимай. Мне всё равно._",
        parse_mode="Markdown"
    )


@router.message(Command("motivation"))
async def cmd_motivation(message: Message):
    motivations = [
        "Делай то, что боишься. Потом будешь бояться большего. 😏",
        "Ты не обязан быть лучшим. Достаточно быть лучше вчерашнего.",
        "Сложно — значит интересно. Если не сложно — тебе скучно.",
        "Каждый великий проект когда-то был 'а давай попробуем'.",
        "Не жди идеального момента. Он не наступит. Начинай.",
        "Ты тратишь энергию на жалобы? Потрать её на действия.",
        "Ошибки — это не провалы. Это учебные материалы.",
        "Кто не рискует — тот не пьёт шампанское. И не живёт полной жизнью.",
        "Ты сильнее чем думаешь. И слабее чем надеешься. В этом баланс.",
        "Сегодняшний день — это первый день остатка твоей жизни. Неплохо, да?",
        "Путь в 1000 миль начинается с одного шага. Сделай его.",
        "Не сдавайся. Остальные сдались раньше.",
    ]
    
    await message.answer(
        f"💪 *Мотивашка от Алекса:*\n\n"
        f"_{random.choice(motivations)}_\n\n"
        f"_Теперь иди и сделай что-нибудь._ 👊",
        parse_mode="Markdown"
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    user_id = message.from_user.id
    history = get_conversation_history(user_id, limit=1000)
    memory_context = get_memory_context(user_id)
    
    user = init_user(user_id)
    name = user.get("name") or "Незнакомец"
    dark_mode = user.get("dark_mode", False)
    reminders = user.get("reminders_enabled", False)
    
    msgs_count = len(history) // 2
    days_ago = "недавно"
    
    await message.answer(
        f"📊 *Статистика общения с Алексом*\n\n"
        f"👤 Имя: {name}\n"
        f"💬 Сообщений: ~{msgs_count}\n"
        f"🌙 Режим: {'Тёмный' if dark_mode else 'Обычный'}\n"
        f"🔔 Напоминания: {'Вкл' if reminders else 'Выкл'}\n"
        f"🧠 Темы в памяти: {len(memory_context) if memory_context else 0} символов\n\n"
        f"_Спасибо что общаешься со мной. Или нет._ 😏",
        parse_mode="Markdown"
    )


MEME_TEMPLATES = [
    "Когда ты: {user} а жизнь: {life}",
    "{user}: Я самый умный!\nЖизнь: *смеётся*",
    "{user} — {life} в 3 ночи",
    "Когда кажется что всё хорошо:\n{life}",
    "{user} ожидание vs {life} реальность",
]


@router.message(Command("meme"))
async def cmd_meme(message: Message):
    args = message.text.replace("/meme", "").strip()
    user_name = get_user_setting(message.from_user.id, "name") or "Ты"
    
    meme = random.choice(MEME_TEMPLATES)
    
    templates_life = [
        "а потом бац, и всё сломалось",
        "решает иначе",
        "говорит 'не сегодня'",
        "делает свой выбор",
        "поворачивается спиной",
        "даёт пинка",
        "меняет правила",
        "забывает про тебя",
    ]
    
    meme_text = meme.format(user=user_name, life=random.choice(templates_life))
    
    await message.answer(
        f"🖼️ *Мем дня:*\n\n"
        f"_{meme_text}_\n\n"
        f"_Отправь другу, пусть страдает_ 😈",
        parse_mode="Markdown"
    )


@router.message(Command("reverse"))
async def cmd_reverse(message: Message):
    args = message.text.replace("/reverse", "").strip()
    if not args:
        await message.answer("Напиши что-нибудь после команды.\n\nПример: /reverse Привет")
        return
    
    reversed_text = args[::-1]
    
    await message.answer(
        f"🔄 *Реверс!*\n\n"
        f"Было: {args}\n"
        f"Стало: {reversed_text}",
        parse_mode="Markdown"
    )


@router.message(Command("coin"))
async def cmd_coin(message: Message):
    result = random.choice(["Орёл 🦅", "Решка 🪙"])
    await message.answer(f"🪙 *Подбрасываем...*\n\n*{result}*", parse_mode="Markdown")


@router.message(Command("randomnum"))
async def cmd_randomnum(message: Message):
    args = message.text.replace("/randomnum", "").strip()
    
    if "-" in args:
        try:
            parts = args.split("-")
            min_num, max_num = int(parts[0].strip()), int(parts[1].strip())
        except:
            min_num, max_num = 1, 100
    else:
        min_num, max_num = 1, 100
    
    result = random.randint(min_num, max_num)
    await message.answer(f"🎱 *Случайное число!*\n\nТвой номер: *{result}*", parse_mode="Markdown")


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
