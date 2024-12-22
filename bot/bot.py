import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from main import get_products_from_db, get_random_products_from_db, get_products
import threading

TOKEN = 'ENTER_YOUR_BOT_TOKEN'
bot = telebot.TeleBot(TOKEN)

categories = {
    'Мужская одежда': 'manwear',
    'Женская одежда': 'womanwear',
    'Детская одежда': 'childwear',
    'Головные уборы': 'headwear',
    'Сумки и рюкзаки': 'bags_and_backpacks',
    'Аксессуары': 'accessory',
    'Чехлы для телефонов': 'cases',
    'Домашний текстиль': 'textile',
    'Посуда': 'tableware',
    'Для интерьера': 'interior',
    'Для школы': 'school',
    'Для пляжа': 'beach',
    'Для спорта': 'sports_goods',
    'Сувениры и подарки': 'all_souvenirs',
    'Вся одежда': 'odezhda',
    'Одежда plus size': 'size_plus',
    'Распродажа': 'sale'
}

emoji_cart = "🛒"
emoji_price = "💲"
emoji_back = "🔙"
emoji_gift = "🎁"

parsing_in_progress = False


def main_menu(chat_id, message_id=None):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💯 Категории", callback_data="categories"))
    markup.add(InlineKeyboardButton("😖 Я не знаю что выбрать", callback_data="random"))
    if message_id:
        bot.edit_message_text("Приветствую! Этот бот поможет тебе найти подарок на новый год для твоих друзей и близких 🎅", chat_id, message_id, reply_markup=markup)
    else:
        bot.send_message(chat_id, "Приветствую! Этот бот поможет тебе найти подарок на новый год для твоих друзей и близких 🎅", reply_markup=markup)


def start_parsing(chat_id):
    global parsing_in_progress
    parsing_in_progress = True

    for category_slug in categories.values():
        get_products(category_slug, bot, chat_id)

    bot.send_message(chat_id, " Подготовка завершена! Переходим в главное меню!.")
    parsing_in_progress = False
    main_menu(chat_id)


@bot.message_handler(commands=['start'])
def start(message):
    global parsing_in_progress

    if not parsing_in_progress:
        bot.send_message(message.chat.id, " Начинается подготовка. Пожалуйста, подождите 🕕")
        threading.Thread(target=start_parsing, args=(message.chat.id,)).start()
    else:
        bot.send_message(message.chat.id, " Парсинг уже выполняется. Пожалуйста, подождите 🕕")


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if parsing_in_progress:
        bot.answer_callback_query(call.id, " Парсинг еще идет. Подождите завершения 🕕")
        return

    if call.data == "categories":
        markup = InlineKeyboardMarkup()
        for category_name, slug in categories.items():
            markup.add(InlineKeyboardButton(category_name, callback_data=f"category|{slug}"))
        markup.add(InlineKeyboardButton(emoji_back + " Назад", callback_data="back_to_main"))
        bot.edit_message_text("Выберите категорию 💗", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("category|"):
        category_slug = call.data.split("|")[1]
        products = get_products_from_db(category_slug)

        if not products:
            bot.answer_callback_query(call.id, f"В категории {category_slug} нет товаров.")
            return

        markup = InlineKeyboardMarkup()
        message_text = f"Товары в категории {category_slug.capitalize()}:\n\n"
        markup.add(InlineKeyboardButton(emoji_back + " Назад", callback_data="categories"))
        for product in products:
            message_text += f"{emoji_cart} {product['name']} - {emoji_price} {product['price']} ₽\n"

        message_text += f"\n{emoji_gift} Ссылки на товары:\n"
        for product in products:
            markup.add(InlineKeyboardButton(product['name'], url=product['link']))

        bot.edit_message_text(message_text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "back_to_main":
        main_menu(call.message.chat.id, call.message.message_id)

    elif call.data == "random":
        products = get_random_products_from_db()
        markup = InlineKeyboardMarkup()
        message_text = "🎁 Случайные товары:\n\n"
        for product in products:
            message_text += f"{emoji_cart} {product['name']} - {emoji_price} {product['price']} ₽\n"
            markup.add(InlineKeyboardButton(product['name'], url=product['link']))

        markup.add(InlineKeyboardButton(emoji_back + " Назад", callback_data="back_to_main"))
        bot.edit_message_text(message_text, call.message.chat.id, call.message.message_id, reply_markup=markup)


bot.polling()
