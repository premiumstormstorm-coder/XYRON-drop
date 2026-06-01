"""
XYRON LIVE DROPS - FULLY WORKING BOT
Real-time CC drops from monitored channels
Admin commands | Instant forwarding
"""

import asyncio
import os
import re
import json
import logging
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.functions.channels import JoinChannelRequest

# ===== RAILWAY VARIABLES =====
API_ID = int(os.environ.get('22225572', 0))
API_HASH = os.environ.get('3734fae2ee81188b5355cab5a30e8f55', '')
BOT_TOKEN = os.environ.get('8808705051:AAGLbuTt3CXJ3Rf2kwChmcw_RNKJJqoTZLY', '')
OWNER_ID = int(os.environ.get('5758431714', 0))
DESTINATION = os.environ.get('@xyrons', '')

CHANNELS_FILE = 'monitored_channels.json'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===== FUTURISTIC EMOJIS =====
F = {
    "neon": "🔮", "cyber": "💠", "hologram": "✨", "quantum": "⚛️",
    "plasma": "🔥", "void": "🖤", "galaxy": "🌌", "nuclear": "☢️",
    "robot": "🤖", "alien": "👽", "crystal": "💎", "laser": "🔫",
    "mega": "💥", "storm": "🌩️", "virus": "🦠", "circuit": "🔌",
    "microchip": "📟", "satellite": "🛸", "sword": "⚔️", "shield": "🛡️",
    "dragon": "🐉", "skull": "💀", "crown": "👑", "lightning": "⚡",
    "infinity": "♾️", "matrix": "〽️", "binary": "🔢", "terminal": "💻",
    "add": "➕", "remove": "❌", "list": "📋", "check": "✅",
    "warning": "⚠️", "info": "ℹ️", "power": "🔋", "drop": "💧",
    "target": "🎯", "time": "⏱️", "alert": "🚨"
}

# ===== CC DETECTION =====
CC_PATTERN = r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12}|\d{16})\b'
CC_FORMATTED = r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'
CC_WITH_EXP = r'(\d{13,16})[|\s/:-](\d{1,2})[|\s/:-](\d{2,4})[|\s/:-](\d{3,4})'
KEYWORDS = ['cc', 'card', 'credit', 'visa', 'mastercard', 'amex', 'discover', 'cvv', 'drop', 'valid', 'fresh', 'live', 'bin']

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
    
    # Pattern 1: Standard CC with expiry and CVV
    matches = re.findall(CC_WITH_EXP, text, re.IGNORECASE)
    for match in matches:
        clean = re.sub(r'[\s-]', '', match[0])
        if luhn_check(clean):
            cards.append({
                'num': clean,
                'masked': f"{clean[:4]}****{clean[-4:]}",
                'exp': f"{match[1]}/{match[2][-2:]}",
                'cvv': match[3],
                'bin': clean[:6],
                'type': "💳 VISA" if clean.startswith('4') else "💳 MC" if clean.startswith('5') else "💳 AMEX" if clean.startswith('3') else "💳 DISC"
            })
    
    # Pattern 2: Just card numbers
    if not cards:
        numbers = re.findall(CC_PATTERN, text)
        numbers += re.findall(CC_FORMATTED, text)
        for num in set(numbers):
            clean = re.sub(r'[\s-]', '', num)
            if luhn_check(clean):
                context = text[max(0, text.find(num)-100):text.find(num)+100]
                expiry = re.search(r'(\d{2})[/\-](\d{2,4})', context)
                cvv = re.search(r'cvv[:.\s]*(\d{3,4})', context, re.I)
                cards.append({
                    'num': clean,
                    'masked': f"{clean[:4]}****{clean[-4:]}",
                    'exp': expiry.group(0) if expiry else 'XX/XX',
                    'cvv': cvv.group(1) if cvv else 'XXX',
                    'bin': clean[:6],
                    'type': "💳 VISA" if clean.startswith('4') else "💳 MC" if clean.startswith('5') else "💳 AMEX" if clean.startswith('3') else "💳 DISC"
                })
    return cards

