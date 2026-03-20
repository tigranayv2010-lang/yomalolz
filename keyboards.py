from telebot import types


def main_menu_keyboard(lang_code='ru'):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✏️ Создать сделку", callback_data="create_deal"),
        types.InlineKeyboardButton("🗂️ Мои сделки",     callback_data="my_deals"),
        types.InlineKeyboardButton("💳 Реквизиты",       callback_data="details"),
        types.InlineKeyboardButton("🔎 Язык",            callback_data="language"),
        types.InlineKeyboardButton("📢 Наш сайт",        url="https://lzt.market/"),
        types.InlineKeyboardButton("❗ Поддержка",       url="https://t.me/yomamanager"),
    )
    return markup


def wallet_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💎 Изменить TON",                        callback_data="edit_ton"),
        types.InlineKeyboardButton("💳 Изменить RUB карту",                  callback_data="edit_rub_card"),
        types.InlineKeyboardButton("💵 Изменить USD/USDT кошелёк",           callback_data="edit_usd_card"),
        types.InlineKeyboardButton("🌐 Изменить реквизиты для любой валюты", callback_data="edit_any_currency"),
        types.InlineKeyboardButton("💰 Пополнить баланс",                    callback_data="topup_balance"),
        types.InlineKeyboardButton("📤 Вывод средств",                       callback_data="withdraw_funds"),
        types.InlineKeyboardButton("⬅️ Назад",                               callback_data="back_to_main"),
    )
    return markup


def topup_currency_keyboard():
    """Выбор валюты для пополнения."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💎 TON",   callback_data="topup_ton"),
        types.InlineKeyboardButton("💳 RUB",   callback_data="topup_rub"),
        types.InlineKeyboardButton("💵 USDT",  callback_data="topup_usdt"),
        types.InlineKeyboardButton("⭐ Stars", callback_data="topup_stars"),
    )
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_details"))
    return markup


def language_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        types.InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
    )
    return markup


def back_button(prev_screen: str = 'main'):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"back_to_{prev_screen}"))
    return markup


def confirm_payment_keyboard(deal_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Я оплатил", callback_data=f"confirm_payment_{deal_id}"))
    return markup


def confirm_gift_sent_keyboard(deal_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Подтвердить отправку подарка", callback_data=f"gift_sent_{deal_id}"))
    return markup


def deal_verdict_keyboard(deal_id, manager_username):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("✅ Завершить сделку", callback_data=f"complete_deal_{deal_id}"),
        types.InlineKeyboardButton("⚠️ Оспорить сделку", url=f"https://t.me/{manager_username.lstrip('@')}"),
    )
    return markup


def rating_keyboard(deal_id, role):
    markup = types.InlineKeyboardMarkup(row_width=5)
    markup.add(*[
        types.InlineKeyboardButton(f"{i}⭐", callback_data=f"rate_{role}_{deal_id}_{i}")
        for i in range(1, 6)
    ])
    return markup


def currency_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💵 USDT",          callback_data="currency_usdt"),
        types.InlineKeyboardButton("💳 RUB",           callback_data="currency_rub"),
        types.InlineKeyboardButton("💎 TON",           callback_data="currency_ton"),
        types.InlineKeyboardButton("⭐ Stars",          callback_data="currency_stars"),
        types.InlineKeyboardButton("🌐 Другая валюта", callback_data="currency_other"),
    )
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main"))
    return markup


def withdraw_currency_keyboard():
    """Выбор валюты для вывода средств."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💎 TON",   callback_data="withdraw_cur_ton"),
        types.InlineKeyboardButton("💳 RUB",   callback_data="withdraw_cur_rub"),
        types.InlineKeyboardButton("💵 USDT",  callback_data="withdraw_cur_usd"),
        types.InlineKeyboardButton("⭐ Stars", callback_data="withdraw_cur_stars"),
    )
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_details"))
    return markup