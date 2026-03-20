import os
import time
import threading
from telebot import TeleBot
from config import BOT_TOKEN

from handlers.start_handler import register_start_handler
from handlers.main_menu import register_main_menu_handler
from handlers.create_deal import register_create_deal_handler
from handlers.my_deals import register_my_deals_handler
from handlers.details import register_details_handler
from handlers.language import register_language_handler
from handlers.back_button import register_back_button_handler
from handlers.manager import register_manager_handler

bot = TeleBot(BOT_TOKEN)

# ── Keep-alive сервер чтобы Render не засыпал ─────────────────────────────────
from http.server import HTTPServer, BaseHTTPRequestHandler

class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

    def log_message(self, format, *args):
        pass  # отключаем логи запросов

def run_keep_alive():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), KeepAliveHandler)
    server.serve_forever()

# ──────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    register_back_button_handler(bot)
    register_start_handler(bot)
    register_main_menu_handler(bot)
    register_create_deal_handler(bot)
    register_my_deals_handler(bot)
    register_details_handler(bot)
    register_language_handler(bot)
    register_manager_handler(bot)

    # Запускаем keep-alive сервер в отдельном потоке
    t = threading.Thread(target=run_keep_alive, daemon=True)
    t.start()
    print(f"Keep-alive сервер запущен...")

    print("Бот запущен...")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Ошибка соединения: {e}")
            time.sleep(5)
            print("Перезапуск...")