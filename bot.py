"""
XYRON DROPS 💧 – REAL‑TIME CC SCRAPER
Commands: /status, /testcc, /add, /remove, /list, /stats, /today, /drop, /test
"""

import asyncio
import os
import re
import json
import logging
import random
from datetime import datetime, date

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, ChatWriteForbiddenError
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest

# ===== CONFIGURATION (Railway Variables) =====
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

# ===== EMOJIS =====
E = {
    "fire": "🔥", "bolt": "⚡", "crown": "👑", "diamond": "💎",
    "drop": "💧", "alert": "🚨", "target": "🎯", "time": "⏱️",
    "check": "✅", "neon": "🔮", "crystal": "💎", "laser": "🔫",
    "shield": "🛡️", "money": "💰", "charged": "💸", "hidden": "🫥",
    "card": "💳", "lock": "🔒", "calendar": "📅", "glow": "✨",
    "ninja": "🥷", "skull": "💀", "satellite": "🛸", "rocket": "🚀",
    "add": "➕", "remove": "❌", "list": "📋", "stats": "📊",
    "today": "☀️", "rain": "☔", "warning": "⚠️", "join": "🔗",
    "settings": "⚙️", "info": "ℹ️", "power": "🔋", "status": "📡",
    "incoming": "📩", "outgoing": "📤"
}

# ===== ULTRA BROAD CC DETECTION PATTERNS (any format) =====
CC_PATTERNS = [
    r'\b\d{16}\b',                                    # 4111111111111111
    r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',      # 4111 1111 1111 1111
    r'(\d{13,16})[|\s/:-](\d{1,2})[|\s/:-](\d{2,4})[|\s/:-](\d{3,4})',  # 4111111111111111|12|26|123
    r'(\d{4}\s?\d{4}\s?\d{4}\s?\d{4})\s*[|/-]\s*(\d{2}/\d{2,4})\s*[|/-]\s*(\d{3,4})',
    r'\b\d{4}\s+\d{4}\s+\d{4}\s+\d{4}\s+\d{2}/\d{2,4}\s+\d{3,4}\b',  # space separated with expiry
    r'\b\d{4}-\d{4}-\d{4}-\d{4}\b',                  # 4111-1111-1111-1111
]

KEYWORDS = re.compile(r'\b(?:cc|card|credit|visa|mastercard|amex|cvv|valid|fresh|drop|bin|stripe|charge|payment)\b', re.I)

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
    """Extract CC from any format – returns first valid card found"""
    cards = []
    # Try all patterns
    for pattern in CC_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                # Pattern with groups (number, expiry, cvv)
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
            else:
                clean = re.sub(r'[\s\-|]', '', match)
                if luhn_check(clean):
                    # Try to find expiry and CVV nearby
                    idx = text.find(match)
                    context = text[max(0, idx-100):idx+100]
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
    return cards

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
💧 FRESH CAPTURE - USE QUICKLY 💧"""
    return msg

# ===== STATS MANAGER =====
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
]

# ===== MAIN BOT =====
async def main():
    print("""
    ╔════════════════════════════════════════════════════╗
    ║   🔥 XYRON DROPS 💧 v9.0 – LIVE CC MONITOR       ║
    ║   ✅ /status – check if bot receives messages     ║
    ║   ✅ Detects ANY CC format instantly              ║
    ╚════════════════════════════════════════════════════╝
    """)

    if not API_ID or not API_HASH or not SESSION_STRING:
        logger.error("Missing API_ID, API_HASH or SESSION_STRING")
        return

    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()
    me = await client.get_me()
    logger.info(f"✅ Logged in as: {me.first_name} (@{me.username})")

    # Load source groups
    saved = load_channels()
    if saved:
        sources_to_monitor = saved
    else:
        sources_to_monitor = [g.strip() for g in SOURCE_GROUPS if g.strip()]

    sources = []
    for group in sources_to_monitor:
        try:
            entity = await client.get_entity(group)
            sources.append(entity)
            logger.info(f"✅ Monitoring: {group}")
        except Exception as e:
            logger.error(f"❌ Cannot access {group}: {e}")

    if not sources:
        logger.error("No source groups. Add via /add or SOURCE_GROUPS env var.")
        return

    # Destination
    try:
        dest_entity = await client.get_entity(DESTINATION)
        logger.info(f"✅ Destination: {DESTINATION}")
        # Test write permission
        await client.send_message(dest_entity, f"{E['check']} XYRON DROPS 💧 online – monitoring {len(sources)} groups")
    except Exception as e:
        logger.error(f"❌ Destination error: {e}")
        return

    if not saved and sources_to_monitor:
        save_channels(sources_to_monitor)

    processed = set()

    # ===== COMMANDS =====

    @client.on(events.NewMessage(pattern='/status'))
    async def status_cmd(e):
        """Shows live receiving status + last message info"""
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        status_msg = f"""
{E['status']} **LIVE MONITORING STATUS** {E['status']}
━━━━━━━━━━━━━━━━━━━━━━━━━
{E['satellite']} Groups monitored: `{len(sources)}`
{E['incoming']} Messages received today: `{stats.get_today()['drops']}`
{E['card']} CCs detected today: `{stats.get_today()['cards']}`
{E['check']} Bot connection: `ACTIVE`

