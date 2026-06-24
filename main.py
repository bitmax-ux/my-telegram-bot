import os
import re
import time
import requests
import telebot
from flask import Flask
from threading import Thread

# --- 1. Render እንዳይዘጋ የሚከለክለው የ Flask ዌብ ሰርቨር ክፍል ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# --- 2. የቦት መረጃዎች ---
BOT_TOKEN = "8887015953:AAFpms2COuvB75ZG44Fe1p_WfBB05SQjN5E"
BOT_USERNAME = "ethioo_helper_bot"

bot = telebot.TeleBot(BOT_TOKEN)
group_stats = {}

# --- 3. /calc Command ---
@bot.message_handler(commands=["calc"])
def calculator(message):
    try:
        expression = message.text.replace("/calc", "").strip()
        if not expression:
            bot.reply_to(message, "💡 ምሳሌ፦ /calc 50 * 2")
            return
        if not re.match(r"^[0-9\+\-\*\/\(\)\.\s]+$", expression):
            bot.reply_to(message, "❌ ልክ ያልሆነ ምልክት ነው።")
            return
        result = eval(expression)
        bot.reply_to(message, f"🔢 **ውጤት:** {result}", parse_mode="Markdown")
    except Exception:
        bot.reply_to(message, "❌ በስሌቱ ላይ ስህተት አለ።")

# --- 4. /crypto Command ---
@bot.message_handler(commands=["crypto"])
def get_crypto_price(message):
    try:
        coin_name = message.text.replace("/crypto", "").strip().lower()
        if not coin_name:
            bot.reply_to(message, "💡 ምሳሌ፦ /crypto solana")
            return

        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_name}&vs_currencies=usd&include_24hr_change=true"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers).json()

        if coin_name in response:
            price = response[coin_name]["usd"]
            change_24h = response[coin_name].get("usd_24h_change", 0)
            change_emoji = "📈" if change_24h >= 0 else "📉"

            crypto_msg = (
                f"💰 **{coin_name.upper()} ወቅታዊ መረጃ:**\n\n"
                f"💵 **ዋጋ:** ${price:,.2f} USD\n"
                f"{change_emoji} **የ24 ሰአት ለውጥ:** {change_24h:.2f}%"
            )
            bot.reply_to(message, crypto_msg, parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ ኮይኑ አልተገኘም (ምሳሌ: bitcoin, solana)")
    except Exception:
        bot.reply_to(message, "❌ መረጃ ማግኘት አልተቻለም። ድጋሚ ይሞክሩ።")

# --- 5. /rank Command ---
@bot.message_handler(commands=["rank"])
def show_rank(message):
    chat_id = message.chat.id
    if chat_id not in group_stats or not group_stats[chat_id]:
        bot.reply_to(message, "📊 እስካሁን የተመዘገበ መረጃ የለም።")
        return

    sorted_users = sorted(group_stats[chat_id].values(), key=lambda x: x["count"], reverse=True)
    rank_msg = "🏆 **የዛሬው የክብር መድረክ (Top ተናጋሪዎች):**\n\n"
    emojis = ["🥇", "🥈", "🥉"]

    for i, user in enumerate(sorted_users[:10]):
        medal = emojis[i] if i < 3 else f"{i+1}ኛ."
        rank_msg += f"{medal} {user['name']} — {user['count']} መልእክት\n"

    bot.reply_to(message, rank_msg, parse_mode="Markdown")

# --- 6. መልእክት መቁጠር እና Tag ማስተናገጃ ---
@bot.message_handler(func=lambda message: True)
def track_all_messages(message):
    if message.chat.type in ["group", "supergroup"]:
        chat_id = message.chat.id
        user_id = message.from_user.id
        user_name = message.from_user.first_name

        if chat_id not in group_stats:
            group_stats[chat_id] = {}
        if user_id not in group_stats[chat_id]:
            group_stats[chat_id][user_id] = {"name": user_name, "count": 0}

        group_stats[chat_id][user_id]["count"] += 1

    if message.text and f"@{BOT_USERNAME}".lower() in message.text.lower():
        bot.reply_to(message, "👋 ሰላም! እኔ የአንተ ግሩፕ ረዳት ቦት ነኝ።")

# --- 7. ቦቱን በሰላም ማስነሻ ክፍል ---
if __name__ == "__main__":
    print("🚀 ቦቱ በትክክል እየተነሳ ነው...")
    bot.infinity_polling()
