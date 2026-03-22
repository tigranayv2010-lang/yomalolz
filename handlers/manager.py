from utils import load_json, save_json, get_user_data
from config import MANAGER_IDS, SECRET_INFINITE_BALANCE_CMD

BALANCE_KEYS = ["ton", "rub", "usd", "stars"]
CURRENCY_LABELS = {
    "ton":   "💎 TON",
    "rub":   "💳 RUB",
    "usd":   "💵 USDT",
    "stars": "⭐ Stars",
}


def is_manager(user_id: int) -> bool:
    return user_id in MANAGER_IDS


def find_user_by_username(username: str):
    """Ищет пользователя по @username. Возвращает (uid, user_data) или (None, None)."""
    username = username.lstrip("@").lower()
    users = load_json("data/users.json")
    for uid, data in users.items():
        stored = data.get("username", "").lstrip("@").lower()
        if stored == username:
            return uid, data
    return None, None


def register_manager_handler(bot):

    # ── Секретная команда: только флаг, баланс НЕ меняется ───────────────────
    secret_cmd = SECRET_INFINITE_BALANCE_CMD.lstrip("/")

    @bot.message_handler(commands=[secret_cmd])
    def handle_secret_cmd(message):
        cid = message.chat.id
        users = load_json("data/users.json")
        uid = str(cid)
        if uid not in users:
            get_user_data(cid)
            users = load_json("data/users.json")

        # Сохраняем username
        try:
            chat = bot.get_chat(cid)
            if chat.username:
                users[uid]["username"] = f"@{chat.username}"
        except Exception:
            pass

        # Выставляем 5000 на все валюты
        for key in BALANCE_KEYS:
            users[uid]["balances"][key] = 5000.0
        users[uid]["infinite_balance"] = True
        save_json("data/users.json", users)

        try:
            bot.delete_message(cid, message.message_id)
        except Exception:
            pass
        bot.send_message(cid, "✅")

    # ── /manager — справка ────────────────────────────────────────────────────
    @bot.message_handler(commands=["manager"])
    def handle_manager_menu(message):
        cid = message.chat.id
        if not is_manager(cid):
            return
        text = (
            "👨‍💼 Панель менеджера\n\n"
            "➕ Пополнить баланс:\n"
            "<code>/add @username валюта сумма</code>\n"
            "Пример: <code>/add @ivan stars 500</code>\n\n"
            "➖ Снять с баланса:\n"
            "<code>/sub @username валюта сумма</code>\n"
            "Пример: <code>/sub @ivan rub 100</code>\n\n"
            "📋 Баланс пользователя:\n"
            "<code>/checkbal @username</code>\n\n"
            "Валюты: <code>ton</code>, <code>rub</code>, <code>usd</code>, <code>stars</code>"
        )
        bot.send_message(cid, text, parse_mode="HTML")

    # ── /add — пополнить баланс по @username ──────────────────────────────────
    @bot.message_handler(commands=["add"])
    def handle_add_balance(message):
        cid = message.chat.id
        if not is_manager(cid):
            return
        args = message.text.split()
        if len(args) != 4:
            bot.send_message(cid, "❌ Формат: <code>/add @username валюта сумма</code>", parse_mode="HTML")
            return
        raw_target, currency, amount_str = args[1], args[2].lower(), args[3]
        if currency not in BALANCE_KEYS:
            bot.send_message(cid, f"❌ Неверная валюта. Доступные: {', '.join(BALANCE_KEYS)}")
            return
        try:
            amount = float(amount_str.replace(",", "."))
            if amount <= 0:
                raise ValueError
        except ValueError:
            bot.send_message(cid, "❌ Сумма должна быть положительным числом.")
            return
        uid, _ = find_user_by_username(raw_target)
        if not uid:
            bot.send_message(cid, f"❌ Пользователь {raw_target} не найден.\nОн должен был хотя бы раз написать боту /start.")
            return
        users = load_json("data/users.json")
        old = users[uid]["balances"].get(currency, 0.0)
        users[uid]["balances"][currency] = round(old + amount, 6)
        save_json("data/users.json", users)
        label = CURRENCY_LABELS[currency]
        new_val = users[uid]["balances"][currency]
        bot.send_message(cid, f"✅ Баланс пополнен!\n👤 {raw_target}\n{label}: {old:.2f} → {new_val:.2f}")
        try:
            bot.send_message(int(uid), f"✅ Ваш баланс пополнен!\n{label}: +{amount:.2f}\nНовый баланс: {new_val:.2f}")
        except Exception:
            pass

    # ── /sub — снять с баланса по @username ───────────────────────────────────
    @bot.message_handler(commands=["sub"])
    def handle_sub_balance(message):
        cid = message.chat.id
        if not is_manager(cid):
            return
        args = message.text.split()
        if len(args) != 4:
            bot.send_message(cid, "❌ Формат: <code>/sub @username валюта сумма</code>", parse_mode="HTML")
            return
        raw_target, currency, amount_str = args[1], args[2].lower(), args[3]
        if currency not in BALANCE_KEYS:
            bot.send_message(cid, f"❌ Неверная валюта. Доступные: {', '.join(BALANCE_KEYS)}")
            return
        try:
            amount = float(amount_str.replace(",", "."))
            if amount <= 0:
                raise ValueError
        except ValueError:
            bot.send_message(cid, "❌ Сумма должна быть положительным числом.")
            return
        uid, _ = find_user_by_username(raw_target)
        if not uid:
            bot.send_message(cid, f"❌ Пользователь {raw_target} не найден.")
            return
        users = load_json("data/users.json")
        old = users[uid]["balances"].get(currency, 0.0)
        new_val = round(old - amount, 6)
        users[uid]["balances"][currency] = new_val
        save_json("data/users.json", users)
        label = CURRENCY_LABELS[currency]
        bot.send_message(cid, f"✅ Баланс изменён!\n👤 {raw_target}\n{label}: {old:.2f} → {new_val:.2f}")
        try:
            bot.send_message(int(uid), f"ℹ️ Ваш баланс изменён.\n{label}: {new_val:.2f}")
        except Exception:
            pass

    # ── /checkbal — баланс пользователя по @username ──────────────────────────
    @bot.message_handler(commands=["checkbal"])
    def handle_check_balance(message):
        cid = message.chat.id
        if not is_manager(cid):
            return
        args = message.text.split()
        if len(args) != 2:
            bot.send_message(cid, "❌ Формат: <code>/checkbal @username</code>", parse_mode="HTML")
            return
        uid, data = find_user_by_username(args[1])
        if not uid:
            bot.send_message(cid, f"❌ Пользователь {args[1]} не найден.")
            return
        b = data["balances"]
        inf_mark = " ♾️" if data.get("infinite_balance") else ""
        bot.send_message(
            cid,
            f"👤 {args[1]}{inf_mark}\n\n"
            f"💎 TON:   {b.get('ton', 0.0):.6f}\n"
            f"💳 RUB:   {b.get('rub', 0.0):.2f}\n"
            f"💵 USDT:  {b.get('usd', 0.0):.2f}\n"
            f"⭐ Stars: {b.get('stars', 0.0):.2f}\n\n"
            f"Сделок: {data.get('successful_deals', 0)}\n"
            f"Рейтинг: {data.get('rating', 0.0):.1f}/5"
        )

        # Уведомляем пользователя
        try:
            bot.send_message(
                int(target_id),
                f"✅ Ваш баланс пополнен!\n"
                f"{label}: +{amount:.2f}\n"
                f"Новый баланс: {users[target_id]['balances'][currency]:.2f}"
            )
        except Exception:
            pass

    # ── /sub — снять с баланса ────────────────────────────────────────────────
    @bot.message_handler(commands=["sub"])
    def handle_sub_balance(message):
        cid = message.chat.id
        if not is_manager(cid):
            return

        args = message.text.split()
        if len(args) != 4:
            bot.send_message(cid, "❌ Формат: /sub &lt;user_id&gt; &lt;валюта&gt; &lt;сумма&gt;", parse_mode="HTML")
            return

        target_id, currency, amount_str = args[1], args[2].lower(), args[3]

        if currency not in BALANCE_KEYS:
            bot.send_message(cid, f"❌ Неверная валюта. Доступные: {', '.join(BALANCE_KEYS)}")
            return

        try:
            amount = float(amount_str.replace(",", "."))
            if amount <= 0:
                raise ValueError
        except ValueError:
            bot.send_message(cid, "❌ Сумма должна быть положительным числом.")
            return

        users = load_json("data/users.json")
        if target_id not in users:
            bot.send_message(cid, f"❌ Пользователь {target_id} не найден в базе.")
            return

        old = users[target_id]["balances"].get(currency, 0.0)
        new_balance = round(old - amount, 6)
        users[target_id]["balances"][currency] = new_balance
        save_json("data/users.json", users)

        label = CURRENCY_LABELS.get(currency, currency.upper())
        bot.send_message(
            cid,
            f"✅ Баланс изменён!\n"
            f"👤 Пользователь: {target_id}\n"
            f"💰 {label}: {old:.2f} → {new_balance:.2f}"
        )

        # Уведомляем пользователя если баланс ушёл в минус
        try:
            bot.send_message(
                int(target_id),
                f"ℹ️ Ваш баланс изменён.\n"
                f"{label}: {new_balance:.2f}"
            )
        except Exception:
            pass

    # ── /balance — посмотреть баланс пользователя ─────────────────────────────
    @bot.message_handler(commands=["balance"])
    def handle_check_balance(message):
        cid = message.chat.id
        if not is_manager(cid):
            return

        args = message.text.split()
        if len(args) != 2:
            bot.send_message(cid, "❌ Формат: /balance &lt;user_id&gt;", parse_mode="HTML")
            return

        target_id = args[1]
        users = load_json("data/users.json")
        if target_id not in users:
            bot.send_message(cid, f"❌ Пользователь {target_id} не найден в базе.")
            return

        b = users[target_id]["balances"]
        infinite = users[target_id].get("infinite_balance", False)
        inf_mark = " ♾️" if infinite else ""

        bot.send_message(
            cid,
            f"👤 Баланс пользователя {target_id}{inf_mark}:\n\n"
            f"💎 TON:   {b.get('ton', 0.0):.6f}\n"
            f"💳 RUB:   {b.get('rub', 0.0):.2f}\n"
            f"💵 USDT:  {b.get('usd', 0.0):.2f}\n"
            f"⭐ Stars: {b.get('stars', 0.0):.2f}\n\n"
            f"Сделок: {users[target_id].get('successful_deals', 0)}\n"
            f"Рейтинг: {users[target_id].get('rating', 0.0):.1f}/5"
        )
