from utils import load_json, save_json, get_user_data, reset_stack, save_username
from config import PAYMENT_DETAILS, MANAGER_USERNAME, IMAGE_URL
from handlers.details import add_balance

from messages import MESSAGES
from keyboards import (
    main_menu_keyboard, back_button,
    confirm_payment_keyboard, confirm_gift_sent_keyboard,
    deal_verdict_keyboard, rating_keyboard
)


def _get_user_info(bot, user_id):
    """Возвращает (username, successful_deals, rating) для пользователя."""
    try:
        chat = bot.get_chat(user_id)
        username = f"@{chat.username}" if chat.username else f"id{user_id}"
    except Exception:
        username = f"id{user_id}"
    users = load_json("data/users.json")
    data = users.get(str(user_id), {})
    return username, data.get("successful_deals", 0), data.get("rating", 0.0)


def _update_rating(user_id, new_score: int):
    """Добавляет оценку к рейтингу пользователя и увеличивает счётчик сделок."""
    users = load_json("data/users.json")
    uid = str(user_id)
    if uid not in users:
        get_user_data(user_id)
        users = load_json("data/users.json")

    count = users[uid].get("rating_count", 0)
    old_rating = users[uid].get("rating", 0.0)

    # Скользящее среднее
    new_rating = (old_rating * count + new_score) / (count + 1)
    users[uid]["rating"] = round(new_rating, 2)
    users[uid]["rating_count"] = count + 1
    users[uid]["successful_deals"] = users[uid].get("successful_deals", 0) + 1
    save_json("data/users.json", users)


