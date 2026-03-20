from utils import safe_edit, load_json, get_user_data, push_screen
from messages import MESSAGES
from keyboards import back_button


def register_my_deals_handler(bot):

    @bot.callback_query_handler(func=lambda call: call.data == "my_deals")
    def handle_my_deals(call):
        cid = call.message.chat.id
        push_screen(cid, "my_deals")
        user_data = get_user_data(cid)
        lang = user_data.get("lang", "ru")
        deals = load_json("data/deals.json")
        user_deals = [
            d for d in deals.values()
            if str(d.get('seller_id')) == str(cid) or str(d.get('buyer_id', '')) == str(cid)
        ]
        if not user_deals:
            response = MESSAGES[lang]['no_deals']
        else:
            lines = []
            for d in user_deals:
                role   = "Продавец" if str(d.get('seller_id')) == str(cid) else "Покупатель"
                status = "✅ Оплачено" if d['paid'] else "⏳ Не оплачено"
                currency_label = d.get('currency_label', 'руб')
                lines.append(f"• {d['product']} — {d['price']} {currency_label} | {status} | {role}")
            response = "🗂️ Ваши сделки:\n\n" + "\n".join(lines)
        safe_edit(bot, call, response, back_button("main"))