📌 **If you see this, bot is alive.**
👉 To test CC detection, send:
   `/testcc 4111111111111111|12|26|123`
👉 Or post any CC in a monitored group.
        """
        await e.reply(status_msg)

    @client.on(events.NewMessage(pattern='/testcc'))
    async def testcc_cmd(e):
        """Simulate a CC detection – for testing without waiting"""
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        parts = e.text.split(maxsplit=1)
        if len(parts) < 2:
            # Use default test card
            test_text = "4111111111111111|12|26|123"
        else:
            test_text = parts[1]
        cards = extract_ccs(test_text)
        if cards:
            await client.send_message(dest_entity, format_drop_simple(cards))
            await e.reply(f"{E['check']} Test CC forwarded! Check {DESTINATION}")
            stats.add_drop(len(cards))
        else:
            await e.reply(f"{E['warning']} Could not extract valid CC from `{test_text}`")

    @client.on(events.NewMessage(pattern='/add'))
    async def add_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        parts = e.text.split()
        if len(parts) < 2:
            return await e.reply("Usage: /add @channel")
        ch = parts[1]
        try:
            entity = await client.get_entity(ch)
            username = entity.username or ch
            if username not in sources_to_monitor:
                sources_to_monitor.append(username)
                save_channels(sources_to_monitor)
                sources.append(entity)
                await e.reply(f"{E['add']} Added: `{username}`")
                await client.send_message(dest_entity, f"{E['add']} New source: `{username}`")
            else:
                await e.reply("Already monitoring!")
        except Exception as ex:
            await e.reply(f"Error: {str(ex)[:100]}")

    @client.on(events.NewMessage(pattern='/remove'))
    async def remove_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        parts = e.text.split()
        if len(parts) < 2:
            return await e.reply("Usage: /remove @channel")
        ch = parts[1].replace('@', '')
        if ch in sources_to_monitor:
            sources_to_monitor.remove(ch)
            save_channels(sources_to_monitor)
            for s in sources[:]:
                if hasattr(s, 'username') and s.username == ch:
                    sources.remove(s)
            await e.reply(f"{E['remove']} Removed: `{ch}`")
            await client.send_message(dest_entity, f"{E['remove']} Source removed: `{ch}`")
        else:
            await e.reply("Not found!")

    @client.on(events.NewMessage(pattern='/list'))
    async def list_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        if not sources_to_monitor:
            return await e.reply("No sources monitored!")
        msg = f"{E['list']} **SOURCES**\n━━━━━━━━━━━━━━━━━━━\n"
        for i, ch in enumerate(sources_to_monitor, 1):
            status = "🟢" if any(hasattr(s, 'username') and s.username == ch for s in sources) else "🔴"
            msg += f"{status} {i}. `{ch}`\n"
        await e.reply(msg)

    @client.on(events.NewMessage(pattern='/stats'))
    async def stats_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        total = stats.get_total()
        await e.reply(f"""
{E['stats']} **XYRON STATISTICS** {E['stats']}
━━━━━━━━━━━━━━━━━━━━━━━━━
{E['crystal']} Total Cards: `{total['cards']}`
{E['drop']} Total Drops: `{total['drops']}`
{E['satellite']} Active Sources: `{len(sources)}`
{E['check']} Status: `LIVE`
        """)

    @client.on(events.NewMessage(pattern='/today'))
    async def today_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        today = stats.get_today()
        await e.reply(f"""
{E['today']} **TODAY'S STATS** {E['today']}
━━━━━━━━━━━━━━━━━━━━━━━━━
{E['calendar']} Date: `{date.today().strftime('%d/%m/%Y')}`
{E['drop']} Drops: `{today['drops']}`
{E['card']} Cards: `{today['cards']}`
{E['charged']} Charged: `${today['cards'] * 0.1:.1f}`
        """)

    @client.on(events.NewMessage(pattern='/drop'))
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
        await client.send_message(dest_entity, format_drop_simple(cards))
        await e.reply(f"{E['drop']} Manual drop sent!")
        stats.add_drop(1)

    @client.on(events.NewMessage(pattern='/test'))
    async def test_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        test_cards = [{'number': '4111111111111111', 'bin': '411111', 'exp': '12/26', 'cvv': '123', 'type': 'TEST'}]
        await client.send_message(dest_entity, format_drop_simple(test_cards))
        await e.reply("✅ Test drop sent!")

    # ===== MAIN EVENT HANDLER – INSTANT CC DETECTION =====
    @client.on(events.NewMessage(chats=sources))
    async def instant_forward(event):
        msg_id = f"{event.chat_id}_{event.message.id}"
        if msg_id in processed:
            return
        if len(processed) > 5000:
            processed.clear()

        text = event.message.text or ""
        if not text:
            return

        # Log every incoming message (helps debugging)
        print(f"\n📩 [{event.chat.title}] {text[:100]}...")

        # Quick detection
        has_pattern = any(re.search(p, text, re.I) for p in CC_PATTERNS[:2])
        has_keyword = bool(KEYWORDS.search(text))
        if not (has_pattern or has_keyword):
            return

        cards = extract_ccs(text)
        if cards:
            processed.add(msg_id)
            try:
                await client.send_message(dest_entity, format_drop_simple(cards), link_preview=False)
                stats.add_drop(len(cards))
                logger.info(f"💧 FORWARDED {len(cards)} CC(s) from {event.chat.title}")
                print(f"✅ FORWARDED {len(cards)} CC(s) → {DESTINATION}")
            except Exception as e:
                logger.error(f"Forward error: {e}")

    print(f"""
{'='*55}
✅ XYRON DROPS 💧 – FULLY ACTIVE
{'='*55}
📡 Monitoring: {len(sources)} groups
🫥 Source: HIDDEN (XYRON DROPS 💧)
🎯 Destination: {DESTINATION}
⚡ Detection: ANY CC FORMAT

📌 **COMMANDS:**
   /status   – Check if bot is receiving messages
   /testcc [card] – Simulate CC detection
   /add @channel   – Add source
   /remove @channel – Remove source
   /list – Show sources
   /stats – Total statistics
   /today – Today's drops
   /drop – Manual CC drop
   /test – Basic test drop

{E['alert']} **READY – POST A CC IN ANY MONITORED GROUP!**
{'='*55}
""")

    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())