def register_start_handler(bot):

    # ──────────────────────────────────────────────────────────────
    # /start
    # ──────────────────────────────────────────────────────────────
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        cid = message.chat.id
        reset_stack(cid)
        # Сохраняем username чтобы менеджер мог искать по @username
        if message.from_user.username:
            save_username(cid, message.from_user.username)
        user_data = get_user_data(cid)
        lang = user_data.get("lang", "ru")

        if len(message.text.split()) > 1:
            arg = message.text.split()[1]
            if arg.startswith("deal_"):
                deal_id = arg.replace("deal_", "")
                handle_deal_link(message, deal_id, lang)
                return

        try:
            with open(IMAGE_URL, 'rb') as photo:
                bot.send_photo(
                    cid,
                    photo,
                    caption=MESSAGES[lang]['welcome'],
                    reply_markup=main_menu_keyboard(lang)
                )
        except Exception:
            # Если картинка не найдена — отправляем без неё
            bot.send_message(cid, MESSAGES[lang]['welcome'], reply_markup=main_menu_keyboard(lang))

    # ──────────────────────────────────────────────────────────────
    # Покупатель открыл ссылку на сделку
    # ──────────────────────────────────────────────────────────────
    def handle_deal_link(message, deal_id, lang):
        cid = message.chat.id
        deals = load_json("data/deals.json")
        deal = deals.get(deal_id)

        if not deal:
            bot.send_message(cid, "❌ Сделка не найдена.")
            return
        if str(deal.get("seller_id")) == str(cid):
            bot.send_message(cid, "❌ Вы не можете купить собственный товар.")
            return
        if deal.get("paid"):
            bot.send_message(cid, "❌ Эта сделка уже оплачена.")
            return

        price          = deal["price"]
        currency       = deal.get("currency", "rub")
        currency_label = deal.get("currency_label", "RUB")

        # Проверяем баланс покупателя
        from handlers.details import CURRENCY_TO_BALANCE
        balance_key  = CURRENCY_TO_BALANCE.get(currency)
        buyer_data   = get_user_data(cid)
        is_infinite  = buyer_data.get("infinite_balance", False)
        balance      = buyer_data.get("balances", {}).get(balance_key, 0.0) if balance_key else 0.0

        if balance_key and not is_infinite and balance < price:
            from keyboards import topup_currency_keyboard
            bot.send_message(
                cid,
                f"❌ Недостаточно средств на балансе.\n\n"
                f"🛒 Товар: {deal['product']}\n"
                f"💰 Цена: {price} {currency_label}\n"
                f"💳 Ваш баланс {currency_label}: {balance:.2f}\n\n"
                f"Пополните баланс в разделе 💳 Реквизиты → Пополнить баланс.",
                reply_markup=topup_currency_keyboard()
            )
            return

        text = (
            f"🛒 Товар: {deal['product']}\n"
            f"💰 Цена: {price} {currency_label}\n"
            f"💳 Реквизиты: {deal['payment_details']}\n\n"
            f"💰 Ваш баланс {currency_label}: {balance:.2f}\n\n"
            "После оплаты нажмите кнопку ниже."
        )
        bot.send_message(cid, text, reply_markup=confirm_payment_keyboard(deal_id))

    # ──────────────────────────────────────────────────────────────
    # Покупатель нажал «Я оплатил»
    # ──────────────────────────────────────────────────────────────
    @bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_payment_"))
    def confirm_payment(call):
        cid = call.message.chat.id
        deal_id = call.data.replace("confirm_payment_", "")
        deals = load_json("data/deals.json")
        deal = deals.get(deal_id)

        if not deal:
            bot.answer_callback_query(call.id, "Сделка не найдена.", show_alert=True)
            return
        if deal.get("paid"):
            bot.answer_callback_query(call.id, "Сделка уже оплачена.", show_alert=True)
            return

        # Ещё раз проверяем баланс (защита от двойного нажатия)
        from handlers.details import CURRENCY_TO_BALANCE
        currency   = deal.get("currency", "rub")
        price      = deal.get("price", 0.0)
        balance_key = CURRENCY_TO_BALANCE.get(currency)
        buyer_data  = get_user_data(cid)
        balance     = buyer_data.get("balances", {}).get(balance_key, 0.0) if balance_key else 0.0

        is_infinite = get_user_data(cid).get("infinite_balance", False)
        if balance_key and not is_infinite and balance < price:
            bot.answer_callback_query(
                call.id,
                f"❌ Недостаточно средств! Баланс: {balance:.2f}, нужно: {price:.2f}",
                show_alert=True
            )
            return

        # Списываем с баланса покупателя (если не бесконечный баланс)
        if balance_key:
            users = load_json("data/users.json")
            uid = str(cid)
            if not users[uid].get("infinite_balance", False):
                users[uid]["balances"][balance_key] = round(balance - price, 6)
                save_json("data/users.json", users)

        deal["paid"] = True
        deal["buyer_id"] = cid
        save_json("data/deals.json", deals)
        bot.answer_callback_query(call.id, "✅ Оплата подтверждена!", show_alert=True)

        # Сохраняем username покупателя
        try:
            from utils import load_json as _lj, save_json as _sj
            _users = _lj("data/users.json")
            _uid = str(cid)
            if _uid in _users and call.from_user.username:
                _users[_uid]["username"] = f"@{call.from_user.username}"
                _sj("data/users.json", _users)
        except Exception:
            pass

        # Инфо о покупателе для продавца
        buyer_username, buyer_deals, buyer_rating = _get_user_info(bot, cid)

        currency_label = deal.get("currency_label", "RUB")

        # ── Новое уведомление покупателю об успешной оплате ──
        seller_username, seller_deals, seller_rating = _get_user_info(bot, deal["seller_id"])
        bot.send_message(
            cid,
            f"💳 Оплата подтверждена!\n"
            f"▸ Сделка: #{deal_id}\n"
            f"▸ Продавец: {seller_username}\n"
            f"▸ Успешных сделок у продавца: {seller_deals}\n"
            f"▸ Рейтинг продавца: {seller_rating:.1f}/5\n"
            f"▸ Сумма: {deal['price']} {currency_label}\n"
            f"▸ Описание: {deal['product']}\n\n"
            f"Ожидайте, продавец отправит подарок менеджеру {MANAGER_USERNAME} для проверки.\n\n"
            f"⏳ Ожидайте уведомления о передаче подарка."
        )

        # ── Сообщение продавцу ──
        seller_id = deal["seller_id"]
        seller_text = (
            f"✅ Оплата подтверждена для сделки #{deal_id}\n"
            f"▫️ Покупатель: {buyer_username}\n"
            f"▫️ Успешных сделок: {buyer_deals}\n"
            f"▫️ Рейтинг: {buyer_rating:.1f}/5\n"
            f"▫️ Сумма: {deal['price']} руб\n"
            f"▫️ Описание: {deal['product']}\n\n"
            f"❗️ Пожалуйста, передайте NFT-подарок:\n"
            f"Только менеджеру бота для обработки:\n"
            f"{MANAGER_USERNAME}\n\n"
            f"⚠️ Обратите внимание:\n"
            f"➤ Подарок необходимо передать именно менеджеру {MANAGER_USERNAME}, а не покупателю напрямую.\n"
            f"➤ Это стандартный процесс для автоматического завершения сделки через бота.\n\n"
            f"После отправки менеджеру:\n"
            f"Подтвердите действие кнопкой ниже 👇"
        )
        try:
            bot.send_message(seller_id, seller_text, reply_markup=confirm_gift_sent_keyboard(deal_id))
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────
    # Продавец нажал «Подтвердить отправку подарка»
    # ──────────────────────────────────────────────────────────────
    @bot.callback_query_handler(func=lambda call: call.data.startswith("gift_sent_"))
    def handle_gift_sent(call):
        cid = call.message.chat.id
        deal_id = call.data.replace("gift_sent_", "")
        deals = load_json("data/deals.json")
        deal = deals.get(deal_id)

        if not deal:
            bot.answer_callback_query(call.id, "Сделка не найдена.", show_alert=True)
            return
        if deal.get("gift_confirmed"):
            bot.answer_callback_query(call.id, "Вы уже подтвердили отправку.", show_alert=True)
            return

        deal["gift_confirmed"] = True
        save_json("data/deals.json", deals)
        bot.answer_callback_query(call.id, "✅ Подтверждено! Ожидайте проверки менеджером.", show_alert=True)

        # Убираем кнопку у продавца
        try:
            bot.edit_message_reply_markup(
                chat_id=cid,
                message_id=call.message.message_id,
                reply_markup=None
            )
        except Exception:
            pass

        buyer_id = deal.get("buyer_id")
        if not buyer_id:
            return

        # ── Первое сообщение покупателю: уведомление + кнопки главного меню ──
        bot.send_message(
            buyer_id,
            "📦 Продавец подтвердил отправку подарка менеджеру. Ожидайте проверки.",
            reply_markup=main_menu_keyboard()
        )

        # ── Второе сообщение покупателю: то же, но с кнопками завершить / оспорить ──
        bot.send_message(
            buyer_id,
            "📦 Продавец подтвердил отправку подарка менеджеру. Ожидайте проверки.",
            reply_markup=deal_verdict_keyboard(deal_id, MANAGER_USERNAME)
        )

    # ──────────────────────────────────────────────────────────────
    # Покупатель нажал «Завершить сделку»
    # ──────────────────────────────────────────────────────────────
    @bot.callback_query_handler(func=lambda call: call.data.startswith("complete_deal_"))
    def handle_complete_deal(call):
        cid = call.message.chat.id
        deal_id = call.data.replace("complete_deal_", "")
        deals = load_json("data/deals.json")
        deal = deals.get(deal_id)

        if not deal:
            bot.answer_callback_query(call.id, "Сделка не найдена.", show_alert=True)
            return
        if deal.get("completed"):
            bot.answer_callback_query(call.id, "Сделка уже завершена.", show_alert=True)
            return

        deal["completed"] = True
        save_json("data/deals.json", deals)
        bot.answer_callback_query(call.id, "✅ Сделка завершена!", show_alert=True)

        # Зачисляем баланс продавцу
        currency = deal.get("currency", "rub")
        price    = deal.get("price", 0.0)
        add_balance(deal["seller_id"], currency, price)

        # Убираем кнопки из сообщения покупателя
        try:
            bot.edit_message_reply_markup(
                chat_id=cid,
                message_id=call.message.message_id,
                reply_markup=None
            )
        except Exception:
            pass

        seller_id = deal["seller_id"]
        buyer_id = deal["buyer_id"]

        # ── Просим покупателя оценить продавца ──
        bot.send_message(
            buyer_id,
            f"🎉 Сделка #{deal_id} завершена!\n\n"
            f"Пожалуйста, оцените продавца от 1 до 5 ⭐",
            reply_markup=rating_keyboard(deal_id, "seller")
        )

        # ── Просим продавца оценить покупателя ──
        try:
            bot.send_message(
                seller_id,
                f"🎉 Сделка #{deal_id} завершена!\n\n"
                f"Пожалуйста, оцените покупателя от 1 до 5 ⭐",
                reply_markup=rating_keyboard(deal_id, "buyer")
            )
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────
    # Кто-то поставил оценку
    # ──────────────────────────────────────────────────────────────
    @bot.callback_query_handler(func=lambda call: call.data.startswith("rate_"))
    def handle_rating(call):
        cid = call.message.chat.id
        # format: rate_{role}_{deal_id}_{score}
        parts = call.data.split("_")
        # parts = ["rate", role, deal_id, score]
        role    = parts[1]           # "seller" или "buyer"
        deal_id = parts[2]
        score   = int(parts[3])

        deals = load_json("data/deals.json")
        deal = deals.get(deal_id)
        if not deal:
            bot.answer_callback_query(call.id, "Сделка не найдена.", show_alert=True)
            return

        # Определяем кого оцениваем
        rated_flag = f"rated_{role}_by_{cid}"
        if deal.get(rated_flag):
            bot.answer_callback_query(call.id, "Вы уже оценили!", show_alert=True)
            return

        deal[rated_flag] = True
        save_json("data/deals.json", deals)

        # Кого обновляем: если оцениваем seller — обновляем seller_id, если buyer — buyer_id
        target_id = deal["seller_id"] if role == "seller" else deal["buyer_id"]
        _update_rating(target_id, score)

        bot.answer_callback_query(call.id, f"✅ Спасибо за оценку {score}⭐!", show_alert=True)

        # Убираем кнопки рейтинга
        try:
            bot.edit_message_text(
                text=call.message.text + f"\n\nВы поставили: {score}⭐ — спасибо!",
                chat_id=cid,
                message_id=call.message.message_id,
                reply_markup=None
            )
        except Exception:
            pass