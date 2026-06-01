"""
XYRON DROPS 💧 - Real-Time CC Scraper
Source Hidden | Extra Commands | Instant Forward
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

# ===== RAILWAY ENVIRONMENT VARIABLES =====
API_ID = int(os.environ.get('API_ID', 0))
API_HASH = os.environ.get('API_HASH', '')
SESSION_STRING = os.environ.get('SESSION_STRING', '')
OWNER_ID = int(os.environ.get('OWNER_ID', 0))
SOURCE_GROUPS = os.environ.get('SOURCE_GROUPS', '').split(',')
DESTINATION = os.environ.get('DESTINATION_CHANNEL', '')

CHANNELS_FILE = 'monitored.json'
STATS_FILE = 'stats.json'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===== PREMIUM EMOJIS =====
E = {
    "fire": "🔥", "bolt": "⚡", "crown": "👑", "diamond": "💎",
    "drop": "💧", "alert": "🚨", "target": "🎯", "time": "⏱️",
    "check": "✅", "neon": "🔮", "crystal": "💎", "laser": "🔫",
    "shield": "🛡️", "money": "💰", "charged": "💸", "hidden": "🫥",
    "card": "💳", "lock": "🔒", "calendar": "📅", "glow": "✨",
    "ninja": "🥷", "skull": "💀", "satellite": "🛸", "rocket": "🚀",
    "add": "➕", "remove": "❌", "list": "📋", "stats": "📊",
    "today": "☀️", "rain": "☔", "warning": "⚠️", "join": "🔗",
    "settings": "⚙️", "info": "ℹ️", "power": "🔋"
}

# ===== CC DETECTION PATTERNS =====
CC_PATTERNS = [
    r'\b\d{16}\b',
    r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
    r'(\d{13,16})[|\s/:-](\d{1,2})[|\s/:-](\d{2,4})[|\s/:-](\d{3,4})',
    r'(\d{4}\s?\d{4}\s?\d{4}\s?\d{4})\s*[|/-]\s*(\d{2}/\d{2,4})\s*[|/-]\s*(\d{3,4})',
]

KEYWORDS = re.compile(r'\b(?:cc|card|credit|visa|mastercard|amex|cvv|valid|fresh|drop|bin)\b', re.I)

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
    cards = []
    matches = re.findall(CC_PATTERNS[2], text, re.IGNORECASE)
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
    numbers = re.findall(CC_PATTERNS[1], text)
    for num in numbers:
        clean = re.sub(r'[\s-]', '', num)
        if luhn_check(clean):
            idx = text.find(num)
            context = text[max(0, idx-50):idx+50]
            expiry = re.search(r'(\d{2})[/\-](\d{2,4})', context)
            cvv = re.search(r'cvv[:.\s]*(\d{3,4})', context, re.I)
            cards.append({
                'number': clean,
                'exp': expiry.group(0) if expiry else 'XX/XX',
                'cvv': cvv.group(1) if cvv else 'XXX',
                'bin': clean[:6],
                'type': get_card_type(clean)
            })
            return cards
    return cards

# ===== DROP FORMAT - SOURCE HIDDEN =====
def format_drop(cards):
    now = datetime.now().strftime("%I:%M:%S %p")
    date_today = datetime.now().strftime("%d/%m/%Y")
    
    msg = f"""
{E['fire']}{E['bolt']}{E['crown']} **XYRON DROPS** {E['drop']} {E['crown']}{E['bolt']}{E['fire']}
{E['glow']} *LIVE CAPTURE* {E['glow']}
{E['crystal']}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{E['crystal']}

{E['hidden']} **SOURCE:** `XYRON DROPS 💧`
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
{E['charged']} **CHARGED:** `0.1$ 💳`
{E['neon']} **└──────────────** {E['neon']}

"""
    
    msg += f"""
{E['crown']}{E['shield']} **XYRON VERIFIED** {E['shield']}{E['crown']}
{E['ninja']} *AUTHENTICATED • SECURE • READY* {E['ninja']}
{E['drop']} `FRESH CAPTURE - USE QUICKLY` {E['drop']}
{E['rocket']} **XYRON DROPS | PREMIUM EDITION** {E['rocket']}
"""
    return msg

def format_drop_simple(cards):
    now = datetime.now().strftime("%I:%M:%S %p")
    date_today = datetime.now().strftime("%d/%m/%Y")
    
    msg = f"""🔥⚡ **XYRON DROPS** 💧 ⚡🔥
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🫥 SOURCE: XYRON DROPS 💧
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
💸 CHARGED: 0.1$ 💳
━━━━━━━━━━━━━━━━━━━━━

