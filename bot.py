"""
XYRON LIVE DROPS - WORKING BOT
"""

import asyncio
import os
import re
import json
import logging
from datetime import datetime

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

# ===== CONFIG =====
API_ID = int(os.environ.get('22225572', 0))
API_HASH = os.environ.get('3734fae2ee81188b5355cab5a30e8f55', '')
BOT_TOKEN = os.environ.get('8808705051:AAGLbuTt3CXJ3Rf2kwChmcw_RNKJJqoTZLY', '')
OWNER_ID = int(os.environ.get('5758431714', 0))
DESTINATION = os.environ.get('@xyrons', '@xyrons')

CHANNELS_FILE = 'monitored.json'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===== EMOJIS =====
F = {
    "neon": "🔮", "cyber": "💠", "plasma": "🔥", "quantum": "⚛️",
    "galaxy": "🌌", "crystal": "💎", "laser": "🔫", "mega": "💥",
    "satellite": "🛸", "shield": "🛡️", "dragon": "🐉", "skull": "💀",
    "crown": "👑", "lightning": "⚡", "add": "➕", "remove": "❌",
    "list": "📋", "check": "✅", "warning": "⚠️", "drop": "💧",
    "alert": "🚨", "target": "🎯", "time": "⏱️", "robot": "🤖"
}

# ===== CC DETECTION =====
CC_FORMATTED = r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'
CC_WITH_EXP = r'(\d{13,16})[|\s/:-](\d{1,2})[|\s/:-](\d{2,4})[|\s/:-](\d{3,4})'
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
    matches = re.findall(CC_WITH_EXP, text, re.IGNORECASE)
    for match in matches:
        clean = re.sub(r'[\s-]', '', match[0])
        if luhn_check(clean):
            cards.append({
                'masked': f"{clean[:4]}****{clean[-4:]}",
                'exp': f"{match[1]}/{match[2][-2:]}",
                'cvv': match[3],
                'bin': clean[:6],
                'type': "VISA" if clean.startswith('4') else "MC" if clean.startswith('5') else "AMEX"
            })
    if not cards:
        numbers = re.findall(CC_FORMATTED, text)
        for num in set(numbers):
            clean = re.sub(r'[\s-]', '', num)
            if luhn_check(clean):
                cards.append({
                    'masked': f"{clean[:4]}****{clean[-4:]}",
                    'exp': 'XX/XX',
                    'cvv': 'XXX',
                    'bin': clean[:6],
                    'type': "CARD"
                })
    return cards

def format_drop(cards, channel_name):
    now = datetime.now().strftime("%H:%M:%S")
    date = datetime.now().strftime("%d/%m/%Y")
    msg = f"""
{F['alert']}{F['plasma']} **XYRON LIVE DROP** {F['plasma']}{F['alert']}
{F['galaxy']}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{F['galaxy']}

{F['satellite']} **SOURCE:** `{channel_name}`
{F['time']} **TIME:** `{date} {now}`
{F['target']} **STATUS:** `LIVE`

"""
    for i, card in enumerate(cards, 1):
        msg += f"""
{F['neon']} **CARD #{i}** {F['neon']}
┌─────────────────────────┐
│ 💳 `{card['masked']}`    │
│ 🏦 BIN: `{card['bin']}`   │
│ 📅 EXP: `{card['exp']}`  │
│ 🔒 CVV: `{card['cvv']}`  │
│ ✅ VALID: `PASS`         │
└─────────────────────────┘
"""
    msg += f"""
{F['crown']}{F['lightning']} **XYRON VERIFIED** {F['lightning']}{F['crown']}
{F['shield']} *AUTHENTICATED • READY TO USE* {F['shield']}
{F['drop']} `FRESH CAPTURE` {F['drop']}
"""
    return msg

