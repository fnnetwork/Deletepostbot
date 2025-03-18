import sys
import subprocess

# Attempt to import required modules; if missing, install via requirements.txt
required_modules = [
    ('telethon', 'telethon>=1.29.0'),
    ('dotenv', 'python-dotenv>=1.0.0')
]

missing = []
for module, package_spec in required_modules:
    try:
        __import__(module)
    except ImportError:
        missing.append(package_spec)

if missing:
    print("Missing modules detected. Installing from requirements.txt...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
    except Exception as install_error:
        print("Error installing required packages:", install_error)
        sys.exit(1)

# Now import all required modules (they should be installed by now)
import logging
import os
import re
import time  # Make sure to import time!
import asyncio
from typing import Dict, Optional
from telethon import TelegramClient, events, Button
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    ApiIdInvalidError,
    ChannelPrivateError,
    FloodWaitError,
    BadRequestError
)
from telethon.tl.custom import Conversation
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")

# State management
USER_STATES: Dict[int, str] = {}  # Tracks user state (e.g., 'user_mode', 'admin_mode')
ACTIVE_CONVERSATIONS: Dict[int, Optional[Conversation]] = {}  # Tracks active conversations
COOLDOWN: Dict[int, float] = {}  # Tracks cooldown timers for users

# Constants
COOLDOWN_TIME = 30  # seconds
MAX_RETRIES = 3
PHONE_REGEX = r"^\+?[1-9]\d{7,14}$"

class ValidationError(Exception):
    pass

class OperationCancelled(Exception):
    pass

def validate_phone_number(phone: str) -> bool:
    return re.match(PHONE_REGEX, phone) is not None

def validate_channel_id(channel_id: str) -> int:
    try:
        cid = int(channel_id)
        if cid >= 0:
            raise ValidationError("Channel ID must be negative (e.g., -100123456789)")
        return cid
    except ValueError:
        raise ValidationError("Invalid Channel ID format")

async def cleanup(client: Optional[TelegramClient] = None):
    if client and client.is_connected():
        await client.disconnect()

async def cancel_operation(user_id: int):
    if user_id in ACTIVE_CONVERSATIONS:
        conv = ACTIVE_CONVERSATIONS.pop(user_id)
        if conv:
            await conv.cancel()
    USER_STATES.pop(user_id, None)
    COOLDOWN.pop(user_id, None)

async def send_main_menu(event, message: str = None):
    user = await event.get_sender()
    text = f"👋 Welcome {user.first_name}!\n" if message is None else message
    text += (
        "\n🔧 Choose an operation mode:\n\n"
        "• `User Mode`: Use your own API credentials\n"
        "• `Admin Mode`: I must be admin in target channel\n\n"
        "_Type /cancel anytime to return here_"
    )
    
    buttons = [
        [Button.inline("User Mode", b"user_mode"),
         Button.inline("Admin Mode", b"admin_mode")],
        [Button.inline("Help", b"help")]
    ]
    
    await event.respond(text, buttons=buttons, parse_mode="md")
    USER_STATES[event.chat_id] = "main_menu"

async def handle_cancel(event):
    user_id = event.chat_id
    await cancel_operation(user_id)
    await event.respond("❌ Operation cancelled", buttons=Button.clear())
    await send_main_menu(event, "Operation cancelled. Choose a mode:")

async def delete_all_posts(client: TelegramClient, channel_id: int):
    try:
        await client.get_entity(channel_id)
    except (ValueError, ChannelPrivateError):
        raise ChannelPrivateError("Channel not found/private")
    
    deleted_count = 0
    async for message in client.iter_messages(channel_id):
        try:
            await message.delete()
            deleted_count += 1
            if deleted_count % 10 == 0:
                await asyncio.sleep(1)
        except FloodWaitError as e:
            logger.warning(f"Flood wait: {e.seconds}s")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"Delete error: {e}")
    
    return deleted_count