"""
    
    msg += f"""👑🛡️ **XYRON VERIFIED** 🛡️👑
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
            return {'total_cards': 0, 'total_drops': 0, 'daily': {}}
    
    def save(self):
        with open(STATS_FILE, 'w') as f:
            json.dump(self.stats, f)
    
    def add_drop(self, cards_count):
        today_str = date.today().isoformat()
        if today_str not in self.stats['daily']:
            self.stats['daily'][today_str] = {'drops': 0, 'cards': 0}
        self.stats['daily'][today_str]['drops'] += 1
        self.stats['daily'][today_str]['cards'] += cards_count
        self.stats['total_drops'] += 1
        self.stats['total_cards'] += cards_count
        self.save()
    
    def get_today(self):
        today_str = date.today().isoformat()
        if today_str in self.stats['daily']:
            return self.stats['daily'][today_str]
        return {'drops': 0, 'cards': 0}
    
    def get_total(self):
        return {'cards': self.stats['total_cards'], 'drops': self.stats['total_drops']}

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
    {'number': '378282246310005', 'exp': '06/25', 'cvv': '1234', 'type': 'AMEX', 'bin': '378282'},
]

async def main():
    print("""
    ╔════════════════════════════════════════════════════╗
    ║   🔥 XYRON DROPS 💧 v8.0 - REAL-TIME SCRAPER 🔥   ║
    ║   SOURCE HIDDEN | EXTRA COMMANDS | INSTANT FORWARD ║
    ╚════════════════════════════════════════════════════╝
    """)
    
    if not API_ID or not API_HASH or not SESSION_STRING:
        logger.error("Missing API_ID, API_HASH or SESSION_STRING")
        return
    
    # Create client with USER account
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    
    try:
        await client.start()
        me = await client.get_me()
        logger.info(f"✅ Logged in as: {me.first_name} (@{me.username})")
        print(f"✅ Logged in as: {me.first_name} (@{me.username})")
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return
    
    # Load source groups from file or use env
    saved = load_channels()
    if saved:
        sources_to_monitor = saved
    else:
        sources_to_monitor = [g.strip() for g in SOURCE_GROUPS if g.strip()]
    
    sources = []
    print("\n📡 Loading source groups...")
    for group in sources_to_monitor:
        try:
            entity = await client.get_entity(group)
            sources.append(entity)
            logger.info(f"✅ Monitoring: {group}")
            print(f"✅ Monitoring: {group}")
        except Exception as e:
            logger.error(f"❌ Cannot access {group}: {e}")
    
    # Check destination
    try:
        dest_entity = await client.get_entity(DESTINATION)
        logger.info(f"✅ Destination: {DESTINATION}")
        print(f"✅ Destination: {DESTINATION}")
    except Exception as e:
        logger.error(f"❌ Destination error: {e}")
        return
    
    # Save channels to file
    if sources_to_monitor and not saved:
        save_channels(sources_to_monitor)
    
    # Send startup message
    await client.send_message(dest_entity, f"""
{E['fire']}{E['bolt']} **XYRON DROPS 💧 ONLINE** {E['bolt']}{E['fire']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{E['satellite']} **Monitoring:** {len(sources)} groups
{E['hidden']} **Source:** HIDDEN (XYRON DROPS 💧)
{E['drop']} **Mode:** INSTANT FORWARD
{E['check']} **Status:** ACTIVE

📌 **Commands Available:**
/add @channel - Add source group
/remove @channel - Remove source group
/list - Show monitored groups
/stats - Total statistics
/today - Today's stats
/test - Send test drop
/forward @channel - Force forward
/ping - Check bot status
    """)
    
    processed = set()
    
    # ===== EXTRA COMMANDS =====
    
    @client.on(events.NewMessage(pattern='/ping'))
    async def ping_cmd(e):
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        await e.reply(f"{E['check']} **Pong!** Bot is alive and monitoring {len(sources)} groups.")
    
    @client.on(events.NewMessage(pattern='/add'))
    async def add_cmd(e):
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        parts = e.text.split()
        if len(parts) < 2:
            return await e.reply(f"Usage: `/add @channel`")
        channel = parts[1]
        try:
            entity = await client.get_entity(channel)
            username = entity.username or channel
            if username not in sources_to_monitor:
                sources_to_monitor.append(username)
                save_channels(sources_to_monitor)
                sources.append(entity)
                await e.reply(f"{E['add']} **Added:** `{username}`\n{E['check']} Now monitoring!")
                await client.send_message(dest_entity, f"{E['add']} **New source added:** `{username}`")
            else:
                await e.reply(f"{E['warning']} Already monitoring!")
        except Exception as ex:
            await e.reply(f"{E['warning']} Error: {str(ex)[:100]}")
    
    @client.on(events.NewMessage(pattern='/remove'))
    async def remove_cmd(e):
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        parts = e.text.split()
        if len(parts) < 2:
            return await e.reply(f"Usage: `/remove @channel`")
        channel = parts[1].replace('@', '')
        if channel in sources_to_monitor:
            sources_to_monitor.remove(channel)
            save_channels(sources_to_monitor)
            for s in sources[:]:
                if hasattr(s, 'username') and s.username == channel:
                    sources.remove(s)
            await e.reply(f"{E['remove']} **Removed:** `{channel}`")
            await client.send_message(dest_entity, f"{E['remove']} **Source removed:** `{channel}`")
        else:
            await e.reply(f"{E['warning']} Not found!")
    
    @client.on(events.NewMessage(pattern='/list'))
    async def list_cmd(e):
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        if not sources_to_monitor:
            return await e.reply("No sources monitored!")
        msg = f"{E['list']} **MONITORED SOURCES**\n━━━━━━━━━━━━━━━━━━━\n"
        for i, ch in enumerate(sources_to_monitor, 1):
            status = "🟢" if any(hasattr(s, 'username') and s.username == ch for s in sources) else "🔴"
            msg += f"{status} {i}. `{ch}`\n"
        await e.reply(msg)
    
    @client.on(events.NewMessage(pattern='/stats'))
    async def stats_cmd(e):
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        total = stats.get_total()
        await e.reply(f"""
{E['stats']} **XYRON STATISTICS** {E['stats']}
━━━━━━━━━━━━━━━━━━━━━━━━━
{E['crystal']} Total Cards: `{total['cards']}`
{E['drop']} Total Drops: `{total['drops']}`
{E['satellite']} Active Sources: `{len(sources)}`
{E['check']} Status: `LIVE`
{E['rocket']} Uptime: `ACTIVE`
        """)
    
    @client.on(events.NewMessage(pattern='/today'))
    async def today_cmd(e):
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        today = stats.get_today()
        await e.reply(f"""
{E['today']} **TODAY'S STATS** {E['today']}
━━━━━━━━━━━━━━━━━━━━━━━━━
{E['calendar']} Date: `{date.today().strftime('%d/%m/%Y')}`
{E['drop']} Drops: `{today['drops']}`
{E['card']} Cards: `{today['cards']}`
{E['charged']} Charged: `${today['cards'] * 0.1:.1f}`
        """)
    
    @client.on(events.NewMessage(pattern='/test'))
    async def test_cmd(e):
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        card = random.choice(MANUAL_CCS)
        cards = [{
            'number': card['number'],
            'bin': card['bin'],
            'exp': card['exp'],
            'cvv': card['cvv'],
            'type': card['type']
        }]
        await client.send_message(dest_entity, format_drop_simple(cards))
        await e.reply(f"{E['check']} **Test drop sent!** Check {DESTINATION}")
    
    @client.on(events.NewMessage(pattern='/forward'))
    async def forward_cmd(e):
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        parts = e.text.split()
        if len(parts) < 2:
            return await e.reply(f"Usage: `/forward @channel`")
        channel = parts[1]
        try:
            entity = await client.get_entity(channel)
            # Get last 10 messages and check for CCs
            count = 0
            async for msg in client.iter_messages(entity, limit=10):
                if msg.text:
                    cards = extract_ccs(msg.text)
                    if cards:
                        await client.send_message(dest_entity, format_drop_simple(cards))
                        count += len(cards)
            await e.reply(f"{E['check']} Forwarded {count} cards from {channel}")
        except Exception as ex:
            await e.reply(f"Error: {str(ex)[:100]}")
    
    # ===== MAIN EVENT HANDLER - INSTANT FORWARD (NO DELAY) =====
    @client.on(events.NewMessage(chats=sources))
    async def instant_forward(event):
        msg_id = f"{event.chat_id}_{event.message.id}"
        
        if msg_id in processed:
            return
        
        if len(processed) > 5000:
            processed.clear()
        
        if not event.message or not event.message.text:
            return
        
        text = event.message.text
        print(f"\n📩 Message from: {event.chat.title or event.chat.username}")
        
        # Quick CC detection
        has_pattern = any(re.search(p, text, re.I) for p in CC_PATTERNS[:2])
        has_keyword = bool(KEYWORDS.search(text))
        
        if not (has_pattern or has_keyword):
            return
        
        cards = extract_ccs(text)
        
        if cards:
            processed.add(msg_id)
            try:
                # Send both formats
                await client.send_message(dest_entity, format_drop_simple(cards), link_preview=False)
                await client.send_message(dest_entity, format_drop(cards), link_preview=False)
                stats.add_drop(len(cards))
                logger.info(f"💧 FORWARDED {len(cards)} CC(s) from {event.chat.title}")
                print(f"✅✅✅ FORWARDED {len(cards)} CARDS TO DESTINATION")
            except FloodWaitError as wait:
                await asyncio.sleep(wait.seconds)
            except Exception as ex:
                logger.error(f"Forward error: {ex}")
    
    print(f"""
{'='*55}
✅ XYRON DROPS 💧 IS READY!
{'='*55}
📡 Monitoring: {len(sources)} groups
🫥 Source: HIDDEN (XYRON DROPS 💧)
🎯 Destination: {DESTINATION}
⚡ Mode: INSTANT FORWARD

📌 **EXTRA COMMANDS:**
   /add @channel    - Add source group
   /remove @channel - Remove source group
   /list            - Show monitored groups
   /stats           - Total statistics
   /today           - Today's drops
   /test            - Send test drop
   /forward @channel- Force forward recent CCs
   /ping            - Check bot status

{E['alert']} **READY FOR REAL-TIME CC DETECTION!**
{'='*55}
""")
    
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Fatal: {e}")