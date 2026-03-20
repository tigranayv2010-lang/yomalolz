from utils import safe_edit, load_json, save_json, get_user_data, push_screen
from messages import MESSAGES
from keyboards import back_button, currency_keyboard

_bot = None
creating_deal_stage: dict = {}

CURRENCY_LABEL = {
    "usdt":  "USDT",
    "rub":   "RUB",
    "ton":   "TON",
    "stars": "Stars",
}


# ── Шаги ввода — определены НА УРОВНЕ МОДУЛЯ чтобы next_step_handler их видел ──

def process_currency_name_input(message, original_msg):
    cid = message.chat.id
    if cid not in creating_deal_stage:
        return
    if message.text and message.text.startswith('/'):
        creating_deal_stage.pop(cid, None)
        _bot.process_new_messages([message])
        return
    currency_name = message.text.strip().upper()[:10]
    creating_deal_stage[cid]['currency_label'] = currency_name
    creating_deal_stage[cid]['step'] = 'waiting_for_product'
    user_data = get_user_data(cid)
    lang = user_data.get("lang", "ru")
    try:
        _bot.edit_message_text(
            text=MESSAGES[lang]['create_deal_request'],
            chat_id=cid,
            message_id=original_msg.message_id,
            reply_markup=back_button("main")
        )
    except Exception:
        pass
    _bot.register_next_step_handler(original_msg, process_product_input, original_msg)


def process_product_input(message, original_msg):
    cid = message.chat.id
    if cid not in creating_deal_stage:
        return
    if message.text and message.text.startswith('/'):
        creating_deal_stage.pop(cid, None)
        _bot.process_new_messages([message])
        return
    user_data = get_user_data(cid)
    lang = user_data.get("lang", "ru")
    creating_deal_stage[cid]['product'] = message.text
    creating_deal_stage[cid]['step'] = 'waiting_for_price'
    currency_label = creating_deal_stage[cid].get('currency_label', '')
    try:
        _bot.edit_message_text(
            text=f"{MESSAGES[lang]['enter_price']} ({currency_label})",
            chat_id=cid,
            message_id=original_msg.message_id,
            reply_markup=back_button("main")
        )
    except Exception:
        _bot.send_message(cid, f"{MESSAGES[lang]['enter_price']} ({currency_label})", reply_markup=back_button("main"))
    _bot.register_next_step_handler(original_msg, process_price_input, original_msg)


def process_price_input(message, original_msg):
    cid = message.chat.id
    if cid not in creating_deal_stage:
        return
    if message.text and message.text.startswith('/'):
        creating_deal_stage.pop(cid, None)
        _bot.process_new_messages([message])
        return
    user_data = get_user_data(cid)
    lang = user_data.get("lang", "ru")
    try:
        price = float(message.text.replace(",", "."))
    except ValueError:
        _bot.reply_to(message, "❌ Цена должна быть числом. Попробуйте ещё раз:")
        _bot.register_next_step_handler(message, process_price_input, original_msg)
        return
    creating_deal_stage[cid]['price'] = price
    _create_and_save_deal(cid, original_msg, lang)


def _create_and_save_deal(cid, original_msg, lang):
    product        = creating_deal_stage[cid]['product']
    price          = creating_deal_stage[cid]['price']
    currency       = creating_deal_stage[cid].get('currency', 'rub')
    currency_label = creating_deal_stage[cid].get('currency_label', 'RUB')
    deals = load_json("data/deals.json")
    deal_id = str(len(deals) + 1)
    deals[deal_id] = {
        "seller_id":      cid,
        "product":        product,
        "price":          price,
        "currency":       currency,
        "currency_label": currency_label,
        "paid":           False,
        "payment_details": _get_seller_wallet(cid, currency),
    }
    save_json("data/deals.json", deals)
    creating_deal_stage.pop(cid, None)
    success_msg = (
        f"✅ Сделка создана!\n"
        f"Товар: {product}\n"
        f"Цена: {price} {currency_label}\n"
        f"Реквизиты: {deals[deal_id]['payment_details']}\n\n"
        f"Отправьте эту ссылку покупателю:\n"
        f"https://t.me/LOLZ_BOT_USERNAME?start=deal_{deal_id}"
    )
    try:
        _bot.edit_message_text(
            text=success_msg,
            chat_id=cid,
            message_id=original_msg.message_id,
            reply_markup=back_button("main")
        )
    except Exception:
        _bot.send_message(cid, success_msg, reply_markup=back_button("main"))


def _get_seller_wallet(seller_id, currency: str) -> str:
    user_data = get_user_data(seller_id)
    wallets = user_data.get("wallets", {})
    mapping = {
        "ton":   wallets.get("ton", ""),
        "rub":   wallets.get("rub_card", ""),
        "usdt":  wallets.get("usd_card", ""),
        "stars": wallets.get("ton", ""),
        "other": wallets.get("any_currency", ""),
    }
    wallet = mapping.get(currency, wallets.get("any_currency", ""))
    return wallet or "не указан — укажите реквизиты в разделе 💳 Реквизиты"


# ── Регистрация обработчиков ───────────────────────────────────────────────────

def register_create_deal_handler(bot):
    global _bot
    _bot = bot

    @bot.callback_query_handler(func=lambda call: call.data == "create_deal")
    def handle_create_deal(call):
        cid = call.message.chat.id
        push_screen(cid, "create_deal")
        creating_deal_stage[cid] = {'step': 'waiting_for_currency'}
        safe_edit(_bot, call, "💱 Выберите валюту сделки:", currency_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("currency_") and call.data != "currency_other")
    def handle_currency_choice(call):
        cid = call.message.chat.id
        if cid not in creating_deal_stage:
            return
        currency_code = call.data.replace("currency_", "")
        label = CURRENCY_LABEL.get(currency_code, currency_code.upper())
        creating_deal_stage[cid]['currency'] = currency_code
        creating_deal_stage[cid]['currency_label'] = label
        creating_deal_stage[cid]['step'] = 'waiting_for_product'
        user_data = get_user_data(cid)
        lang = user_data.get("lang", "ru")
        safe_edit(_bot, call, MESSAGES[lang]['create_deal_request'], back_button("main"))
        _bot.register_next_step_handler(call.message, process_product_input, call.message)

    @bot.callback_query_handler(func=lambda call: call.data == "currency_other")
    def handle_currency_other(call):
        cid = call.message.chat.id
        if cid not in creating_deal_stage:
            return
        creating_deal_stage[cid]['currency'] = 'other'
        creating_deal_stage[cid]['step'] = 'waiting_for_currency_name'
        safe_edit(_bot, call, "✏️ Введите инициалы валюты (например: AMD, EUR, GBP):", back_button("main"))
        _bot.register_next_step_handler(call.message, process_currency_name_input, call.message)