async def authenticate_user(conv: Conversation, phone: str, api_id: int, api_hash: str):
    client = TelegramClient(None, api_id, api_hash)
    await client.connect()
    
    try:
        if not await client.is_user_authorized():
            sent_code = await client.send_code_request(phone)
            code_type = sent_code.type.__class__.__name__
            
            hint = "code" if code_type == "SentCodeTypeApp" else "Telegram message"
            await conv.send_message(
                f"Enter the 5-digit code received via {hint} (format: `1 2 3 4 5`):",
                parse_mode="md"
            )
            
            response = await conv.get_response()
            if response.text.lower() == "/cancel":
                raise OperationCancelled()
            
            code = response.text.replace(" ", "")
            if not code.isdigit() or len(code) != 5:
                raise ValidationError("Invalid code format")
            
            try:
                await client.sign_in(phone, code=code)
            except SessionPasswordNeededError:
                await conv.send_message("🔑 Enter your 2FA password:")
                password = (await conv.get_response()).text
                await client.sign_in(password=password)
        
        return client
    except Exception as e:
        await cleanup(client)
        raise e

async def user_mode_flow(event):
    user_id = event.chat_id
    client: Optional[TelegramClient] = None
    async with event.client.conversation(event.chat_id, timeout=600) as conv:
        ACTIVE_CONVERSATIONS[user_id] = conv
        try:
            await conv.send_message(
                "📝 **User Mode Setup**\n\n"
                "1. Get API credentials from [my.telegram.org](https://my.telegram.org)\n"
                "2. Enter them below\n\n"
                "_Type /cancel to abort_",
                parse_mode="md",
                link_preview=False
            )
            
            # API ID
            await conv.send_message("🔢 Enter your **API_ID**:")
            api_id_text = (await conv.get_response()).text
            if not api_id_text.isdigit():
                raise ValidationError("API ID must be a number")
            api_id_input = int(api_id_text)
            
            # API HASH
            await conv.send_message("🔑 Enter your **API_HASH**:")
            api_hash = (await conv.get_response()).text
            if len(api_hash) != 32 or not re.match(r"^[a-f0-9]+$", api_hash):
                raise ValidationError("Invalid API HASH format")
            
            # Phone Number
            await conv.send_message("📱 Enter your phone number (e.g., +12345678901):")
            phone = (await conv.get_response()).text
            if not validate_phone_number(phone):
                raise ValidationError("Invalid phone number")
            
            # Channel ID
            await conv.send_message("🆔 Enter channel ID (e.g., -100123456789):")
            channel_id = validate_channel_id((await conv.get_response()).text)
            
            # Authentication
            client = await authenticate_user(conv, phone, api_id_input, api_hash)
            
            # Channel verification
            try:
                await client.get_entity(channel_id)
            except (ValueError, ChannelPrivateError):
                raise ChannelPrivateError("Channel access denied")
            
            # Confirmation
            await conv.send_message(
                f"⚠️ **WARNING**: This will delete ALL messages in channel `{channel_id}`\n\n"
                "Type `CONFIRM DELETE` to proceed:",
                parse_mode="md"
            )
            confirmation = (await conv.get_response()).text
            if confirmation.lower() != "confirm delete":
                raise OperationCancelled()
            
            progress = await conv.send_message("⏳ Starting deletion...")
            deleted = await delete_all_posts(client, channel_id)
            await progress.edit(f"✅ Successfully deleted {deleted} messages!")
            
        except OperationCancelled:
            await event.respond("❌ Deletion cancelled")
        except Exception as e:
            await event.respond(f"❌ Error: {str(e)}")
        finally:
            await cleanup(client)
            await send_main_menu(event)

