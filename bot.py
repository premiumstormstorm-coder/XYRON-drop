```python
"""
XYRON DROP - ULTIMATE VERSION
🔥 Source Hidden | Instant Drop | All CC Formats
✅ VALID PASSED → CHARGED 0.1$💳
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

# ===== PREMIUM EMOJIS =====
E = {
    "fire": "🔥", "bolt": "⚡", "crown": "👑", "diamond": "💎",
    "glow": "✨", "ninja": "🥷", "skull": "💀", "shield": "🛡️",
    "drop": "💧", "alert": "🚨", "target": "🎯", "time": "⏱️",
    "add": "➕", "remove": "❌", "list": "📋", "check": "✅",
    "warning": "⚠️", "neon": "🔮", "cyber": "💠", "quantum": "⚛️",
    "galaxy": "🌌", "crystal": "💎", "laser": "🔫", "satellite": "🛸",
    "dragon": "🐉", "lightning": "⚡", "join": "🔗", "stats": "📊",
    "today": "☀️", "rain": "☔", "calendar": "📅", "rocket": "🚀",
    "card": "💳", "lock": "🔒", "hidden": "🤫", "ghost": "👻",
    "money": "💰", "charged": "💸"
}

# ===== ALL CC FORMATS (COMPREHENSIVE) =====
CC_PATTERNS = [
    # Format: 4111111111111111
    r'\b\d{16}\b',
    
    # Format: 4111 1111 1111 1111
    r'\b\d{4} \d{4} \d{4} \d{4}\b',
    
    # Format: 4111-1111-1111-1111
    r'\b\d{4}-\d{4}-\d{4}-\d{4}\b',
    
    # Format: 4111|1111|1111|1111
    r'\b\d{4}\|\d{4}\|\d{4}\|\d{4}\b',
    
    # Format: 4111111111111111|12|26|123
    r'(\d{13,16})[|\s/:-](\d{1,2})[|\s/:-](\d{2,4})[|\s/:-](\d{3,4})',
    
    # Format: 4111 1111 1111 1111 | 12/26 | 123
    r'(\d{4}\s?\d{4}\s?\d{4}\s?\d{4})\s*[|\s]\s*(\d{2}[/\-]\d{2,4})\s*[|\s]\s*(\d{3,4})',
    
    # Format: CC: 4111111111111111 Exp: 12/26 CVV: 123
    r'[Cc][Cc]:?\s*(\d{13,16}).*?[Ee]xp:?\s*(\d{2}[/\-]\d{2,4}).*?[Cc][Vv][Vv]:?\s*(\d{3,4})',
    
    # Format: 4111111111111111 12/26 123
    r'(\d{13,16})\s+(\d{2}/\d{2,4})\s+(\d{3,4})',
]

KEYWORDS = ['cc', 'card', 'credit', 'visa', 'mastercard', 'amex', 'discover', 'cvv', 'drop', 'valid', 'fresh', 'live', 'bin', 'cc:', 'card:']

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
    else:
        return "CARD"

def extract_ccs(text):
    """Extract CC from ANY format"""
    cards = []
    text_lower = text.lower()
    
    # Pattern 1: Standard with separator
    matches = re.findall(CC_PATTERNS[4], text, re.IGNORECASE)
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
    
    # Pattern 2: CC: format
    if not cards:
        matches = re.findall(CC_PATTERNS[6], text, re.IGNORECASE)
        for match in matches:
            clean = re.sub(r'[\s\-|]', '', match[0])
            if luhn_check(clean):
                cards.append({
                    'number': clean,
                    'exp': match[1],
                    'cvv': match[2],
                    'bin': clean[:6],
                    'type': get_card_type(clean)
                })
    
    # Pattern 3: Simple space separated
    if not cards:
        matches = re.findall(CC_PATTERNS[7], text, re.IGNORECASE)
        for match in matches:
            clean = re.sub(r'[\s\-|]', '', match[0])
            if luhn_check(clean):
                cards.append({
                    'number': clean,
                    'exp': match[1],
                    'cvv': match[2],
                    'bin': clean[:6],
                    'type': get_card_type(clean)
                })
    
    # Pattern 4: Just numbers
    if not cards:
        numbers = re.findall(CC_PATTERNS[0], text)
        numbers += re.findall(CC_PATTERNS[1], text)
        numbers += re.findall(CC_PATTERNS[2], text)
        for num in set(numbers):
            clean = re.sub(r'[\s\-|]', '', num)
            if luhn_check(clean):
                # Try to find expiry and CVV nearby
                context = text[max(0, text.find(num)-100):text.find(num)+100]
                expiry_match = re.search(r'(\d{2})[/\-](\d{2,4})', context)
                cvv_match = re.search(r'cvv[:.\s]*(\d{3,4})', context, re.I)
                
                cards.append({
                    'number': clean,
                    'exp': expiry_match.group(0) if expiry_match else 'XX/XX',
                    'cvv': cvv_match.group(1) if cvv_match else 'XXX',
                    'bin': clean[:6],
                    'type': get_card_type(clean)
                })
    
    return cards

# ===== DROP FORMAT - SOURCE HIDDEN with CHARGED 0.1$ =====
def format_drop(cards):
    """Source hidden - shows XYRON DROP ☔ instead"""
    now = datetime.now().strftime("%I:%M:%S %p")
    date_today = datetime.now().strftime("%d/%m/%Y")
    
    msg = f"""
{E['fire']}{E['bolt']}{E['crown']} **XYRON DROP** {E['rain']} {E['crown']}{E['bolt']}{E['fire']}
{E['quantum']} *INSTANT CAPTURE* {E['quantum']}
{E['galaxy']}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{E['galaxy']}

{E['hidden']} **SOURCE:** `XYRON DROP ☔`
{E['time']} **TIME:** `{date_today} {now}`
{E['target']} **STATUS:** `FRESH / VALID`

"""
    for i, card in enumerate(cards, 1):
        msg += f"""
{E['neon']} **┌── CARD #{i}** {E['neon']}
{E['card']} **NUMBER:** `{card['number']}`
{E['crystal']} **TYPE:** `{card['type']}`
{E['laser']} **BIN:** `{card['bin']}`
{E['calendar']} **EXP:** `{card['exp']}`
{E['lock']} **CVV:** `{card['cvv']}`
{E['charged']} **CHARGED:** `0.1$💳`
{E['neon']} **└──────────────** {E['neon']}

"""
    
    msg += f"""
{E['crown']}{E['lightning']} **XYRON VERIFIED** {E['lightning']}{E['crown']}
{E['ninja']} *AUTHENTICATED • SECURE • READY* {E['ninja']}
{E['drop']} `FRESH CAPTURE - USE QUICKLY` {E['drop']}
"""
    return msg

# ===== SIMPLE DROP FORMAT (SOURCE HIDDEN) with CHARGED 0.1$ =====
def format_drop_simple(cards):
    """Simple clean format with source hidden"""
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
            return {'total_cards': 0, 'daily': {}, 'total_charged': 0}
    
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
        self.stats['total_charged'] += cards_count * 0.1
        self.save()
    
    def get_today(self):
        today_str = date.today().isoformat()
        if today_str in self.stats['daily']:
            return self.stats['daily'][today_str]
        return {'drops': 0, 'cards': 0}
    
    def get_total_charged(self):
        return self.stats.get('total_charged', 0)

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
    ║   🔥 XYRON DROP ☔ v7.0 🔥            ║
    ║   SOURCE HIDDEN | INSTANT DROP       ║
    ║   CHARGED: 0.1$ PER CARD 💳          ║
    ╚════════════════════════════════════════╝
    """)
    
    if not API_ID or not API_HASH or not BOT_TOKEN:
        print("❌ Missing credentials!")
        return
    
    # Start Bot Client
    bot_client = TelegramClient('xyron_bot', API_ID, API_HASH)
    await bot_client.start(bot_token=BOT_TOKEN)
    bot_me = await bot_client.get_me()
    print(f"✅ Bot online: @{bot_me.username}")
    
    # Start User Client
    user_client = None
    if SESSION_STRING:
        try:
            user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
            await user_client.start()
            user_me = await user_client.get_me()
            print(f"✅ User online: @{user_me.username}")
        except:
            pass
    
    # Load channels
    saved = load_channels()
    monitored = []
    
    for ch in saved:
        try:
            entity = await bot_client.get_entity(ch)
            monitored.append(entity)
            print(f"📡 Monitoring: {ch}")
        except Exception as e:
            print(f"⚠️ Cannot access {ch}: {e}")
    
    # Send startup
    try:
        await bot_client.send_message(OWNER_ID, f"✅ XYRON DROP ONLINE\n📡 Monitoring {len(monitored)} channels\n💸 Charged: 0.1$ per card")
        if DESTINATION:
            await bot_client.send_message(DESTINATION, f"🔥 **XYRON DROP** ☔ 🔥\n💸 Charged 0.1$ per valid card")
    except:
        pass
    
    processed = set()
    
    # ===== COMMANDS =====
    
    @bot_client.on(events.NewMessage(pattern='/start'))
    async def start_cmd(e):
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        await e.reply(f"""
{E['crown']} **XYRON DROP** ☔ {E['crown']}
━━━━━━━━━━━━━━━━━━━
{E['check']} Status: LIVE
{E['satellite']} Channels: {len(monitored)}
{E['today']} Today: {stats.get_today()['cards']} cards
{E['money']} Total Charged: ${stats.get_total_charged():.1f}
{E['hidden']} Source: HIDDEN

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
                await e.reply(f"✅ Added: {username}\nNow monitoring for CC!")
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
        msg = "📋 **Monitored Channels:**\n"
        for i, ch in enumerate(saved, 1):
            msg += f"{i}. `{ch}`\n"
        await e.reply(msg)
    
    @bot_client.on(events.NewMessage(pattern='/today'))
    async def today_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        today = stats.get_today()
        await e.reply(f"""
{E['today']} **TODAY'S STATS** {E['today']}
━━━━━━━━━━━━━━━━━━━
{E['calendar']} Date: {date.today().strftime('%d/%m/%Y')}
{E['drop']} Drops: {today['drops']}
{E['card']} Cards: {today['cards']}
{E['money']} Charged: ${today['cards'] * 0.1:.1f}
        """)
    
    @bot_client.on(events.NewMessage(pattern='/drop'))
    async def drop_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        
        parts = e.text.split()
        
        if len(parts) >= 2:
            custom_text = ' '.join(parts[1:])
            cards = extract_ccs(custom_text)
            if cards:
                dest = DESTINATION if DESTINATION else OWNER_ID
                await bot_client.send_message(dest, format_drop_simple(cards))
                await e.reply(f"✅ Manual drop sent with {len(cards)} cards\n💸 Charged: ${len(cards) * 0.1:.1f}")
                stats.add_drop(len(cards))
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
        await bot_client.send_message(dest, format_drop_simple(cards))
        await e.reply(f"✅ Manual CC dropped to {DESTINATION}\n💸 Charged: $0.1")
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
        await bot_client.send_message(dest, format_drop_simple(test_cards))
        await e.reply("✅ Test drop sent! (No charge for test)")
    
    # ===== INSTANT AUTO DROP =====
    @bot_client.on(events.NewMessage(chats=monitored))
    async def instant_drop(e):
        msg_id = f"{e.chat_id}_{e.message.id}"
        
        if msg_id in processed:
            return
        
        if len(processed) > 5000:
            processed.clear()
        
        if not e.message or not e.message.text:
            return
        
        text = e.message.text
        
        # Fast CC detection
        has_cc = False
        for pattern in CC_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                has_cc = True
                break
        
        has_keywords = any(k in text.lower() for k in KEYWORDS)
        
        if not has_cc and not has_keywords:
            return
        
        # Extract cards
        cards = extract_ccs(text)
        
        if cards:
            processed.add(msg_id)
            dest = DESTINATION if DESTINATION else OWNER_ID
            
            try:
                # Send simple drop with hidden source
                drop_msg = format_drop_simple(cards)
                await bot_client.send_message(dest, drop_msg, link_preview=False)
                
                # Also send fancy version
                fancy_msg = format_drop(cards)
                await bot_client.send_message(dest, fancy_msg, link_preview=False)
                
                stats.add_drop(len(cards))
                logger.info(f"💧 DROP: {len(cards)} cards | Charged: ${len(cards) * 0.1:.1f}")
                print(f"✅ DROPPED: {len(cards)} cards | CHARGED: ${len(cards) * 0.1:.1f}")
                
            except FloodWaitError as wait:
                await asyncio.sleep(wait.seconds)
            except Exception as ex:
                logger.error(f"Error: {ex}")
    
    print(f"""
{'='*55}
✅ XYRON DROP ☔ IS READY!
{'='*55}
{E['satellite']} Monitoring: {len(monitored)} channels
{E['drop']} Instant drop: ENABLED
{E['hidden']} Source: HIDDEN (XYRON DROP ☔)
{E['money']} Charge: 0.1$ per card 💳
{E['rocket']} Destination: {DESTINATION}

📌 **COMMANDS:**
   /join @channel  - Auto-join channel
   /add @channel   - Start monitoring
   /list           - Show channels
   /today          - Today's stats
   /drop           - Manual CC drop
   /test           - Test drop

{E['alert']} **READY FOR INSTANT CC DETECTION!**
{'='*55}
""")
    
    await bot_client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Fatal: {e}")
        print(f"Error: {e}")
```
