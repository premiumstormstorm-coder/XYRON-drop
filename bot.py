"""
XYRON DROP ☔ – ULTIMATE EXTRACTOR (now handles multi-line Exp Date / CVV2)
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

# ===== RAILWAY ENVIRONMENT =====
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
    """Extract CC, expiry, CVV from any format – now handles multi-line labeled entries."""
    # 1. Multi-line with "Exp Date" and "CVV2" labels
    pattern = re.compile(
        r'(\d{13,16})\s*\n\s*Exp\s*Date\s*\n\s*(\d{2}/\d{2,4})\s*\n\s*CVV2?\s*\n\s*(\d{3,4})',
        re.IGNORECASE | re.MULTILINE
    )
    m = pattern.search(text)
    if m:
        cc = m.group(1)
        if luhn_check(cc):
            return [{
                'number': cc,
                'exp': m.group(2),
                'cvv': m.group(3),
                'bin': cc[:6],
                'type': get_card_type(cc)
            }]

    # 2. Standard pipe: 5446147525910816|07|27|364
    m = re.search(r'(\d{13,16})\s*[|]\s*(\d{1,2})\s*[|]\s*(\d{2,4})\s*[|]\s*(\d{3,4})', text, re.I)
    if m:
        cc = re.sub(r'[\s\-|]', '', m.group(1))
        if luhn_check(cc):
            return [{'number': cc, 'exp': f"{m.group(2)}/{m.group(3)}", 'cvv': m.group(4), 'bin': cc[:6], 'type': get_card_type(cc)}]

    # 3. Pipe with slash: 5193458202434359|07/26|591
    m = re.search(r'(\d{13,16})\s*[|]\s*(\d{2}/\d{2,4})\s*[|]\s*(\d{3,4})', text, re.I)
    if m:
        cc = re.sub(r'[\s\-|]', '', m.group(1))
        if luhn_check(cc):
            return [{'number': cc, 'exp': m.group(2), 'cvv': m.group(3), 'bin': cc[:6], 'type': get_card_type(cc)}]

    # 4. Space separated: card + MMyy + cvv  (e.g., 4867960043082121 1129 358)
    m = re.search(r'(\d{13,16})\s+(\d{4})\s+(\d{3,4})', text)
    if m:
        cc = m.group(1)
        if luhn_check(cc):
            month = m.group(2)[:2]
            year = m.group(2)[2:]
            exp = f"{month}/{year}"
            return [{'number': cc, 'exp': exp, 'cvv': m.group(3), 'bin': cc[:6], 'type': get_card_type(cc)}]

    # 5. Space separated: card + MM/YY + cvv
    m = re.search(r'(\d{13,16})\s+(\d{2}/\d{2,4})\s+(\d{3,4})', text)
    if m:
        cc = m.group(1)
        if luhn_check(cc):
            return [{'number': cc, 'exp': m.group(2), 'cvv': m.group(3), 'bin': cc[:6], 'type': get_card_type(cc)}]

    # 6. Space separated: card + MM + YY + cvv
    m = re.search(r'(\d{13,16})\s+(\d{2})\s+(\d{2,4})\s+(\d{3,4})', text)
    if m:
        cc = m.group(1)
        if luhn_check(cc):
            exp = f"{m.group(2)}/{m.group(3)}"
            return [{'number': cc, 'exp': exp, 'cvv': m.group(4), 'bin': cc[:6], 'type': get_card_type(cc)}]

    # 7. Card + CVV only (space)
    m = re.search(r'(\d{13,16})\s+(\d{3,4})', text)
    if m:
        cc = m.group(1)
        if luhn_check(cc):
            return [{'number': cc, 'exp': 'N/A', 'cvv': m.group(2), 'bin': cc[:6], 'type': get_card_type(cc)}]

    # 8. Just the card number
    m = re.search(r'\b\d{13,16}\b', text)
    if m:
        cc = m.group(0)
        if luhn_check(cc):
            return [{'number': cc, 'exp': 'N/A', 'cvv': 'N/A', 'bin': cc[:6], 'type': get_card_type(cc)}]

    return []

def format_styled_drop(cards):
    card = cards[0]
    now = datetime.now().strftime("%I:%M:%S %p")
    date_today = datetime.now().strftime("%d/%m/%Y")
    arrow = "⇾"
    msg = f"🔥 **XYRON DROP** ☔ 🔥\n\n"
    msg += f"𝘾𝘼𝙍𝘿 {arrow} {card['number']}\n"
    msg += f"𝙀𝙓𝙋 {arrow} {card['exp']}\n"
    msg += f"𝘾𝙑𝙑 {arrow} {card['cvv']}\n"
    msg += f"𝙎𝙏𝘼𝙏𝙐𝙎 {arrow} 𝘈𝘱𝘱𝘳𝘖𝘝𝘌𝘋 💎\n"
    msg += f"𝙈𝙀𝙎𝙎𝘼𝙂𝙀 {arrow} 𝘚𝘊𝘙𝘈𝘗𝘗𝘌𝘋\n"
    msg += f"𝙂𝘼𝙏𝙀𝙒𝘼𝙔 {arrow} 𝘟𝘠𝘙𝘖𝘕 𝘋𝘙𝘖𝘗 ☔\n"
    msg += f"𝙄𝙉𝙁𝙊 {arrow} {card['type']} - CREDIT\n"
    msg += f"𝘽𝘼𝙉𝙆 {arrow} {card['type']} INTERNATIONAL\n"
    msg += f"𝘾𝙊𝙐𝙉𝙏𝙍𝙔 {arrow} 🌍\n"
    msg += f"\n🛡️ **XYRON VERIFIED** 💧\n"
    msg += f"⏱️ {date_today} {now}"
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

async def main():
    print("\n🔥 XYRON DROP ☔ – MULTI-LINE SUPPORT ADDED 🔥\n")

    if not API_ID or not API_HASH or not SESSION_STRING:
        logger.error("Missing API_ID, API_HASH or SESSION_STRING")
        return

    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()
    me = await client.get_me()
    logger.info(f"✅ Logged in as: {me.first_name} (@{me.username})")

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
        logger.error("No source groups. Use /add @channel")
        # still start to allow adding later

    try:
        dest_entity = await client.get_entity(DESTINATION)
        await client.send_message(dest_entity, f"🔥 XYRON DROP ☔ ONLINE\nNow handles multi-line Exp Date / CVV2")
        logger.info(f"✅ Destination: {DESTINATION}")
    except Exception as e:
        logger.error(f"Destination error: {e}")
        return

    if not saved and sources_to_monitor:
        save_channels(sources_to_monitor)

    processed = set()

    # ===== COMMANDS =====
    @client.on(events.NewMessage(pattern='/start'))
    async def start_cmd(e):
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        await e.reply(f"""
🔥 **XYRON DROP** ☔ 🔥
━━━━━━━━━━━━━━━━━━━
✅ Status: LIVE
📡 Groups: {len(sources)}
💎 Formats: ALL (pipe, slash, space, multi-line)

