#!/usr/bin/env python3
"""
Много прост Telegram бот за поръчки на Snus 43MG
Изпълнение: python snus_bot.py
"""

import telebot
from telebot import types

# === ТВОЯТ TOKEN ===
TOKEN = "9073068508:AAGS2jF08tRuoiV3L8iYJtjtvmpXzLYuC5w"

bot = telebot.TeleBot(TOKEN)

# Регистрираме командите в Telegram (излизат в менюто ☰)
bot.set_my_commands([
    types.BotCommand("start", "🏠 Начало"),
    types.BotCommand("order", "🛒 Направи поръчка"),
    types.BotCommand("myorders", "📦 Моите поръчки"),
])

# Памет за поръчките
orders = {}
user_state = {}

# Конфигурация
PRICE_PER_CAN = 10.00  # €
FLAVORS = {
    "mango": "🥭 Mango 43MG",
    "blueberry": "🫐 Blueberry 43MG"
}
ADMIN_ID = 5032938049

@bot.message_handler(commands=['start'])
def start(message):
    """Стартово меню"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🛒 Направи поръчка"))
    markup.add(types.KeyboardButton("📦 Моите поръчки"))
    bot.send_message(
        message.chat.id,
        "👋 Здравей! Тук можеш да поръчаш **Snus 43MG**.\n\n"
        f"💰 Цена: {PRICE_PER_CAN:.2f} €/кутия\n"
        f"🥭 Вкусове: Mango, Blueberry\n\n"
        "Натисни бутона по-долу за да поръчаш:",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == "🛒 Направи поръчка")
def order_start(message):
    """Стъпка 1: Избор на вкус"""
    user_state[message.chat.id] = "awaiting_flavor"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for key, name in FLAVORS.items():
        markup.add(types.KeyboardButton(name))
    markup.add(types.KeyboardButton("❌ Отказ"))
    bot.send_message(
        message.chat.id,
        "🍃 **Избери вкус:**",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == "awaiting_flavor")
def order_flavor(message):
    """Приема вкуса и пита за количество"""
    if message.text == "❌ Отказ":
        user_state.pop(message.chat.id, None)
        start(message)
        return

    # Намеряваме вкуса по бутона
    flavor_key = None
    for key, name in FLAVORS.items():
        if name == message.text:
            flavor_key = key
            break

    if not flavor_key:
        bot.send_message(message.chat.id, "❌ Моля избери вкус от бутоните.")
        return

    user_state[message.chat.id] = {"flavor": flavor_key, "step": "awaiting_quantity"}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for qty in [1, 2, 3, 5, 10]:
        markup.add(types.KeyboardButton(str(qty)))
    markup.add(types.KeyboardButton("❌ Отказ"))

    flavor_name = FLAVORS[flavor_key]
    bot.send_message(
        message.chat.id,
        f"✅ Избран вкус: {flavor_name}\n\n📦 Колко кутии искаш?",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: isinstance(user_state.get(m.chat.id), dict) and user_state[m.chat.id].get("step") == "awaiting_quantity")
def order_quantity(message):
    """Приема количеството и пита за адрес"""
    if message.text == "❌ Отказ":
        user_state.pop(message.chat.id, None)
        start(message)
        return

    try:
        qty = int(message.text)
        if qty < 1 or qty > 50:
            bot.send_message(message.chat.id, "❌ Моля въведи число между 1 и 50.")
            return
    except ValueError:
        bot.send_message(message.chat.id, "❌ Моля въведи валидно число.")
        return

    data = user_state[message.chat.id]
    data["qty"] = qty
    data["step"] = "awaiting_address"

    flavor_name = FLAVORS[data["flavor"]]
    bot.send_message(
        message.chat.id,
        f"✅ {flavor_name} x{qty} ({qty * PRICE_PER_CAN:.2f} €)\n\n"
        "📍 Напиши адреса за доставка (име, телефон, адрес):",
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(func=lambda m: isinstance(user_state.get(m.chat.id), dict) and user_state[m.chat.id].get("step") == "awaiting_address")
def order_address(message):
    """Приема адреса и потвърждава поръчката"""
    data = user_state[message.chat.id]
    qty = data["qty"]
    flavor_key = data["flavor"]
    flavor_name = FLAVORS[flavor_key]
    address = message.text
    total = qty * PRICE_PER_CAN

    # Записва поръчката
    order_id = len(orders) + 1
    orders[order_id] = {
        "user_id": message.chat.id,
        "username": message.from_user.username or message.from_user.first_name,
        "flavor": flavor_key,
        "flavor_name": flavor_name,
        "qty": qty,
        "address": address,
        "total": total,
        "status": "Нова"
    }
    user_state.pop(message.chat.id, None)

    # Потвърждение за клиента
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🛒 Направи поръчка"))
    markup.add(types.KeyboardButton("📦 Моите поръчки"))

    bot.send_message(
        message.chat.id,
        f"✅ **Поръчката е приета!**\n\n"
        f"📦 Поръчка №{order_id}\n"
        f"🛍 {flavor_name} x{qty}\n"
        f"💰 Общо: {total:.2f} €\n"
        f"📍 Адрес: {address}\n\n"
        "Ще се свържем с теб за потвърждение и плащане при доставка.",
        parse_mode="Markdown",
        reply_markup=markup
    )

    # Известие за админа
    try:
        bot.send_message(
            ADMIN_ID,
            f"🔔 **НОВА ПОРЪЧКА №{order_id}**\n\n"
            f"👤 @{orders[order_id]['username']} (ID: {message.chat.id})\n"
            f"🛍 {flavor_name} x{qty}\n"
            f"💰 {total:.2f} €\n"
            f"📍 {address}",
            parse_mode="Markdown"
        )
    except:
        pass

@bot.message_handler(func=lambda m: m.text == "📦 Моите поръчки")
def my_orders(message):
    """Показва поръчките на потребителя"""
    user_orders = [o for o in orders.values() if o["user_id"] == message.chat.id]
    if not user_orders:
        bot.send_message(message.chat.id, "📭 Все още нямаш поръчки.")
        return

    text = "📦 **Твоите поръчки:**\n\n"
    for o in user_orders:
        text += f"№{list(orders.keys())[list(orders.values()).index(o)]} - {o['flavor_name']} x{o['qty']} - {o['total']:.2f} € - {o['status']}\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    """Админ панел - само за теб"""
    if message.chat.id != ADMIN_ID:
        return

    if not orders:
        bot.send_message(message.chat.id, "📭 Няма поръчки.")
        return

    text = "👑 **АДМИН ПАНЕЛ - Всички поръчки:**\n\n"
    for oid, o in orders.items():
        text += f"№{oid} | @{o['username']} | {o['flavor_name']} x{o['qty']} | {o['total']:.2f} € | {o['status']}\n"
        text += f"   📍 {o['address']}\n\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

print("🤖 Ботът стартира...")
bot.infinity_polling()