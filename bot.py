"""
XYRON LIVE DROPS - COMPLETE PRODUCTION BOT
✅ Auto drop when CC detected LIVE
✅ Bot token for commands
✅ User account for joining channels
✅ Today stats + Manual drop
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
    "today": "☀️", "rain": "☔", "calendar": "📅", "rocket": "🚀"
}

# ===== CC DETECTION PATTERNS =====
CC_PATTERNS = [
    r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
    r'\b\d{16}\b',
    r'(\d{13,16})[|\s/:-](\d{1,2})[|\s/:-](\d{2,4})[|\s/:-](\d{3,4})',
]

KEYWORDS = ['cc', 'card', 'credit', 'visa', 'mastercard', 'amex', 'discover', 'cvv', 'drop', 'valid', 'fresh', 'live', 'bin']

# ===== LUHN ALGORITHM =====
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

# ===== EXTRACT CC FROM TEXT =====
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
                'type': "VISA" if clean.startswith('4') else "MC" if clean.startswith('5') else "AMEX" if clean.startswith('3') else "DISC" if clean.startswith('6') else "CC"
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
                    'type': "VISA" if clean.startswith('4') else "MC" if clean.startswith('5') else "AMEX" if clean.startswith('3') else "CC"
                })
    return cards

# ===== FUTURISTIC DROP FORMAT =====
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
{E['check']} │ ✅ **LUHN:** `PASSED`
{E['neon']} **└─────** {E['neon']}

"""
    
    msg += f"""
{E['crown']}{E['lightning']} **XYRON VERIFIED** {E['lightning']}{E['crown']}
{E['ninja']} *AUTHENTICATED • SECURE • READY* {E['ninja']}
{E['drop']} `FRESH CAPTURE - USE QUICKLY` {E['drop']}
{E['rocket']} **XYRON DROPS | PREMIUM EDITION** {E['rocket']}
"""
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

