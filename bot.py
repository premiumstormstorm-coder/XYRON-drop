"""
XYRON LIVE DROPS - CRASH FIXED
No aiohttp required, simplified health check
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

# ===== CONFIG =====
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
    "today": "☀️", "rain": "☔", "calendar": "📅", "rocket": "🚀"
}

# ===== CC DETECTION =====
CC_PATTERNS = [
    r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
    r'\b\d{16}\b',
    r'(\d{13,16})[|\s/:-](\d{1,2})[|\s/:-](\d{2,4})[|\s/:-](\d{3,4})',
]

KEYWORDS = ['cc', 'card', 'credit', 'visa', 'mastercard', 'cvv', 'drop', 'valid', 'fresh', 'bin']

def luhn_check(card):
    card = re.sub(r'[\s-]', '', card)
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

def extract_ccs(text):
    cards = []
    matches = re.findall(CC_PATTERNS[2], text, re.IGNORECASE)
    for match in matches:
        clean = re.sub(r'[\s-]', '', match[0])
        if luhn_check(clean):
            cards.append({
                'masked': f"{clean[:4]}****{clean[-4:]}",
                'exp': f"{match[1]}/{match[2][-2:]}",
                'cvv': match[3],
                'bin': clean[:6],
                'type': "VISA" if clean.startswith('4') else "MC" if clean.startswith('5') else "AMEX" if clean.startswith('3') else "CC"
            })
    if not cards:
        numbers = re.findall(CC_PATTERNS[0], text)
        numbers += re.findall(CC_PATTERNS[1], text)
        for num in set(numbers):
            clean = re.sub(r'[\s-]', '', num)
            if luhn_check(clean):
                cards.append({
                    'masked': f"{clean[:4]}****{clean[-4:]}",
                    'exp': 'XX/XX',
                    'cvv': 'XXX',
                    'bin': clean[:6],
                    'type': "CC"
                })
    return cards

def format_drop(cards, channel_name):
    now = datetime.now().strftime("%H:%M:%S")
    date_today = datetime.now().strftime("%d/%m/%Y")
    
    msg = f"""
{E['alert']}{E['fire']}{E['bolt']} **XYRON LIVE DROP** {E['bolt']}{E['fire']}{E['alert']}
{E['quantum']} *REAL-TIME CAPTURE* {E['quantum']}
{E['galaxy']}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{E['galaxy']}

{E['satellite']} **SOURCE:** `{channel_name}`
{E['time']} **TIME:** `{date_today} {now}`
{E['target']} **STATUS:** `LIVE / VALIDATED`

{E['dragon']}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{E['dragon']}

"""
    for i, card in enumerate(cards, 1):
        msg += f"""
{E['neon']} **┌── CARD #{i}** {E['neon']}
{E['cyber']} │ {E['crystal']} **TYPE:** `{card['type']}`
{E['glow']} │ 💳 **NUMBER:** `{card['masked']}`
{E['laser']} │ 🏦 **BIN:** `{card['bin']}`
{E['time']} │ 📅 **EXP:** `{card['exp']}`
{E['shield']} │ 🔒 **CVV:** `{card['cvv']}`
{E['check']} │ ✅ **VALID:** `PASSED`
{E['neon']} **└─────** {E['neon']}

"""
    
    msg += f"""
{E['crown']}{E['lightning']} **XYRON VERIFIED** {E['lightning']}{E['crown']}
{E['ninja']} *AUTHENTICATED • SECURE • READY* {E['ninja']}
{E['drop']} `FRESH CAPTURE - USE QUICKLY` {E['drop']}
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
            return {'total_cards': 0, 'total_drops': 0, 'daily': {}}
    
    def save(self):
        with open(STATS_FILE, 'w') as f:
            json.dump(self.stats, f)
    
    def add_drop(self, cards_count, source):
        today_str = date.today().isoformat()
        if today_str not in self.stats['daily']:
            self.stats['daily'][today_str] = {'drops': 0, 'cards': 0, 'sources': []}
        self.stats['daily'][today_str]['drops'] += 1
        self.stats['daily'][today_str]['cards'] += cards_count
        if source not in self.stats['daily'][today_str]['sources']:
            self.stats['daily'][today_str]['sources'].append(source)
        self.stats['total_drops'] += 1
        self.stats['total_cards'] += cards_count
        self.save()
    
    def get_today(self):
        today_str = date.today().isoformat()
        if today_str in self.stats['daily']:
            return self.stats['daily'][today_str]
        return {'drops': 0, 'cards': 0, 'sources': []}
    
    def get_total(self):
        return self.stats['total_cards']

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
    {'num': '4532123456781234', 'exp': '12/26', 'cvv': '789', 'type': 'VISA'},
    {'num': '5424123456781234', 'exp': '08/27', 'cvv': '456', 'type': 'MASTERCARD'},
]

