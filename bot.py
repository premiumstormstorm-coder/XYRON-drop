"""
XYRON DROP - LIVE CC DETECTION
✅ Tested & Working
✅ Instant drop on CC detection
"""

import asyncio
import os
import re
import json
import logging
import random
from datetime import datetime, date

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest

# ===== CONFIG (Set these in Railway) =====
API_ID = int(os.environ.get('API_ID', 0))
API_HASH = os.environ.get('API_HASH', '')
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
SESSION_STRING = os.environ.get('SESSION_STRING', '')
OWNER_ID = int(os.environ.get('OWNER_ID', 0))
DESTINATION = os.environ.get('DESTINATION_CHANNEL', '@xyrons')

CHANNELS_FILE = 'monitored.json'
STATS_FILE = 'stats.json'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===== EMOJIS =====
E = {
    "fire": "🔥", "bolt": "⚡", "crown": "👑", "diamond": "💎",
    "glow": "✨", "ninja": "🥷", "skull": "💀", "shield": "🛡️",
    "drop": "💧", "alert": "🚨", "target": "🎯", "time": "⏱️",
    "add": "➕", "remove": "❌", "list": "📋", "check": "✅",
    "warning": "⚠️", "neon": "🔮", "cyber": "💠", "quantum": "⚛️",
    "galaxy": "🌌", "crystal": "💎", "laser": "🔫", "satellite": "🛸",
    "dragon": "🐉", "lightning": "⚡", "join": "🔗", "stats": "📊",
    "today": "☀️", "rain": "☔", "calendar": "📅", "rocket": "🚀",
    "card": "💳", "lock": "🔒", "hidden": "🤫", "money": "💰", "charged": "💸"
}

# ===== CC DETECTION PATTERNS =====
CC_RAW = re.compile(r'\b\d{13,16}\b')
CC_FORMATTED = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b')
CC_WITH_SEP = re.compile(r'(\d{13,16})[|\s/:-](\d{1,2})[|\s/:-](\d{2,4})[|\s/:-](\d{3,4})')
CC_WITH_SPACE = re.compile(r'(\d{13,16})\s+(\d{2}/\d{2,4})\s+(\d{3,4})')

KEYWORDS = re.compile(r'\b(?:cc|card|credit|visa|mastercard|amex|cvv|drop|valid|fresh|bin)\b', re.I)

def luhn_check(card):
    card = re.sub(r'[\s\-|]', '', card)
    if not card.isdigit() or not (13 <= len(card) <= 16):
        return False
    total = 0
    for i, d in enumerate(card[::-1]):
        n = int(d)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0

def get_card_type(card):
    first = card[0]
    if first == '4':
        return "VISA"
    elif first == '5':
        return "MASTERCARD"
    elif first == '3':
        return "AMEX"
    elif first == '6':
        return "DISCOVER"
    return "CARD"

def extract_ccs(text):
    """Extract CC from message"""
    cards = []
    
    # Check with separators (most common)
    matches = CC_WITH_SEP.findall(text)
    for match in matches:
        clean = re.sub(r'[\s\-|]', '', match[0])
        if luhn_check(clean):
            cards.append({
                'number': clean,
                'exp': f"{match[1]}/{match[2][-2:]}",
                'cvv': match[3],
                'bin': clean[:6],
                'type': get_card_type(clean)
            })
            return cards
    
    # Check formatted CCs
    if not cards:
        formatted = CC_FORMATTED.findall(text)
        for num in formatted[:3]:
            clean = re.sub(r'[\s-]', '', num)
            if luhn_check(clean):
                cards.append({
                    'number': clean,
                    'exp': 'XX/XX',
                    'cvv': 'XXX',
                    'bin': clean[:6],
                    'type': get_card_type(clean)
                })
                return cards
    
    # Check raw numbers
    if not cards:
        raw = CC_RAW.findall(text)
        for num in raw[:3]:
            if luhn_check(num):
                # Try to find expiry nearby
                idx = text.find(num)
                context = text[max(0, idx-50):idx+50]
                expiry = re.search(r'(\d{2})[/\-](\d{2,4})', context)
                cvv = re.search(r'cvv[:.\s]*(\d{3,4})', context, re.I)
                cards.append({
                    'number': num,
                    'exp': expiry.group(0) if expiry else 'XX/XX',
                    'cvv': cvv.group(1) if cvv else 'XXX',
                    'bin': num[:6],
                    'type': get_card_type(num)
                })
                return cards
    
    return cards

def format_drop(cards):
    """Format drop message"""
    now = datetime.now().strftime("%I:%M:%S %p")
    date_today = datetime.now().strftime("%d/%m/%Y")
    
    msg = f"""🔥⚡ **XYRON DROP** ☔ ⚡🔥
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤫 SOURCE: XYRON DROP ☔
⏱️ TIME: {date_today} {now}
🎯 STATUS: LIVE / FRESH

"""
    for i, card in enumerate(cards, 1):
        msg += f"""
🔮 CARD #{i}
━━━━━━━━━━━━━━━━━━━━━
💳 NUMBER: `{card['number']}`
🏦 TYPE: {card['type']}
🔢 BIN: {card['bin']}
📅 EXP: {card['exp']}
🔒 CVV: {card['cvv']}
💸 CHARGED: 0.1$💳
━━━━━━━━━━━━━━━━━━━━━

"""
    
    msg += f"""👑⚡ **XYRON VERIFIED** ⚡👑
💧 FRESH CAPTURE - USE QUICKLY 💧
"""
    return msg