📌 Commands: /status, /testcc, /add, /remove, /list, /stats, /today, /drop
        """)

    @client.on(events.NewMessage(pattern='/status'))
    async def status_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        await e.reply(f"📡 Live – {len(sources)} groups, today {stats.get_today()['cards']} cards")

    @client.on(events.NewMessage(pattern='/testcc'))
    async def testcc_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        parts = e.text.split(maxsplit=1)
        test_text = parts[1] if len(parts) > 1 else "5424320188943301\nExp Date\n01/27\nCVV2\n321"
        cards = extract_ccs(test_text)
        if cards:
            try:
                await client.send_message(dest_entity, format_styled_drop(cards))
                await e.reply(f"✅ Test drop sent – extracted: {cards[0]['exp']}, CVV {cards[0]['cvv']}")
                stats.add_drop(len(cards))
            except FloodWaitError as wait:
                await asyncio.sleep(wait.seconds)
                await client.send_message(dest_entity, format_styled_drop(cards))
                await e.reply("✅ Test drop sent after wait")
        else:
            await e.reply(f"❌ Could not extract CC from `{test_text[:80]}...`")

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
                await e.reply(f"➕ Added: {username}")
                await client.send_message(dest_entity, f"➕ New source: {username}")
            else:
                await e.reply("Already monitoring")
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
            await e.reply(f"❌ Removed: {ch}")
            await client.send_message(dest_entity, f"❌ Removed: {ch}")
        else:
            await e.reply("Not found")

    @client.on(events.NewMessage(pattern='/list'))
    async def list_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        if not sources_to_monitor:
            return await e.reply("No sources")
        msg = "📋 Sources\n"
        for i, ch in enumerate(sources_to_monitor, 1):
            status = "🟢" if any(hasattr(s, 'username') and s.username == ch for s in sources) else "🔴"
            msg += f"{status} {i}. `{ch}`\n"
        await e.reply(msg)

    @client.on(events.NewMessage(pattern='/stats'))
    async def stats_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        total = stats.get_total()
        await e.reply(f"📊 Total cards: {total['cards']}\nDrops: {total['drops']}")

    @client.on(events.NewMessage(pattern='/today'))
    async def today_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        today = stats.get_today()
        await e.reply(f"☀️ Today: {today['cards']} cards, {today['drops']} drops")

    @client.on(events.NewMessage(pattern='/drop'))
    async def drop_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        card = random.choice(MANUAL_CCS)
        cards = [{'number': card['number'], 'exp': card['exp'], 'cvv': card['cvv'], 'bin': card['bin'], 'type': card['type']}]
        try:
            await client.send_message(dest_entity, format_styled_drop(cards))
            await e.reply("💧 Manual drop sent")
            stats.add_drop(1)
        except FloodWaitError as wait:
            await asyncio.sleep(wait.seconds)
            await client.send_message(dest_entity, format_styled_drop(cards))
            await e.reply("💧 Manual drop sent after wait")
            stats.add_drop(1)

    # ===== LIVE DETECTION =====
    @client.on(events.NewMessage(chats=sources))
    async def live_detect(event):
        msg_id = f"{event.chat_id}_{event.message.id}"
        if msg_id in processed:
            return
        if len(processed) > 5000:
            processed.clear()

        text = event.message.text or ""
        if not text:
            return

        # Quick heuristic to avoid processing non-CC messages
        if not re.search(r'\b\d{13,16}\b', text):
            return

        cards = extract_ccs(text)
        if not cards:
            return

        processed.add(msg_id)

        for attempt in range(3):
            try:
                await client.send_message(dest_entity, format_styled_drop(cards), link_preview=False)
                stats.add_drop(len(cards))
                logger.info(f"💧 DROPPED {len(cards)} CC(s) from {event.chat.title}")
                print(f"✅ FORWARDED → {DESTINATION}")
                break
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except Exception as e:
                logger.error(f"Forward error: {e}")
                break

    print(f"\n✅ XYRON DROP ☔ – READY")
    print(f"📡 Monitoring {len(sources)} group(s) → {DESTINATION}")
    print("🧪 Test with: /testcc 5424320188943301\nExp Date\n01/27\nCVV2\n321")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())