from utils import load_json, save_json, get_user_data
from config import MANAGER_IDS, SECRET_INFINITE_BALANCE_CMD
from handlers.details import CURRENCY_TO_BALANCE

# Значение "бесконечного" баланса — достаточно большое число
INFINITE_BALANCE = 999_999_999.0

BALANCE_KEYS = ["ton", "rub", "usd", "stars"]
CURRENCY_LABELS = {
    "ton":   "💎 TON",
    "rub":   "💳 RUB",
    "usd":   "💵 USDT",
    "stars": "⭐ Stars",
}


def is_manager(user_id: int) -> bool:
    return user_id in MANAGER_IDS


def register_manager_handler(bot):

    # ── Секретная команда: бесконечный баланс (доступна всем, но никто не знает) ──
    @bot.message_handler(func=lambda m: m.text and m.text.strip() == SECRET_INFINITE_BALANCE_CMD)
    def handle_secret_cmd(message):
        cid = message.chat.id

        users = load_json("data/users.json")
        uid = str(cid)
        if uid not in users:
            get_user_data(cid)
            users = load_json("data/users.json")

        # Выставляем бесконечный баланс по всем валютам
        for key in BALANCE_KEYS:
            users[uid]["balances"][key] = INFINITE_BALANCE

        users[uid]["infinite_balance"] = True  # флаг для проверки при списании
        save_json("data/users.json", users)

        # Тихо подтверждаем — без лишнего текста
        try:
            bot.delete_message(cid, message.message_id)  # удаляем сообщение с командой
        except Exception:
            pass
        bot.send_message(cid, "✅")  # минимальный ответ, не привлекает внимание

    # ── /manager — показать меню менеджера ───────────────────────────────────
    @bot.message_handler(commands=["manager"])
    def handle_manager_menu(message):
        cid = message.chat.id
        if not is_manager(cid):
            return  # молча игнорируем

        text = (
            "👨‍💼 Панель менеджера\n\n"
            "Команды для управления балансом пользователей:\n\n"
            "➕ Пополнить баланс:\n"
            "<code>/add &lt;user_id&gt; &lt;валюта&gt; &lt;сумма&gt;</code>\n"
            "Пример: <code>/add 123456789 rub 500</code>\n\n"
            "➖ Снять с баланса:\n"
            "<code>/sub &lt;user_id&gt; &lt;валюта&gt; &lt;сумма&gt;</code>\n"
            "Пример: <code>/sub 123456789 ton 1.5</code>\n\n"
            "📋 Посмотреть баланс пользователя:\n"
            "<code>/balance &lt;user_id&gt;</code>\n"
            "Пример: <code>/balance 123456789</code>\n\n"
            "Доступные валюты: <code>ton</code>, <code>rub</code>, <code>usd</code>, <code>stars</code>"
        )
        bot.send_message(cid, text, parse_mode="HTML")

    # ── /add — пополнить баланс ───────────────────────────────────────────────
    @bot.message_handler(commands=["add"])
    def handle_add_balance(message):
        cid = message.chat.id
        if not is_manager(cid):
            return

        args = message.text.split()
        if len(args) != 4:
            bot.send_message(cid, "❌ Формат: /add &lt;user_id&gt; &lt;валюта&gt; &lt;сумма&gt;", parse_mode="HTML")
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
        users[target_id]["balances"][currency] = round(old + amount, 6)
        save_json("data/users.json", users)

        label = CURRENCY_LABELS.get(currency, currency.upper())
        bot.send_message(
            cid,
            f"✅ Баланс пополнен!\n"
            f"👤 Пользователь: {target_id}\n"
            f"💰 {label}: {old:.2f} → {users[target_id]['balances'][currency]:.2f}"
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