def load_channels():
    try:
        with open(CHANNELS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_channels(channels):
    with open(CHANNELS_FILE, 'w') as f:
        json.dump(channels, f)

async def main():
    print("""
    ╔════════════════════════════════╗
    ║   🔥 XYRON LIVE DROPS 🔥       ║
    ║   Starting bot...              ║
    ╚════════════════════════════════╝
    """)
    
    # DEBUG PRINTS
    print(f"API_ID: {API_ID}")
    print(f"API_HASH: {API_HASH[:10] if API_HASH else 'NOT SET'}...")
    print(f"BOT_TOKEN: {BOT_TOKEN[:15] if BOT_TOKEN else 'NOT SET'}...")
    print(f"OWNER_ID: {OWNER_ID}")
    print(f"DESTINATION: {DESTINATION}")
    
    if not API_ID or not API_HASH or not BOT_TOKEN:
        logger.error("Missing credentials! Set Railway variables")
        print("❌ Missing API_ID, API_HASH, or BOT_TOKEN")
        return
    
    if not OWNER_ID:
        logger.error("Missing OWNER_ID!")
        print("❌ Missing OWNER_ID")
        return
    
    client = TelegramClient('xyron', API_ID, API_HASH)
    
    try:
        await client.start(bot_token=BOT_TOKEN)
        me = await client.get_me()
        logger.info(f"✅ Bot online: @{me.username}")
        print(f"✅ Bot online: @{me.username}")
    except Exception as e:
        logger.error(f"Failed to start: {e}")
        print(f"❌ Failed to start: {e}")
        return
    
    # Health check
    if os.environ.get('PORT'):
        try:
            from aiohttp import web
            app = web.Application()
            app.router.add_get('/', lambda r: web.Response(text='OK'))
            runner = web.AppRunner(app)
            await runner.setup()
            await web.TCPSite(runner, '0.0.0.0', int(os.environ.get('PORT', 8080))).start()
            logger.info(f"✅ Health check on port {os.environ.get('PORT', 8080)}")
        except:
            pass
    
    saved = load_channels()
    monitored = []
    
    for ch in saved:
        try:
            entity = await client.get_entity(ch)
            monitored.append(entity)
            logger.info(f"📡 Monitoring: {ch}")
        except Exception as e:
            logger.warning(f"⚠️ Cannot access {ch}: {e}")
    
    try:
        await client.send_message(OWNER_ID, f"✅ XYRON ONLINE\n📡 Monitoring {len(monitored)} channels")
        if DESTINATION:
            await client.send_message(DESTINATION, f"🔥 **XYRON LIVE** 🔥\nSystem active • Ready for drops")
        print("✅ Startup messages sent")
    except Exception as e:
        logger.warning(f"Could not send startup: {e}")
        print(f"⚠️ Could not send startup: {e}")
    
    processed = set()
    
    @client.on(events.NewMessage(pattern='/start'))
    async def start_cmd(e):
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        await e.reply(f"""
{F['crown']} **XYRON ACTIVE** {F['crown']}
━━━━━━━━━━━━━━━━━
{F['check']} Status: LIVE
{F['satellite']} Channels: {len(monitored)}
{F['add']} /add @channel
{F['remove']} /remove @channel  
{F['list']} /list
{F['drop']} /test
        """)
    
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
            if username not in saved:
                saved.append(username)
                save_channels(saved)
                monitored.append(entity)
                await e.reply(f"{F['add']} Added: `{username}`")
                logger.info(f"Added: {username}")
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
        if ch in saved:
            saved.remove(ch)
            save_channels(saved)
            for m in monitored[:]:
                if hasattr(m, 'username') and m.username == ch:
                    monitored.remove(m)
            await e.reply(f"{F['remove']} Removed: `{ch}`")
        else:
            await e.reply("Channel not found!")
    
    @client.on(events.NewMessage(pattern='/list'))
    async def list_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        if not saved:
            return await e.reply("No channels monitored!")
        msg = f"{F['list']} **Channels:**\n"
        for i, ch in enumerate(saved, 1):
            status = "🟢" if any(hasattr(m, 'username') and m.username == ch for m in monitored) else "🔴"
            msg += f"{status} {i}. `{ch}`\n"
        await e.reply(msg)
    
    @client.on(events.NewMessage(pattern='/test'))
    async def test_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        test_cards = [{'masked': '4111****1111', 'bin': '411111', 'exp': '12/26', 'cvv': '123', 'type': 'TEST'}]
        dest = DESTINATION if DESTINATION else OWNER_ID
        await client.send_message(dest, format_drop(test_cards, "TEST"))
        await e.reply("✅ Test drop sent!")
        logger.info("Test drop sent")
    
    @client.on(events.NewMessage(chats=monitored))
    async def drop_handler(e):
        mid = f"{e.chat_id}_{e.message.id}"
        if mid in processed:
            return
        if len(processed) > 5000:
            processed.clear()
        if not e.message or not e.message.text:
            return
        text = e.message.text
        if not re.search(CC_FORMATTED, text) and not any(k in text.lower() for k in KEYWORDS):
            return
        cards = extract_ccs(text)
        if cards:
            processed.add(mid)
            name = e.chat.title or e.chat.username or "UNKNOWN"
            dest = DESTINATION if DESTINATION else OWNER_ID
            try:
                await client.send_message(dest, format_drop(cards, name), link_preview=False)
                logger.info(f"💧 DROPPED {len(cards)} cards from {name}")
            except FloodWaitError as wait:
                await asyncio.sleep(wait.seconds)
            except Exception as ex:
                logger.error(f"Send error: {ex}")
    
    logger.info(f"🚀 XYRON LIVE - READY!")
    print(f"🚀 XYRON LIVE - READY!")
    logger.info(f"📡 Monitoring {len(monitored)} channels")
    print(f"📡 Monitoring {len(monitored)} channels")
    
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped")
    except Exception as e:
        logger.error(f"Fatal: {e}")
        print(f"❌ Fatal error: {e}")