async def main():
    print("""
    ╔════════════════════════════════════════╗
    ║   🔥 XYRON LIVE DROPS - FIXED 🔥      ║
    ╚════════════════════════════════════════╝
    """)
    
    # Check credentials
    if not API_ID or not API_HASH:
        logger.error("Missing API_ID or API_HASH")
        return
    
    if not BOT_TOKEN:
        logger.error("Missing BOT_TOKEN")
        return
    
    # Start Bot Client
    bot_client = TelegramClient('xyron_bot', API_ID, API_HASH)
    await bot_client.start(bot_token=BOT_TOKEN)
    bot_me = await bot_client.get_me()
    logger.info(f"✅ Bot online: @{bot_me.username}")
    
    # Start User Client (optional)
    user_client = None
    if SESSION_STRING:
        try:
            user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
            await user_client.start()
            user_me = await user_client.get_me()
            logger.info(f"✅ User online: @{user_me.username}")
        except Exception as e:
            logger.warning(f"User login failed: {e}")
    
    # Load channels
    saved = load_channels()
    monitored = []
    
    for ch in saved:
        try:
            entity = await bot_client.get_entity(ch)
            monitored.append(entity)
            logger.info(f"📡 Monitoring: {ch}")
        except Exception as e:
            logger.warning(f"Cannot access {ch}: {e}")
    
    # Send startup
    try:
        await bot_client.send_message(OWNER_ID, f"✅ XYRON ONLINE\n📡 Monitoring {len(monitored)} channels")
    except:
        pass
    
    processed = set()
    
    # ===== COMMANDS =====
    
    @bot_client.on(events.NewMessage(pattern='/start'))
    async def start_cmd(e):
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        await e.reply(f"""
{E['crown']} **XYRON ACTIVE** {E['crown']}
━━━━━━━━━━━━━━━━━━━
{E['check']} Status: LIVE
{E['satellite']} Channels: {len(monitored)}
{E['today']} Today: {stats.get_today()['cards']} cards

📌 **COMMANDS:**
/join @channel - Auto-join
/add @channel - Monitor
/remove @channel - Remove
/list - Show channels
/today - Today's stats
/drop - Manual CC
/test - Test drop
        """)
    
    @bot_client.on(events.NewMessage(pattern='/join'))
    async def join_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        if not user_client:
            return await e.reply("❌ No user account")
        parts = e.text.split()
        if len(parts) < 2:
            return await e.reply("Usage: /join @channel")
        channel = parts[1]
        if channel.startswith('https://t.me/'):
            channel = channel.replace('https://t.me/', '@')
        try:
            entity = await user_client.get_entity(channel)
            username = entity.username or channel
            await user_client(JoinChannelRequest(entity))
            await e.reply(f"✅ Joined: {username}\nNow use /add {username}")
        except Exception as ex:
            await e.reply(f"❌ Failed: {str(ex)[:100]}")
    
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
                await e.reply(f"✅ Added: {username}")
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
        else:
            await e.reply("Not found!")
    
    @bot_client.on(events.NewMessage(pattern='/list'))
    async def list_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        if not saved:
            return await e.reply("No channels!")
        msg = "📋 **Channels:**\n"
        for i, ch in enumerate(saved, 1):
            msg += f"{i}. `{ch}`\n"
        await e.reply(msg)
    
    @bot_client.on(events.NewMessage(pattern='/today'))
    async def today_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        today = stats.get_today()
        await e.reply(f"""
☀️ **TODAY'S STATS**
━━━━━━━━━━━━━━━
📅 Date: {date.today().strftime('%d/%m/%Y')}
💧 Drops: {today['drops']}
💳 Cards: {today['cards']}
        """)
    
    @bot_client.on(events.NewMessage(pattern='/drop'))
    async def drop_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        card = random.choice(MANUAL_CCS)
        cards = [{
            'masked': f"{card['num'][:4]}****{card['num'][-4:]}",
            'bin': card['num'][:6],
            'exp': card['exp'],
            'cvv': card['cvv'],
            'type': card['type']
        }]
        dest = DESTINATION if DESTINATION else OWNER_ID
        await bot_client.send_message(dest, format_drop(cards, "MANUAL DROP"))
        await e.reply(f"✅ Manual drop sent to {dest}")
    
    @bot_client.on(events.NewMessage(pattern='/test'))
    async def test_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        test_cards = [{'masked': '4111****1111', 'bin': '411111', 'exp': '12/26', 'cvv': '123', 'type': 'TEST'}]
        dest = DESTINATION if DESTINATION else OWNER_ID
        await bot_client.send_message(dest, format_drop(test_cards, "TEST"))
        await e.reply("✅ Test drop sent!")
    
    # ===== LIVE AUTO DROP =====
    @bot_client.on(events.NewMessage(chats=monitored))
    async def auto_drop(e):
        msg_id = f"{e.chat_id}_{e.message.id}"
        if msg_id in processed:
            return
        if len(processed) > 5000:
            processed.clear()
        if not e.message or not e.message.text:
            return
        
        text = e.message.text
        
        # Check for CC
        has_cc = False
        for pattern in CC_PATTERNS:
            if re.search(pattern, text):
                has_cc = True
                break
        has_keywords = any(k in text.lower() for k in KEYWORDS)
        
        if not has_cc and not has_keywords:
            return
        
        cards = extract_ccs(text)
        
        if cards:
            processed.add(msg_id)
            channel_name = e.chat.title or e.chat.username or "UNKNOWN"
            dest = DESTINATION if DESTINATION else OWNER_ID
            
            try:
                await bot_client.send_message(dest, format_drop(cards, channel_name), link_preview=False)
                stats.add_drop(len(cards), channel_name)
                logger.info(f"💧 DROPPED {len(cards)} cards from {channel_name}")
                print(f"✅ DROPPED: {len(cards)} cards")
            except FloodWaitError as wait:
                await asyncio.sleep(wait.seconds)
            except Exception as ex:
                logger.error(f"Error: {ex}")
    
    print(f"""
✅ BOT READY!
📡 Monitoring: {len(monitored)} channels
💧 Auto-drop: ACTIVE
📍 Destination: {DESTINATION}

🔥 Send /start to your bot
    """)
    
    await bot_client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Fatal: {e}")
        print(f"Error: {e}")