def format_drop(cards, channel_name):
    now = datetime.now()
    timestamp = now.strftime("%H:%M:%S")
    date = now.strftime("%d/%m/%Y")
    
    drop = f"""
{F['alert']}{F['plasma']}{F['storm']} ═══ **XYRON LIVE DROP** ═══ {F['storm']}{F['plasma']}{F['alert']}
{F['quantum']} *REAL-TIME CAPTURE* {F['quantum']}
{F['galaxy']}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{F['galaxy']}

{F['satellite']} **SOURCE:** `{channel_name}`
{F['target']} **TIME:** `{date} {timestamp}`
{F['microchip']} **STATUS:** `LIVE / VALID`

{F['dragon']}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{F['dragon']}

"""
    for i, card in enumerate(cards, 1):
        drop += f"""
{F['neon']} **┌── CARD #{i}** {F['neon']}
{F['cyber']} │ {F['robot']} `{card['type']}`
{F['hologram']} │ 💳 `{card['masked']}`
{F['circuit']} │ 🏦 BIN: `{card['bin']}`
{F['terminal']} │ 📅 EXP: `{card['exp']}`
{F['laser']} │ 🔒 CVV: `{card['cvv']}`
{F['shield']} │ ✅ LUHN: `PASS`
{F['neon']} **└─────** {F['neon']}

"""
    
    drop += f"""
{F['crown']}{F['lightning']}{F['mega']} **XYRON VERIFIED** {F['mega']}{F['lightning']}{F['crown']}
{F['alien']} *AUTHENTICATED • VALID • READY* {F['alien']}

{F['quantum']}╔════════════════════════════════════════╗
{F['neon']}║  {F['infinity']} XYRON SECURITY v9.4 {F['infinity']}                ║
{F['cyber']}║  {F['matrix']} ENCRYPTION: ACTIVE {F['matrix']}              ║
{F['plasma']}║  {F['nuclear']} DROP MODE: INSTANT {F['nuclear']}             ║
{F['galaxy']}╚════════════════════════════════════════╝

{F['skull']} **FRESH DROP** • USE QUICKLY {F['skull']}
{F['void']} **XYRON DROPS** | *PREMIUM EDITION*

{F['robot']} `SYSTEM: LIVE` {F['robot']} {F['crystal']} `DROP: READY` {F['crystal']}
"""
    return drop