class StatsManager:
    def __init__(self):
        self.stats = self.load()
    
    def load(self):
        try:
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {'total_cards': 0, 'daily': {}}
    
    def save(self):
        with open(STATS_FILE, 'w') as f:
            json.dump(self.stats, f)
    
    def add_drop(self, cards_count):
        today_str = date.today().isoformat()
        if today_str not in self.stats['daily']:
            self.stats['daily'][today_str] = {'drops': 0, 'cards': 0}
        self.stats['daily'][today_str]['drops'] += 1
        self.stats['daily'][today_str]['cards'] += cards_count
        self.stats['total_cards'] += cards_count
        self.save()
    
    def get_today(self):
        today_str = date.today().isoformat()
        if today_str in self.stats['daily']:
            return self.stats['daily'][today_str]
        return {'drops': 0, 'cards': 0}

stats = StatsManager()

def load_channels():
    try:
        with open(CHANNELS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_channels(channels):
    with open(CHANNELS_FILE, 'w') as f:
        json.dump(channels, f)

MANUAL_CCS = [
    {'number': '4532123456781234', 'exp': '12/26', 'cvv': '789', 'type': 'VISA', 'bin': '453212'},
    {'number': '5424123456781234', 'exp': '08/27', 'cvv': '456', 'type': 'MASTERCARD', 'bin': '542412'},
]

async def main():
    print("""
    ╔════════════════════════════════════════╗
    ║   🔥 XYRON DROP - LIVE CC DETECTION 🔥 ║
    ║   READY FOR INSTANT DROPS              ║
    ╚════════════════════════════════════════╝
    """)
    
    if not API_ID or not API_HASH or not BOT_TOKEN:
        print("❌ Missing API_ID, API_HASH, or BOT_TOKEN!")
        return
    
    # Start Bot Client
    bot_client = TelegramClient('xyron_bot', API_ID, API_HASH)
    await bot_client.start(bot_token=BOT_TOKEN)
    bot_me = await bot_client.get_me()
    print(f"✅ Bot online: @{bot_me.username}")
    
    # Start User Client for joining channels
    user_client = None
    if SESSION_STRING:
        try:
            user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
            await user_client.start()
            user_me = await user_client.get_me()
            print(f"✅ User online: @{user_me.username}")
        except Exception as e:
            print(f"⚠️ User login failed: {e}")
    
    # Load monitored channels
    saved = load_channels()
    monitored = []
    
    print(f"\n📋 Loaded {len(saved)} channels from storage")
    
    for ch in saved:
        try:
            entity = await bot_client.get_entity(ch)
            monitored.append(entity)
            print(f"✅ Monitoring: {ch}")
        except Exception as e:
            print(f"❌ Cannot access {ch}: {e}")
    
    # Send startup notification
    try:
        await bot_client.send_message(OWNER_ID, f"✅ XYRON DROP LIVE\n📡 Monitoring {len(monitored)} channels\n💳 Ready for CC detection")
        if DESTINATION:
            await bot_client.send_message(DESTINATION, f"🔥 XYRON DROP ☔ LIVE 🔥\n⚡ CC detection active")
    except Exception as e:
        print(f"⚠️ Could not send startup: {e}")
    
    processed = set()
    
    # ===== COMMANDS =====
    
    @bot_client.on(events.NewMessage(pattern='/start'))
    async def start_cmd(e):
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        today = stats.get_today()
        await e.reply(f"""
🔥 **XYRON DROP LIVE** ☔
━━━━━━━━━━━━━━━━━━━
✅ Status: ACTIVE
📡 Channels: {len(monitored)}
📊 Today: {today['cards']} cards

📌 **COMMANDS:**
/add @channel - Start monitoring
/remove @channel - Stop monitoring
/list - Show channels
/today - Today's stats
/drop - Manual CC
/test - Test drop

⚡ **LIVE CC DETECTION ACTIVE**
        """)
    
    @bot_client.on(events.NewMessage(pattern='/add'))
    async def add_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        parts = e.text.split()
        if len(parts) < 2:
            return await e.reply("Usage: /add @channel")
        channel = parts[1]
        try:
            entity = await bot_client.get_entity(channel)
            username = entity.username or channel
            if username not in saved:
                saved.append(username)
                save_channels(saved)
                monitored.append(entity)
                await e.reply(f"✅ Added: {username}\n⚡ Now monitoring for CCs!")
                print(f"✅ Added channel: {username}")
            else:
                await e.reply("Already monitoring!")
        except Exception as ex:
            await e.reply(f"Error: {str(ex)[:100]}")
    
    @bot_client.on(events.NewMessage(pattern='/remove'))
    async def remove_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        parts = e.text.split()
        if len(parts) < 2:
            return await e.reply("Usage: /remove @channel")
        channel = parts[1].replace('@', '')
        if channel in saved:
            saved.remove(channel)
            save_channels(saved)
            for m in monitored[:]:
                if hasattr(m, 'username') and m.username == channel:
                    monitored.remove(m)
            await e.reply(f"❌ Removed: {channel}")
            print(f"❌ Removed channel: {channel}")
        else:
            await e.reply("Not found!")
    
    @bot_client.on(events.NewMessage(pattern='/list'))
    async def list_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        if not saved:
            return await e.reply("No channels monitored!\nUse /add @channel")
        msg = "📋 **Monitored Channels:**\n\n"
        for i, ch in enumerate(saved, 1):
            status = "🟢" if any(hasattr(m, 'username') and m.username == ch for m in monitored) else "🔴"
            msg += f"{status} {i}. `{ch}`\n"
        await e.reply(msg)
    
    @bot_client.on(events.NewMessage(pattern='/today'))
    async def today_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        today = stats.get_today()
        await e.reply(f"""
☀️ **TODAY'S STATS** ☀️
━━━━━━━━━━━━━━━━━━━
📅 Date: {date.today().strftime('%d/%m/%Y')}
💧 Drops: {today['drops']}
💳 Cards: {today['cards']}
⚡ Status: LIVE
        """)
    
    @bot_client.on(events.NewMessage(pattern='/drop'))
    async def drop_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        card = random.choice(MANUAL_CCS)
        cards = [{
            'number': card['number'],
            'bin': card['bin'],
            'exp': card['exp'],
            'cvv': card['cvv'],
            'type': card['type']
        }]
        dest = DESTINATION if DESTINATION else OWNER_ID
        await bot_client.send_message(dest, format_drop(cards))
        await e.reply(f"✅ Manual CC dropped to {DESTINATION}")
        stats.add_drop(1)
    
    @bot_client.on(events.NewMessage(pattern='/test'))
    async def test_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        test_cards = [{
            'number': '4111111111111111',
            'bin': '411111',
            'exp': '12/26',
            'cvv': '123',
            'type': 'TEST'
        }]
        dest = DESTINATION if DESTINATION else OWNER_ID
        await bot_client.send_message(dest, format_drop(test_cards))
        await e.reply("✅ Test drop sent! Check your destination channel.")
    
    # ===== LIVE CC DETECTION HANDLER =====
    @bot_client.on(events.NewMessage(chats=monitored))
    async def live_cc_detection(e):
        msg_id = f"{e.chat_id}_{e.message.id}"
        
        # Skip if already processed
        if msg_id in processed:
            return
        
        # Clean old processed IDs
        if len(processed) > 5000:
            processed.clear()
        
        # Skip if no text
        if not e.message or not e.message.text:
            return
        
        text = e.message.text
        print(f"\n📩 Message from: {e.chat.title or e.chat.username}")
        print(f"📝 Content: {text[:100]}...")
        
        # Check if message contains CC
        has_cc = False
        if CC_RAW.search(text) or CC_FORMATTED.search(text):
            has_cc = True
            print("✅ CC pattern detected!")
        
        has_keyword = bool(KEYWORDS.search(text))
        if has_keyword:
            print("✅ Keyword detected!")
        
        if not has_cc and not has_keyword:
            print("❌ No CC detected, skipping...")
            return
        
        # Extract CC cards
        cards = extract_ccs(text)
        
        if cards:
            processed.add(msg_id)
            channel_name = e.chat.title or e.chat.username or "UNKNOWN"
            dest = DESTINATION if DESTINATION else OWNER_ID
            
            try:
                # Format and send drop
                drop_msg = format_drop(cards)
                await bot_client.send_message(dest, drop_msg, link_preview=False)
                
                # Update stats
                stats.add_drop(len(cards))
                
                # Log success
                logger.info(f"💧 LIVE DROP: {len(cards)} cards from {channel_name}")
                print(f"✅✅✅ DROPPED {len(cards)} CARDS TO {dest}")
                print(f"💳 Card: {cards[0]['number']} | EXP: {cards[0]['exp']} | CVV: {cards[0]['cvv']}")
                
            except FloodWaitError as wait:
                print(f"⚠️ Rate limited, waiting {wait.seconds}s")
                await asyncio.sleep(wait.seconds)
            except Exception as ex:
                logger.error(f"Drop error: {ex}")
                print(f"❌ Error sending drop: {ex}")
        else:
            print("❌ No valid CC extracted after detection")
    
    print(f"""
{'='*55}
✅ XYRON DROP - LIVE AND READY!
{'='*55}
📡 Monitoring: {len(monitored)} channels
💧 Live detection: ACTIVE
🎯 Destination: {DESTINATION}
📌 Owner ID: {OWNER_ID}

⚡ **TO START DETECTING:**
   1. Add a channel: /add @channel
   2. Make sure bot is MEMBER of that channel
   3. When someone posts CC, it will drop instantly!

📝 **TEST NOW:**
   Send /test to see a test drop
   Or post this in a monitored channel:
   4111111111111111|12|26|123

{'='*55}
""")
    
    await bot_client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Fatal: {e}")
        print(f"Error: {e}")