"""
XYRON LIVE DROPS - USER ACCOUNT VERSION
Can join any channel automatically using YOUR account
"""

import asyncio
import os
import re
import json
import logging
from datetime import datetime

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import JoinChannelRequest

# ===== CONFIG =====
API_ID = int(os.environ.get('API_ID', 0))
API_HASH = os.environ.get('API_HASH', '')
PHONE_NUMBER = os.environ.get('PHONE_NUMBER', '')  # Your phone number
OWNER_ID = int(os.environ.get('OWNER_ID', 0))
DESTINATION = os.environ.get('DESTINATION_CHANNEL', '@xyrons')

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
    "alert": "🚨", "target": "🎯", "time": "⏱️", "robot": "🤖", "join": "🔗"
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
                'type': "VISA" if clean.startswith('4') else "MC" if clean.startswith('5') else "AMEX"
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
                    'type': "VISA" if clean.startswith('4') else "MC" if clean.startswith('5') else "CARD"
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
    ╔════════════════════════════════════╗
    ║   🔥 XYRON LIVE DROPS 🔥           ║
    ║   USER ACCOUNT MODE                ║
    ║   Can auto-join ANY channel!       ║
    ╚════════════════════════════════════╝
    """)
    
    if not API_ID or not API_HASH or not PHONE_NUMBER:
        logger.error("Missing credentials! Set API_ID, API_HASH, PHONE_NUMBER")
        return
    
    # Use USER account (not bot token!)
    client = TelegramClient('xyron_user', API_ID, API_HASH)
    
    try:
        await client.start(phone=PHONE_NUMBER)
        me = await client.get_me()
        logger.info(f"✅ Logged in as: {me.first_name} (@{me.username})")
        print(f"✅ Logged in as: {me.first_name} (@{me.username})")
    except Exception as e:
        logger.error(f"Failed to login: {e}")
        print(f"❌ Login failed: {e}")
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
        if DESTINATION:
            await client.send_message(DESTINATION, f"🔥 **XYRON LIVE** 🔥\nUser mode active | Can auto-join channels")
    except:
        pass
    
    processed = set()
    
    # ===== FORCE JOIN COMMAND (WORKS WITH USER ACCOUNT!) =====
    @client.on(events.NewMessage(pattern='/join'))
    async def force_join(e):
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        
        parts = e.text.split()
        if len(parts) < 2:
            return await e.reply(f"{F['warning']} Usage: `/join @channel_name`")
        
        channel = parts[1]
        
        try:
            # Get channel entity
            entity = await client.get_entity(channel)
            channel_title = entity.title
            channel_username = entity.username or channel
            
            # JOIN the channel (THIS WORKS WITH USER ACCOUNT!)
            await client(JoinChannelRequest(entity))
            await asyncio.sleep(1)
            
            await e.reply(f"""
{F['join']} **AUTO-JOIN SUCCESSFUL** {F['join']}
━━━━━━━━━━━━━━━━━━━
{F['check']} **Channel:** `{channel_username}`
{F['target']} **Title:** `{channel_title}`
{F['satellite']} **Status:** `JOINED SUCCESSFULLY`

{F['add']} Now add to monitoring:
`/add {channel_username}`
            """)
            logger.info(f"✅ Auto-joined: {channel_username}")
            
        except Exception as ex:
            await e.reply(f"{F['skull']} Failed to join: {str(ex)[:100]}")
            logger.error(f"Join failed: {ex}")
    
    @client.on(events.NewMessage(pattern='/start'))
    async def start_cmd(e):
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        await e.reply(f"""
{F['crown']} **XYRON ACTIVE (USER MODE)** {F['crown']}
━━━━━━━━━━━━━━━━━━━━━━━━
{F['check']} Status: LIVE
{F['satellite']} Channels: {len(monitored)}
{F['join']} /join @channel  - Auto-join ANY channel
{F['add']} /add @channel    - Start monitoring
{F['remove']} /remove @channel - Stop monitoring
{F['list']} /list
{F['drop']} /test

⚡ **USER MODE FEATURES:**
• Can auto-join ANY public channel
• Can see all messages
• Full access like normal user
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
                await e.reply(f"{F['add']} Added: `{username}`\n✅ Now monitoring!")
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
            return await e.reply("No channels monitored!\nUse /join @channel then /add")
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
    
    print(f"\n{'='*50}")
    print(f"✅ USER MODE BOT IS READY!")
    print(f"📡 Monitoring {len(monitored)} channels")
    print(f"\n🔥 COMMANDS:")
    print(f"   /join @channel   - AUTO-JOIN any channel!")
    print(f"   /add @channel    - Start monitoring")
    print(f"   /remove @channel - Stop monitoring")
    print(f"   /list           - Show monitored channels")
    print(f"   /test           - Send test drop")
    print(f"{'='*50}\n")
    
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped")
    except Exception as e:
        logger.error(f"Fatal: {e}")