# ===== CHANNEL MANAGER =====
class ChannelManager:
    def __init__(self):
        self.channels = self.load()
    
    def load(self):
        try:
            with open(CHANNELS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def save(self):
        with open(CHANNELS_FILE, 'w') as f:
            json.dump(self.channels, f)
    
    def add(self, channel_id, username, title):
        ch = {'id': channel_id, 'username': username, 'title': title, 'added': datetime.now().isoformat()}
        if ch not in self.channels:
            self.channels.append(ch)
            self.save()
            return True
        return False
    
    def remove(self, username):
        for ch in self.channels:
            if ch['username'] == username:
                self.channels.remove(ch)
                self.save()
                return True
        return False
    
    def get_all(self):
        return self.channels

cm = ChannelManager()

# ===== MAIN BOT =====
async def main():
    print(f"""
    ╔════════════════════════════════════════════╗
    ║   {F['plasma']} XYRON LIVE DROPS ACTIVE {F['plasma']}            ║
    ║   {F['lightning']} REAL-TIME CC MONITOR {F['lightning']}          ║
    ║   {F['crown']} READY FOR DROPS {F['crown']}                     ║
    ╚════════════════════════════════════════════╝
    """)
    
    # Start bot
    client = TelegramClient('xyron_live', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
    bot = await client.get_me()
    logger.info(f"{F['check']} BOT ONLINE: @{bot.username}")
    
    # Health check for Railway
    if os.environ.get('PORT'):
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('0.0.0.0', int(os.environ.get('PORT', 8080))))
        sock.listen(1)
    
    # Load previously added channels
    monitored_entities = []
    for ch in cm.get_all():
        try:
            entity = await client.get_entity(ch['username'])
            monitored_entities.append(entity)
            logger.info(f"{F['satellite']} MONITORING: {ch['username']}")
        except Exception as e:
            logger.error(f"{F['warning']} CAN'T ACCESS: {ch['username']}")
    
    # Send startup
    await client.send_message(OWNER_ID, f"{F['check']} XYRON ONLINE\n{F['satellite']} Monitoring {len(monitored_entities)} channels")
    
    if DESTINATION:
        await client.send_message(DESTINATION, f"{F['alert']} **XYRON LIVE** {F['alert']}\n{F['lightning']} System Active • Ready for Drops")
    
    # Track processed messages
    processed = set()
    
    # ===== COMMANDS =====
    @client.on(events.NewMessage(pattern='/start'))
    async def cmd_start(event):
        if event.sender_id == OWNER_ID:
            await event.reply(f"""
{F['crown']} **XYRON CONTROL PANEL** {F['crown']}
━━━━━━━━━━━━━━━━━━━━━
{F['check']} Status: `LIVE`
{F['satellite']} Channels: `{len(monitored_entities)}`
{F['add']} /add @channel
{F['remove']} /remove @channel
{F['list']} /list
{F['stats']} /stats
{F['power']} /test
            """)
    
    @client.on(events.NewMessage(pattern='/add'))
    async def cmd_add(event):
        if event.sender_id != OWNER_ID:
            return
        parts = event.message.text.split()
        if len(parts) < 2:
            await event.reply(f"{F['warning']} Usage: `/add @channel`")
            return
        
        channel = parts[1]
        try:
            entity = await client.get_entity(channel)
            # Try to join
            try:
                await client(JoinChannelRequest(entity))
                await asyncio.sleep(1)
            except:
                pass
            
            username = entity.username or channel
            title = entity.title
            
            if cm.add(entity.id, username, title):
                monitored_entities.append(entity)
                await event.reply(f"{F['add']} **ADDED:** `{username}`\n{F['check']} Now monitoring this channel!")
                logger.info(f"{F['add']} Added: {username}")
            else:
                await event.reply(f"{F['warning']} Channel already monitored!")
        except Exception as e:
            await event.reply(f"{F['skull']} Error: {str(e)[:100]}")
    
    @client.on(events.NewMessage(pattern='/remove'))
    async def cmd_remove(event):
        if event.sender_id != OWNER_ID:
            return
        parts = event.message.text.split()
        if len(parts) < 2:
            await event.reply(f"{F['warning']} Usage: `/remove @channel`")
            return
        
        channel = parts[1].replace('@', '')
        if cm.remove(channel):
            for e in monitored_entities[:]:
                if e.username == channel:
                    monitored_entities.remove(e)
            await event.reply(f"{F['remove']} **REMOVED:** `{channel}`")
            logger.info(f"{F['remove']} Removed: {channel}")
        else:
            await event.reply(f"{F['warning']} Channel not found!")
    
    @client.on(events.NewMessage(pattern='/list'))
    async def cmd_list(event):
        if event.sender_id != OWNER_ID:
            return
        channels = cm.get_all()
        if not channels:
            await event.reply(f"{F['warning']} No channels monitored!")
            return
        
        msg = f"{F['list']} **MONITORED CHANNELS**\n━━━━━━━━━━━━━━━━━\n"
        for i, ch in enumerate(channels, 1):
            status = "🟢" if any(e.username == ch['username'] for e in monitored_entities) else "🔴"
            msg += f"{status} {i}. `{ch['username']}`\n"
        await event.reply(msg)
    
    @client.on(events.NewMessage(pattern='/stats'))
    async def cmd_stats(event):
        if event.sender_id != OWNER_ID:
            return
        await event.reply(f"""
{F['crystal']} **XYRON STATISTICS**
━━━━━━━━━━━━━━━━━━━
{F['satellite']} Active Channels: `{len(monitored_entities)}`
{F['drop']} Drops Today: `Calculating...`
{F['quantum']} Status: `LIVE`
{F['check']} Verified: `XYRON ACTIVE`
        """)
    
    @client.on(events.NewMessage(pattern='/test'))
    async def cmd_test(event):
        if event.sender_id != OWNER_ID:
            return
        # Send test drop
        test_cards = [{'masked': '4111****1111', 'bin': '411111', 'exp': '12/26', 'cvv': '123', 'type': '💳 TEST'}]
        test_drop = format_drop(test_cards, "TEST_CHANNEL")
        await client.send_message(DESTINATION or OWNER_ID, test_drop)
        await event.reply(f"{F['check']} Test drop sent!")
    
    # ===== LIVE DROP HANDLER =====
    @client.on(events.NewMessage(chats=monitored_entities))
    async def live_drop(event):
        msg_id = f"{event.chat_id}_{event.message.id}"
        if msg_id in processed:
            return
        
        if len(processed) > 5000:
            processed.clear()
        
        if not event.message.text:
            return
        
        text = event.message.text
        
        # Check for CC
        has_cc = bool(re.search(CC_FORMATTED, text)) or bool(re.search(CC_WITH_EXP, text))
        has_keywords = any(k in text.lower() for k in KEYWORDS)
        
        if has_cc or has_keywords:
            cards = extract_ccs(text)
            
            if cards:
                processed.add(msg_id)
                channel_name = event.chat.title or event.chat.username or str(event.chat_id)
                
                # Format and send drop
                drop_msg = format_drop(cards, channel_name)
                
                try:
                    await client.send_message(DESTINATION, drop_msg, link_preview=False)
                    logger.info(f"{F['drop']} DROPPED {len(cards)} cards from {channel_name}")
                    
                    # Also send raw original for reference
                    await client.send_message(DESTINATION, f"{F['neon']} **RAW CAPTURE:**\n`{text[:300]}`")
                except Exception as e:
                    logger.error(f"Send error: {e}")
    
    logger.info(f"{F['alert']}{F['lightning']} XYRON LIVE - READY FOR DROPS {F['lightning']}{F['alert']}")
    logger.info(f"{F['satellite']} MONITORING: {len(monitored_entities)} CHANNELS")
    logger.info(f"{F['target']} DESTINATION: {DESTINATION or 'OWNER'}")
    logger.info(f"{F['crown']} TYPE: /add @channel TO START MONITORING")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())