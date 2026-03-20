import os
from utils import safe_edit, load_json, save_json, get_user_data, push_screen
from messages import MESSAGES
from keyboards import language_keyboard, main_menu_keyboard


def register_language_handler(bot):

    @bot.callback_query_handler(func=lambda call: call.data == "language")
    def handle_language(call):
        cid = call.message.chat.id
        push_screen(cid, "language")
        user_data = get_user_data(cid)
        lang = user_data.get("lang", "ru")
        safe_edit(bot, call, MESSAGES[lang]['select_language'], language_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
    def handle_language_change(call):
        cid = call.message.chat.id
        new_lang = call.data.split('_')[1]
        users = load_json("data/users.json")
        uid = str(cid)
        if uid not in users:
            get_user_data(cid)
            users = load_json("data/users.json")
        users[uid]["lang"] = new_lang
        save_json("data/users.json", users)
        notice = MESSAGES[new_lang]['switched_to_russian'] if new_lang == 'ru' \
                 else MESSAGES[new_lang]['switched_to_english']
        bot.answer_callback_query(call.id, notice)
        safe_edit(bot, call, MESSAGES[new_lang]['welcome'], main_menu_keyboard(new_lang))