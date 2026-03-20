from utils import get_user_data, reset_stack
from messages import MESSAGES
from keyboards import main_menu_keyboard, wallet_menu_keyboard, topup_currency_keyboard, back_button
import handlers.create_deal as create_deal_module


def _safe_edit_text(bot, call, text, reply_markup=None):
    """
    Пытается отредактировать сообщение.
    Если сообщение — фото (caption), использует edit_message_caption.
    Если не получается — отправляет новое сообщение.
    """
    cid = call.message.chat.id
    mid = call.message.message_id
    # Если у сообщения есть фото — редактируем caption
    if call.message.content_type == 'photo':
        try:
            bot.edit_message_caption(
                caption=text,
                chat_id=cid,
                message_id=mid,
                reply_markup=reply_markup
            )
            return
        except Exception:
            pass
    # Обычное текстовое сообщение
    try:
        bot.edit_message_text(
            text=text,
            chat_id=cid,
            message_id=mid,
            reply_markup=reply_markup
        )
    except Exception:
        # Если вообще ничего не работает — новое сообщение
        bot.send_message(cid, text, reply_markup=reply_markup)


def _show_main_menu(bot, call, lang):
    _safe_edit_text(bot, call, MESSAGES[lang]['welcome'], main_menu_keyboard(lang))


def _show_details(bot, call, cid, lang):
    from handlers.details import build_details_text
    _safe_edit_text(bot, call, build_details_text(cid), wallet_menu_keyboard())


def _show_topup(bot, call, cid):
    _safe_edit_text(bot, call, "💰 Пополнение баланса\n\nВыберите валюту:", topup_currency_keyboard())


def register_back_button_handler(bot):

    @bot.callback_query_handler(func=lambda call: call.data.startswith("back_to_"))
    def handle_back(call):
        cid = call.message.chat.id
        target = call.data.replace("back_to_", "")

        # Отменяем активную сделку и очищаем next_step_handler
        create_deal_module.creating_deal_stage.pop(cid, None)
        bot.clear_step_handler_by_chat_id(cid)

        user_data = get_user_data(cid)
        lang = user_data.get("lang", "ru")

        if target == "main":
            reset_stack(cid)
            _show_main_menu(bot, call, lang)
        elif target == "details":
            _show_details(bot, call, cid, lang)
        elif target == "topup":
            _show_topup(bot, call, cid)
        elif target == "withdraw":
            from keyboards import withdraw_currency_keyboard
            _safe_edit_text(bot, call, "📤 Вывод средств\n\nВыберите валюту для вывода:", withdraw_currency_keyboard())
        else:
            reset_stack(cid)
            _show_main_menu(bot, call, lang)