async def admin_mode_flow(event):
    user_id = event.chat_id
    async with event.client.conversation(event.chat_id, timeout=600) as conv:
        ACTIVE_CONVERSATIONS[user_id] = conv
        try:
            await conv.send_message(
                "🛡️ **Admin Mode Setup**\n\n"
                "Requirements:\n"
                "1. Add me as admin in the channel\n"
                "2. Grant delete messages permission\n\n"
                "_Type /cancel to abort_",
                parse_mode="md"
            )
            
            await conv.send_message("🆔 Enter channel ID (e.g., -100123456789):")
            channel_id = validate_channel_id((await conv.get_response()).text)
            
            try:
                channel = await event.client.get_entity(channel_id)
                me = await event.client.get_me()
                perms = await event.client.get_permissions(channel, me)
                if not (perms.is_admin and perms.delete_messages):
                    raise PermissionError("Missing admin permissions")
            except (ValueError, ChannelPrivateError):
                raise ChannelPrivateError("Channel not found/access denied")
            
            await conv.send_message(
                f"⚠️ **WARNING**: This will delete ALL messages in {channel.title}\n\n"
                "Type `CONFIRM ADMIN DELETE` to proceed:",
                parse_mode="md"
            )
            confirmation = (await conv.get_response()).text
            if confirmation.lower() != "confirm admin delete":
                raise OperationCancelled()
            
            progress = await conv.send_message("⏳ Starting admin deletion...")
            deleted = await delete_all_posts(event.client, channel_id)
            await progress.edit(f"✅ Deleted {deleted} messages using admin privileges!")
            
        except Exception as e:
            await event.respond(f"❌ Admin mode error: {str(e)}")
        finally:
            await send_main_menu(event)

# Initialize the bot
bot = TelegramClient(f'bot_session_{int(time.time())}', API_ID, API_HASH)

# Event handlers
@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    await send_main_menu(event, "⚡ Hi! Welcome to Telegram Mega Cleaner Bot!")

@bot.on(events.NewMessage(pattern='/cancel'))
async def cancel_handler(event):
    await handle_cancel(event)

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    user_id = event.chat_id
    current_time = time.time()
    cooldown_time = COOLDOWN.get(user_id)
    if cooldown_time is not None and cooldown_time > current_time:
        await event.answer("⏳ Please wait before another action", alert=True)
        return
    
    COOLDOWN[user_id] = current_time + COOLDOWN_TIME
    
    try:
        await event.answer()
        choice = event.data.decode()  # now choice is a string
        
        if choice == "user_mode":
            if USER_STATES.get(user_id) != "user_mode":
                USER_STATES[user_id] = "user_mode"
                await user_mode_flow(event)
        elif choice == "admin_mode":
            if USER_STATES.get(user_id) != "admin_mode":
                USER_STATES[user_id] = "admin_mode"
                await admin_mode_flow(event)
        elif choice == "help":
            await event.edit(
                "🆘 **Help Menu**\n\n"
                "• User Mode: Use your own API credentials for full access\n"
                "• Admin Mode: Requires bot admin rights in channel\n\n"
                "⚠️ Always backup important data before deletion!",
                parse_mode="md"
            )
    except FloodWaitError as e:
        logger.error(f"Flood wait error: please wait for {e.seconds} seconds.")
        await event.respond(f"⏳ You need to wait for {e.seconds} seconds before retrying.")
        await asyncio.sleep(e.seconds)
    except Exception as e:
        logger.error(f"Callback error: {str(e)}")
        await event.respond("❌ An error occurred. Please try again.")

@bot.on(events.NewMessage)
async def message_handler(event):
    user_id = event.chat_id
    if USER_STATES.get(user_id) == "main_menu":
        await send_main_menu(event, "Please choose a mode from the buttons below:")

# Main function
async def main():
    while True:
        try:
            await bot.start(bot_token=BOT_TOKEN)
            logger.info(f"Bot started as @{(await bot.get_me()).username}")
            await bot.run_until_disconnected()
            break
        except FloodWaitError as e:
            logger.error(f"Flood wait error: please wait for {e.seconds} seconds.")
            await asyncio.sleep(e.seconds)

if __name__ == "__main__":
    asyncio.run(main())