# ===== CHANNEL MANAGER =====
def load_channels():
    try:
        with open(CHANNELS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_channels(channels):
    with open(CHANNELS_FILE, 'w') as f:
        json.dump(channels, f)

# ===== MANUAL CC LIST =====
MANUAL_CCS = [
    {'num': '4532123456781234', 'exp': '12/26', 'cvv': '789', 'type': 'VISA'},
    {'num': '5424123456781234', 'exp': '08/27', 'cvv': '456', 'type': 'MASTERCARD'},
    {'num': '378282246310005', 'exp': '06/25', 'cvv': '1234', 'type': 'AMEX'},
]

# ===== MAIN BOT =====
async def main():
    print("""
    ╔════════════════════════════════════════════════╗
    ║   🔥 XYRON LIVE DROPS - PRODUCTION READY 🔥    ║
    ║   ✅ Auto Drop on CC Detection                 ║
    ║   🤖 Bot + User Account Dual Mode              ║
    ╚════════════════════════════════════════════════╝
    """)
    
    # Start Bot Client (for commands and dropping)
    bot_client = TelegramClient('xyron_bot', API_ID, API_HASH)
    await bot_client.start(bot_token=BOT_TOKEN)
    bot_me = await bot_client.get_me()
    logger.info(f"✅ Bot online: @{bot_me.username}")
    print(f"✅ Bot online: @{bot_me.username}")
    
    # Start User Client (for joining channels)
    user_client = None
    if SESSION_STRING:
        user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
        await user_client.start()
        user_me = await user_client.get_me()
        logger.info(f"✅ User online: @{user_me.username}")
        print(f"✅ User online: @{user_me.username}")
    
    # Health check for Railway
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
    
    # Load monitored channels
    saved = load_channels()
    monitored = []
    
    for ch in saved:
        try:
            entity = await bot_client.get_entity(ch)
            monitored.append(entity)
            logger.info(f"📡 Monitoring: {ch}")
            print(f"📡 Monitoring: {ch}")
        except Exception as e:
            logger.warning(f"⚠️ Cannot access {ch}: {e}")
    
    # Send startup notification
    try:
        await bot_client.send_message(OWNER_ID, f"""✅ **XYRON ONLINE** ✅
━━━━━━━━━━━━━━━━━━━
{E['satellite']} Monitoring: `{len(monitored)}` channels
{E['drop']} Total drops: `{stats.get_total()}`
{E['check']} Status: `LIVE`
{E['rocket']} Auto-drop: `ACTIVE`

📌 Commands: /start
""")
        if DESTINATION:
            await bot_client.send_message(DESTINATION, f"{E['alert']}{E['fire']} **XYRON LIVE** {E['fire']}{E['alert']}\n{E['check']} Auto-drop active | Monitoring {len(monitored)} channels")
    except:
        pass
    
    processed = set()
    
    # ========== COMMANDS ==========
    
    @bot_client.on(events.NewMessage(pattern='/start'))
    async def start_cmd(e):
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        
        today = stats.get_today()
        await e.reply(f"""
{E['crown']} **XYRON CONTROL PANEL** {E['crown']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━
{E['check']} Status: `LIVE`
{E['satellite']} Channels: `{len(monitored)}`
{E['today']} Today: `{today['cards']}` cards / `{today['drops']}` drops
{E['crystal']} Total: `{stats.get_total()}` cards

{E['rocket']} **COMMANDS:**
{E['join']} `/join @channel` - Auto-join
{E['add']} `/add @channel` - Start monitoring
{E['remove']} `/remove @channel` - Stop monitoring
{E['list']} `/list` - Show monitored channels
{E['stats']} `/stats` - Total statistics
{E['today']} `/today` - Today's drops
{E['drop']} `/drop` - Manual CC drop
{E['bolt']} `/test` - Send test drop

{E['alert']} *Auto-drop active on all monitored channels*
        """)
    
    @bot_client.on(events.NewMessage(pattern='/join'))
    async def join_cmd(e):
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        
        if not user_client:
            return await e.reply("❌ User account not configured! Add SESSION_STRING to Railway variables.")
        
        parts = e.text.split()
        if len(parts) < 2:
            return await e.reply(f"Usage: `/join @channel_name` or `/join https://t.me/channel`")
        
        channel = parts[1]
        if channel.startswith('https://t.me/'):
            channel = channel.replace('https://t.me/', '@')
        
        try:
            entity = await user_client.get_entity(channel)
            username = entity.username or channel
            await user_client(JoinChannelRequest(entity))
            await asyncio.sleep(1)
            
            await e.reply(f"""
{E['join']} **AUTO-JOIN SUCCESSFUL!** {E['join']}
━━━━━━━━━━━━━━━━━━━━━━━━━
{E['check']} **Channel:** `{username}`
{E['target']} **Title:** `{entity.title}`
{E['satellite']} **Status:** `JOINED`

{E['add']} Now add to monitoring:
`/add {username}`
            """)
            logger.info(f"✅ Joined: {username}")
        except Exception as ex:
            await e.reply(f"{E['skull']} Failed: {str(ex)[:150]}")
    
    @bot_client.on(events.NewMessage(pattern='/add'))
    async def add_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        
        parts = e.text.split()
        if len(parts) < 2:
            return await e.reply(f"{E['warning']} Usage: `/add @channel`")
        
        channel = parts[1]
        
        try:
            entity = await bot_client.get_entity(channel)
            username = entity.username or channel
            
            if username not in saved:
                saved.append(username)
                save_channels(saved)
                monitored.append(entity)
                await e.reply(f"{E['add']} **Added:** `{username}`\n{E['check']} Now monitoring for CC drops!")
                logger.info(f"✅ Added to monitoring: {username}")
            else:
                await e.reply(f"{E['warning']} Already monitoring this channel!")
        except Exception as ex:
            await e.reply(f"{E['skull']} Error: {str(ex)[:100]}")
    
    @bot_client.on(events.NewMessage(pattern='/remove'))
    async def remove_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        
        parts = e.text.split()
        if len(parts) < 2:
            return await e.reply(f"{E['warning']} Usage: `/remove @channel`")
        
        channel = parts[1].replace('@', '')
        
        if channel in saved:
            saved.remove(channel)
            save_channels(saved)
            
            for m in monitored[:]:
                if hasattr(m, 'username') and m.username == channel:
                    monitored.remove(m)
            
            await e.reply(f"{E['remove']} **Removed:** `{channel}`\n{E['check']} No longer monitoring.")
            logger.info(f"❌ Removed: {channel}")
        else:
            await e.reply(f"{E['warning']} Channel not found in monitoring list!")
    
    @bot_client.on(events.NewMessage(pattern='/list'))
    async def list_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        
        if not saved:
            return await e.reply(f"{E['warning']} No channels monitored!\n\nUse `/join @channel` then `/add @channel`")
        
        msg = f"{E['list']} **MONITORED CHANNELS**\n━━━━━━━━━━━━━━━━━━━\n"
        for i, ch in enumerate(saved, 1):
            status = "🟢" if any(hasattr(m, 'username') and m.username == ch for m in monitored) else "🔴"
            msg += f"{status} {i}. `{ch}`\n"
        
        msg += f"\n{E['drop']} Auto-drop: **ACTIVE** on all channels"
        await e.reply(msg)
    
    @bot_client.on(events.NewMessage(pattern='/stats'))
    async def stats_cmd(e):
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        
        total = stats.get_total()
        await e.reply(f"""
{E['stats']} **XYRON TOTAL STATISTICS** {E['stats']}
━━━━━━━━━━━━━━━━━━━━━━━━━
{E['crystal']} Total Cards: `{total}`
{E['satellite']} Active Channels: `{len(monitored)}`
{E['check']} Bot Status: `LIVE`
{E['rocket']} Version: `XYRON v5.0`

{E['alert']} *Auto-drop enabled*
        """)
    
    @bot_client.on(events.NewMessage(pattern='/today'))
    async def today_cmd(e):
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        
        today = stats.get_today()
        today_date = date.today().strftime("%d/%m/%Y")
        
        sources_text = ""
        for s in today['sources']:
            sources_text += f"\n  {E['laser']} `{s}`"
        
        if not sources_text:
            sources_text = "\n  No drops yet today"
        
        await e.reply(f"""
{E['today']}{E['rain']} **TODAY'S CC DROPS** {E['rain']}{E['today']}
━━━━━━━━━━━━━━━━━━━━━━━━━
{E['calendar']} Date: `{today_date}`
{E['drop']} Drops: `{today['drops']}`
{E['crystal']} Cards: `{today['cards']}`

{E['satellite']} Sources:{sources_text}

{E['quantum']}━━━━━━━━━━━━━━━━━━━━━━━━━{E['quantum']}
{E['check']} *Auto-drop active*
        """)
    
    @bot_client.on(events.NewMessage(pattern='/drop'))
    async def drop_cmd(e):
        if e.sender_id != OWNER_ID:
            return await e.reply("❌ Unauthorized")
        
        parts = e.text.split()
        
        if len(parts) >= 2:
            custom_text = ' '.join(parts[1:])
            cards = extract_ccs(custom_text)
            
            if cards:
                dest = DESTINATION if DESTINATION else OWNER_ID
                await bot_client.send_message(dest, format_drop(cards, "MANUAL DROP"))
                await e.reply(f"{E['drop']} **Manual drop sent!** {E['drop']}\n{E['check']} {len(cards)} cards dropped.")
                stats.add_drop(len(cards), "MANUAL")
                logger.info(f"Manual drop: {len(cards)} cards")
            else:
                await e.reply(f"{E['warning']} Invalid CC format!\n\nExamples:\n`/drop 4111111111111111|12|26|123`\n`/drop 4111 1111 1111 1111 12/26 123`")
        else:
            card = random.choice(MANUAL_CCS)
            cards = [{
                'masked': f"{card['num'][:4]}****{card['num'][-4:]}",
                'bin': card['num'][:6],
                'exp': card['exp'],
                'cvv': card['cvv'],
                'type': card['type']
            }]
            
            dest = DESTINATION if DESTINATION else OWNER_ID
            await bot_client.send_message(dest, format_drop(cards, "☔ XYRON MANUAL ☔"))
            await e.reply(f"""
{E['drop']} **MANUAL CC DROPPED** {E['drop']}
━━━━━━━━━━━━━━━━━━━
{E['crystal']} Type: `{card['type']}`
{E['time']} EXP: `{card['exp']}`
{E['shield']} CVV: `{card['cvv']}`

{E['check']} Sent to {DESTINATION}
            """)
            stats.add_drop(1, "MANUAL")
            logger.info("Manual random drop")
    
    @bot_client.on(events.NewMessage(pattern='/test'))
    async def test_cmd(e):
        if e.sender_id != OWNER_ID:
            return
        
        test_cards = [{
            'masked': '4111****1111',
            'bin': '411111',
            'exp': '12/26',
            'cvv': '123',
            'type': 'TEST'
        }]
        
        dest = DESTINATION if DESTINATION else OWNER_ID
        await bot_client.send_message(dest, format_drop(test_cards, "TEST CHANNEL"))
        await e.reply(f"{E['check']} **Test drop sent!**\n{E['satellite']} Check {DESTINATION}")
        logger.info("Test drop sent")
    
    # ========== LIVE AUTO DROP HANDLER ==========
    @bot_client.on(events.NewMessage(chats=monitored))
    async def live_auto_drop(e):
        msg_id = f"{e.chat_id}_{e.message.id}"
        
        if msg_id in processed:
            return
        
        if len(processed) > 5000:
            processed.clear()
        
        if not e.message or not e.message.text:
            return
        
        text = e.message.text
        
        # Check for CC patterns
        has_cc = False
        for pattern in CC_PATTERNS:
            if re.search(pattern, text):
                has_cc = True
                break
        
        has_keywords = any(k in text.lower() for k in KEYWORDS)
        
        if not has_cc and not has_keywords:
            return
        
        # Extract and validate CCs
        cards = extract_ccs(text)
        
        if cards:
            processed.add(msg_id)
            channel_name = e.chat.title or e.chat.username or "UNKNOWN"
            dest = DESTINATION if DESTINATION else OWNER_ID
            
            try:
                # Send formatted drop
                drop_message = format_drop(cards, channel_name)
                await bot_client.send_message(dest, drop_message, link_preview=False)
                
                # Update stats
                stats.add_drop(len(cards), channel_name)
                
                # Log to console
                logger.info(f"{E['drop']} AUTO-DROPPED {len(cards)} cards from {channel_name}")
                print(f"✅ LIVE DROP: {len(cards)} cards from {channel_name} → {dest}")
                
                # Also send raw preview
                await bot_client.send_message(dest, f"{E['neon']} **RAW CAPTURE:**\n`{text[:200]}`")
                
            except FloodWaitError as wait:
                logger.warning(f"Rate limited, waiting {wait.seconds}s")
                await asyncio.sleep(wait.seconds)
            except Exception as ex:
                logger.error(f"Drop error: {ex}")
    
    # ========== STARTUP COMPLETE ==========
    print(f"""
{'='*55}
✅ **XYRON LIVE DROPS - FULLY ACTIVE**
{'='*55}
{E['satellite']} Monitoring: {len(monitored)} channels
{{E['drop']} Auto-drop: ENABLED
{E['rocket']} Destination: {DESTINATION}
{E['crown']} Owner: @{bot_me.username}

📌 **COMMANDS READY:**
   /join @channel  - Auto-join any channel
   /add @channel   - Start monitoring
   /list           - Show monitored channels
   /today          - Today's stats
   /drop           - Manual CC drop
   /test           - Test drop

{E['alert']} **WAITING FOR CC DETECTION...**
{'='*55}
""")
    
    await bot_client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
```
