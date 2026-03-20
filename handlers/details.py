from utils import safe_edit, load_json, save_json, get_user_data, push_screen
from messages import MESSAGES
from keyboards import wallet_menu_keyboard, topup_currency_keyboard, back_button
from config import TOPUP_WALLETS, MANAGER_USERNAME
from telebot import types

CURRENCY_TO_BALANCE = {
    "usdt":  "usd",
    "rub":   "rub",
    "ton":   "ton",
    "stars": "stars",
}

TOPUP_LABELS = {
    "ton":   "💎 TON",
    "rub":   "💳 RUB",
    "usdt":  "💵 USDT",
    "stars": "⭐ Stars",
}


def add_balance(seller_id, currency: str, amount: float):
    balance_key = CURRENCY_TO_BALANCE.get(currency)
    if not balance_key:
        return
    users = load_json("data/users.json")
    uid = str(seller_id)
    if uid not in users:
        get_user_data(seller_id)
        users = load_json("data/users.json")
    users[uid]["balances"][balance_key] = round(
        users[uid]["balances"].get(balance_key, 0.0) + amount, 6
    )
    save_json("data/users.json", users)


def build_details_text(cid) -> str:
    user_data = get_user_data(cid)
    wallets  = user_data.get("wallets", {})
    balances = user_data.get("balances", {})

    def w(val): return val if val else "не указан"

    return (
        "💳 Управление реквизитами\n\n"
        "📋 Ваши кошельки:\n"
        f"• 💎 TON:          {w(wallets.get('ton'))}\n"
        f"• 💳 RUB карта:    {w(wallets.get('rub_card'))}\n"
        f"• 💵 USD/USDT:     {w(wallets.get('usd_card'))}\n"
        f"• 🌐 Любая валюта: {w(wallets.get('any_currency'))}\n\n"
        "💰 Ваши балансы:\n"
        f"• 💎 TON:   {balances.get('ton',   0.0):.6f}\n"
        f"• 💳 RUB:   {balances.get('rub',   0.0):.2f}\n"
        f"• 💵 USDT:  {balances.get('usd',   0.0):.2f}\n"
        f"• ⭐ Stars: {balances.get('stars', 0.0):.2f}\n\n"
        "Выберите действие:"
    )


def register_details_handler(bot):

    @bot.callback_query_handler(func=lambda call: call.data == "details")
    def handle_details(call):
        cid = call.message.chat.id
        push_screen(cid, "details")
        safe_edit(bot, call, build_details_text(cid), wallet_menu_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
    def handle_edit_wallet(call):
        cid = call.message.chat.id
        push_screen(cid, f"edit_{call.data}")
        mapping = {
            "edit_ton":          ("TON кошелёк",            "ton"),
            "edit_rub_card":     ("RUB карту",               "rub_card"),
            "edit_usd_card":     ("USD / USDT кошелёк",     "usd_card"),
            "edit_any_currency": ("реквизиты любой валюты", "any_currency"),
        }
        if call.data not in mapping:
            bot.answer_callback_query(call.id, "Неизвестное действие.")
            return
        label, key = mapping[call.data]
        safe_edit(bot, call, f"✏️ Введите новые реквизиты ({label}):", back_button("details"))
        bot.register_next_step_handler(call.message, save_wallet_input, cid, key, call.message)

    def save_wallet_input(message, cid, key, original_msg):
        if message.text and message.text.startswith('/'):
            bot.process_new_messages([message])
            return
        value = message.text.strip()
        users = load_json("data/users.json")
        uid = str(cid)
        if uid not in users:
            get_user_data(cid)
            users = load_json("data/users.json")
        users[uid]["wallets"][key] = value
        save_json("data/users.json", users)
        try:
            bot.edit_message_text(
                text="✅ Реквизиты обновлены.\n\n" + build_details_text(cid),
                chat_id=cid,
                message_id=original_msg.message_id,
                reply_markup=wallet_menu_keyboard()
            )
        except Exception:
            bot.send_message(cid, "✅ Реквизиты обновлены.\n\n" + build_details_text(cid), reply_markup=wallet_menu_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data == "topup_balance")
    def handle_topup(call):
        cid = call.message.chat.id
        push_screen(cid, "topup")
        safe_edit(bot, call, "💰 Пополнение баланса\n\nВыберите валюту:", topup_currency_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data in ("topup_ton", "topup_rub", "topup_usdt", "topup_stars"))
    def handle_topup_currency(call):
        cid = call.message.chat.id
        currency = call.data.replace("topup_", "")
        label    = TOPUP_LABELS.get(currency, currency.upper())
        wallet   = TOPUP_WALLETS.get(currency, "не указан")

        if currency == "stars":
            text = (
                f"⭐ Пополнение баланса Stars\n\n"
                f"Для пополнения Stars напишите менеджеру:\n"
                f"{MANAGER_USERNAME}\n\n"
                f"📸 Не забудьте отправить скриншот перевода менеджеру как подтверждение."
            )
        else:
            text = (
                f"💰 Пополнение баланса {label}\n\n"
                f"Переведите нужную сумму на следующие реквизиты:\n\n"
                f"{wallet}\n\n"
                f"📸 После перевода отправьте скриншот менеджеру:\n"
                f"{MANAGER_USERNAME}\n\n"
                f"⏳ После проверки менеджер зачислит средства на ваш баланс."
            )
        safe_edit(bot, call, text, back_button("topup"))

    @bot.callback_query_handler(func=lambda call: call.data == "withdraw_funds")
    def handle_withdraw(call):
        cid = call.message.chat.id
        push_screen(cid, "withdraw")
        from keyboards import withdraw_currency_keyboard
        safe_edit(bot, call, "📤 Вывод средств\n\nВыберите валюту для вывода:", withdraw_currency_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("withdraw_cur_"))
    def handle_withdraw_currency(call):
        cid = call.message.chat.id
        currency = call.data.replace("withdraw_cur_", "")
        label = {"ton": "💎 TON", "rub": "💳 RUB", "usd": "💵 USDT", "stars": "⭐ Stars"}.get(currency, currency.upper())
        user_data = get_user_data(cid)
        balance   = user_data.get("balances", {}).get(currency, 0.0)
        wallet    = user_data.get("wallets", {})
        wallet_map = {"ton": wallet.get("ton"), "rub": wallet.get("rub_card"), "usd": wallet.get("usd_card"), "stars": wallet.get("ton")}
        user_wallet = wallet_map.get(currency) or "не указан"
        text = (
            f"📤 Вывод средств — {label}\n\n"
            f"💰 Ваш баланс: {balance:.2f}\n"
            f"💳 Ваши реквизиты: {user_wallet}\n\n"
            f"Для вывода напишите менеджеру:\n"
            f"{MANAGER_USERNAME}\n\n"
            f"📝 Укажите сумму и валюту: {label}\n\n"
            f"⏳ Менеджер обработает заявку в ближайшее время."
        )
        safe_edit(bot, call, text, back_button("withdraw"))