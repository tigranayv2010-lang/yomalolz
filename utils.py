import json
import os

# ─── Навигационный стек ───────────────────────────────────────────────────────
# Хранит историю экранов для каждого пользователя
# Структура: { chat_id: ["main", "details", "edit_ton"] }
nav_stack: dict[int, list[str]] = {}

def push_screen(cid: int, screen: str):
    """Запушить экран в стек навигации."""
    stack = nav_stack.setdefault(cid, ["main"])
    if not stack or stack[-1] != screen:
        stack.append(screen)

def pop_screen(cid: int) -> str:
    """Убрать текущий экран и вернуть предыдущий."""
    stack = nav_stack.get(cid, ["main"])
    if len(stack) > 1:
        stack.pop()
    return stack[-1] if stack else "main"

def current_screen(cid: int) -> str:
    stack = nav_stack.get(cid, ["main"])
    return stack[-1] if stack else "main"

def reset_stack(cid: int):
    nav_stack[cid] = ["main"]


# ─── JSON-хелперы ─────────────────────────────────────────────────────────────

def load_json(file_path: str, default=None) -> dict:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        default_value = default if default is not None else {}
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(default_value, f, ensure_ascii=False, indent=2)
        return default_value
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(file_path: str, data: dict):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ─── Данные пользователя ──────────────────────────────────────────────────────

USERS_PATH = "data/users.json"

def get_user_data(user_id) -> dict:
    users = load_json(USERS_PATH)
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            "lang": "ru",
            "wallets": {
                "ton": "",
                "rub_card": "",
                "usd_card": "",
                "any_currency": ""
            },
            "balances": {
                "ton": 0.0,
                "rub": 0.0,
                "usd": 0.0,
                "stars": 0.0
            }
        }
        save_json(USERS_PATH, users)
    return users[uid]

def save_user_field(user_id, field: str, value):
    users = load_json(USERS_PATH)
    uid = str(user_id)
    if uid not in users:
        get_user_data(user_id)
        users = load_json(USERS_PATH)
    users[uid][field] = value
    save_json(USERS_PATH, users)


def save_username(user_id, username: str):
    """Сохраняет @username пользователя в базу. Вызывать при каждом /start."""
    if not username:
        return
    users = load_json(USERS_PATH)
    uid = str(user_id)
    if uid not in users:
        get_user_data(user_id)
        users = load_json(USERS_PATH)
    users[uid]["username"] = f"@{username.lstrip('@')}"
    save_json(USERS_PATH, users)


def safe_edit(bot, call_or_msg, text, reply_markup=None, parse_mode=None):
    """
    Универсальное редактирование сообщения.
    Работает и с фото (caption), и с текстом.
    Если редактирование невозможно — отправляет новое сообщение.
    """
    cid = call_or_msg.message.chat.id if hasattr(call_or_msg, 'message') else call_or_msg.chat.id
    mid = call_or_msg.message.message_id if hasattr(call_or_msg, 'message') else call_or_msg.message_id
    msg = call_or_msg.message if hasattr(call_or_msg, 'message') else call_or_msg

    kwargs = {"reply_markup": reply_markup}
    if parse_mode:
        kwargs["parse_mode"] = parse_mode

    if getattr(msg, 'content_type', None) == 'photo':
        try:
            bot.edit_message_caption(caption=text, chat_id=cid, message_id=mid, **kwargs)
            return
        except Exception:
            pass
    try:
        bot.edit_message_text(text=text, chat_id=cid, message_id=mid, **kwargs)
    except Exception:
        bot.send_message(cid, text, **kwargs)