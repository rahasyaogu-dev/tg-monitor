from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, ForceReply
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN, OWNER_IDS, MIN_TIME, MAX_TIME, START_IMAGE_URL
from database import set_user_time, get_user_time, add_monitor, get_active_monitors, stop_monitor, delete_monitor, set_channel_config, get_channel_config, get_notification_target
from api import get_instagram_profile
from monitor import start_monitor_task
import datetime
import os
from utils import generate_instagram_header

user_states = {}

def check_owner(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in OWNER_IDS:
            await update.message.reply_text("<b>Access Denied, This bot is private.</b>", parse_mode="HTML")
            return
        return await func(update, context)
    return wrapper

def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("✕ ᴍᴏɴɪᴛᴏʀ ʙᴀɴ", callback_data="monitor_ban"),
         InlineKeyboardButton("✓ ᴍᴏɴɪᴛᴏʀ ᴜɴʙᴀɴ", callback_data="monitor_unban")],
        [InlineKeyboardButton("✓ ᴍᴏɴɪᴛᴏʀ ᴠᴇʀɪꜰʏ", callback_data="monitor_verify"),
         InlineKeyboardButton("≡ ʜᴇʟᴘ", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def start_caption():
    message = "<b>ɪɴꜱᴛᴀɢʀᴀᴍ ᴘʀᴏꜰɪʟᴇ ᴍᴏɴɪᴛᴏʀ ʙᴏᴛ</b>\n\n"
    message += "<blockquote>ᴛʀᴀᴄᴋ ɪɴꜱᴛᴀɢʀᴀᴍ ᴘʀᴏꜰɪʟᴇꜱ ꜰᴏʀ ʙᴀɴ, ᴜɴʙᴀɴ, ᴀɴᴅ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ꜱᴛᴀᴛᴜꜱ ᴄʜᴀɴɢᴇꜱ.</blockquote>\n\n"
    message += '<a href="https://t.me/mannerful">ᴅᴇᴠᴇʟᴏᴘᴇʀ</a> | <a href="https://t.me/+QEwTCUt99RFhMzc9">ᴄʜᴀɴɴᴇʟ</a>'
    return message

@check_owner
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_photo(
        photo=START_IMAGE_URL,
        caption=start_caption(),
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id not in OWNER_IDS:
        await query.answer("Access Denied", show_alert=True)
        return

    if query.data == "help":
        keyboard = [[InlineKeyboardButton("← ʙᴀᴄᴋ", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        help_text = "<b>📖 ʜᴇʟᴘ ɢᴜɪᴅᴇ</b>\n\n"
        help_text += "<b>ᴄᴏᴍᴍᴀɴᴅꜱ:</b>\n"
        help_text += "• /settime - ꜱᴇᴛ ᴍᴏɴɪᴛᴏʀɪɴɢ ɪɴᴛᴇʀᴠᴀʟ\n"
        help_text += "• /setbanchannel - ꜱᴇᴛ ᴄʜᴀɴɴᴇʟ ꜰᴏʀ ʙᴀɴ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴꜱ\n"
        help_text += "• /setunbanchannel - ꜱᴇᴛ ᴄʜᴀɴɴᴇʟ ꜰᴏʀ ᴜɴʙᴀɴ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴꜱ\n"
        help_text += "• /setverifychannel - ꜱᴇᴛ ᴄʜᴀɴɴᴇʟ ꜰᴏʀ ᴠᴇʀɪꜰʏ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴꜱ\n"
        help_text += "• /viewsettings - ᴠɪᴇᴡ ᴄᴜʀʀᴇɴᴛ ꜱᴇᴛᴛɪɴɢꜱ\n"
        help_text += "• /active_monitor - ᴠɪᴇᴡ ᴀᴄᴛɪᴠᴇ ᴍᴏɴɪᴛᴏʀꜱ\n"
        help_text += "• /stop - ꜱᴛᴏᴘ ᴀ ᴍᴏɴɪᴛᴏʀ\n"
        help_text += "• /insta - ɢᴇᴛ ɪɴꜱᴛᴀɢʀᴀᴍ ᴘʀᴏꜰɪʟᴇ ɪɴꜰᴏ\n"
        help_text += "• /testban - ᴛᴇꜱᴛ ʙᴀɴ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ\n"
        help_text += "• /testunban - ᴛᴇꜱᴛ ᴜɴʙᴀɴ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ\n\n"
        help_text += "<b>ʜᴏᴡ ᴛᴏ ᴜꜱᴇ:</b>\n"
        help_text += "1. ꜱᴇᴛ ᴛɪᴍᴇ ɪɴᴛᴇʀᴠᴀʟ ᴜꜱɪɴɢ /settime\n"
        help_text += "2. ꜱᴇᴛ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ ᴄʜᴀɴɴᴇʟꜱ ᴜꜱɪɴɢ /setbanchannel, /setunbanchannel, /setverifychannel\n"
        help_text += "3. ᴄʜᴏᴏꜱᴇ ᴍᴏɴɪᴛᴏʀɪɴɢ ᴛʏᴘᴇ\n"
        help_text += "4. ꜱᴇɴᴅ ɪɴꜱᴛᴀɢʀᴀᴍ ᴜꜱᴇʀɴᴀᴍᴇ ᴏʀ ʟɪɴᴋ\n"
        help_text += "5. ʙᴏᴛ ᴡɪʟʟ ɴᴏᴛɪꜰʏ ᴡʜᴇɴ ꜱᴛᴀᴛᴜꜱ ᴄʜᴀɴɢᴇꜱ"

        await query.edit_message_caption(
            caption=help_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

    elif query.data == "back":
        await query.edit_message_caption(
            caption=start_caption(),
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )

    elif query.data.startswith("monitor_"):
        user_time = get_user_time(user_id)
        if not user_time:
            await query.answer("⚠️ Please set time first using /settime command", show_alert=True)
            return

        monitor_type = query.data.split("_")[1]
        user_states[user_id] = {"waiting_for": "username", "type": monitor_type}

        type_names = {
            "ban": "✕ ᴍᴏɴɪᴛᴏʀ ʙᴀɴ",
            "unban": "✓ ᴍᴏɴɪᴛᴏʀ ᴜɴʙᴀɴ",
            "verify": "✓ ᴍᴏɴɪᴛᴏʀ ᴠᴇʀɪꜰʏ"
        }

        await context.bot.send_chat_action(chat_id=user_id, action="typing")
        await query.message.delete()

        text = f"<b>{type_names.get(monitor_type,'Monitoring')}</b>\n\n"
        text += "<blockquote>Send Instagram Username or Profile Link\n\nExample: username or https://instagram.com/username</blockquote>\n\n"
        text += "<i>To cancel use /cancel command</i>"

        await context.bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode="HTML",
            reply_markup=ForceReply(selective=True, input_field_placeholder="Enter username")
        )

    elif query.data.startswith("time_"):
        time_value = query.data.split("_")[1]

        if time_value == "custom":
            user_states[user_id] = {"waiting_for": "custom_time"}
            await query.message.delete()
            try:
                await context.bot.delete_message(chat_id=user_id, message_id=query.message.message_id - 1)
            except:
                pass
            await context.bot.send_message(
                chat_id=user_id,
                text=f"<b>Set Custom Time</b>\n\nSend time in minutes (e.g., 30)\n\n<i>Range: {MIN_TIME}-{MAX_TIME} minutes</i>",
                parse_mode="HTML"
            )
        else:
            time_minutes = int(time_value)
            set_user_time(user_id, time_minutes)

            await query.message.delete()
            try:
                await context.bot.delete_message(chat_id=user_id, message_id=query.message.message_id - 1)
            except:
                pass

            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ <b>Time Interval Set</b>\n\n<i>Your monitoring interval is set to {time_minutes} minutes.</i>",
                parse_mode="HTML"
            )
            user_states.pop(user_id, None)

    elif query.data == "close_settime":
        await query.message.delete()
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=query.message.message_id - 1)
        except:
            pass

@check_owner
async def settime_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("◴ 5 ᴍɪɴ", callback_data="time_5"),
         InlineKeyboardButton("◴ 10 ᴍɪɴ", callback_data="time_10")],
        [InlineKeyboardButton("◴ 15 ᴍɪɴ", callback_data="time_15"),
         InlineKeyboardButton("◴ 30 ᴍɪɴ", callback_data="time_30")],
        [InlineKeyboardButton("• ᴄᴜꜱᴛᴏᴍ", callback_data="time_custom"),
         InlineKeyboardButton("✕ ᴄʟᴏꜱᴇ ✕", callback_data="close_settime")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "<b>Select Time Interval</b>\n\n<i>Choose how often to check the profile:</i>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

@check_owner
async def set_ban_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = {"waiting_for": "ban_channel"}
    
    await update.message.reply_text(
        "<b>Set Ban Notification Channel</b>\n\n"
        "Send the channel ID where ban notifications should be sent.\n\n"
        "Examples:\n"
        "- Channel ID: -1001234567890\n"
        "- Topic ID: 12345 (if using topics)\n"
        "- Channel with topic: -1001234567890:12345\n\n"
        "<i>Make sure the bot is an admin in that channel/group.</i>\n\n"
        "Use /cancel to cancel.",
        parse_mode="HTML"
    )

@check_owner
async def set_unban_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = {"waiting_for": "unban_channel"}
    
    await update.message.reply_text(
        "<b>Set Unban Notification Channel</b>\n\n"
        "Send the channel ID where unban notifications should be sent.\n\n"
        "Examples:\n"
        "- Channel ID: -1001234567890\n"
        "- Topic ID: 12345 (if using topics)\n"
        "- Channel with topic: -1001234567890:12345\n\n"
        "<i>Make sure the bot is an admin in that channel/group.</i>\n\n"
        "Use /cancel to cancel.",
        parse_mode="HTML"
    )

@check_owner
async def set_verify_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = {"waiting_for": "verify_channel"}
    
    await update.message.reply_text(
        "<b>Set Verify Notification Channel</b>\n\n"
        "Send the channel ID where verify notifications should be sent.\n\n"
        "Examples:\n"
        "- Channel ID: -1001234567890\n"
        "- Topic ID: 12345 (if using topics)\n"
        "- Channel with topic: -1001234567890:12345\n\n"
        "<i>Make sure the bot is an admin in that channel/group.</i>\n\n"
        "Use /cancel to cancel.",
        parse_mode="HTML"
    )

@check_owner
async def view_settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    ban_channel = get_channel_config(user_id, "ban_channel")
    unban_channel = get_channel_config(user_id, "unban_channel")
    verify_channel = get_channel_config(user_id, "verify_channel")
    time_interval = get_user_time(user_id)
    
    message = "<b>Current Settings</b>\n\n"
    message += f"<b>Time Interval:</b> {time_interval if time_interval else 'Not set'} minutes\n\n"
    message += "<b>Notification Channels:</b>\n"
    message += f"• Ban: {ban_channel if ban_channel else 'Not set'}\n"
    message += f"• Unban: {unban_channel if unban_channel else 'Not set'}\n"
    message += f"• Verify: {verify_channel if verify_channel else 'Not set'}\n\n"
    message += "<i>Use /setbanchannel, /setunbanchannel, or /setverifychannel to update settings.</i>"
    
    await update.message.reply_text(message, parse_mode="HTML")

@check_owner
async def active_monitor_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    monitors = get_active_monitors(user_id)

    if not monitors:
        await update.message.reply_text("📭 <b>No Active Monitors</b>\n\n<i>You have no active monitors running.</i>", parse_mode="HTML")
        return

    message = "<b>📊 Active Monitors</b>\n\n"
    for idx, monitor in enumerate(monitors, 1):
        message += f"{idx}. <b>@{monitor['username']}</b>\n"
        message += f"   Type: <i>{monitor['type'].title()}</i>\n"
        message += f"   ID: <code>{str(monitor['_id'])}</code>\n\n"

    await update.message.reply_text(message, parse_mode="HTML")

@check_owner
async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ <b>Usage:</b> /stop [monitor_id]\n\n<i>Get monitor IDs from /active_monitor</i>", parse_mode="HTML")
        return

    try:
        monitor_id = int(context.args[0])
        stop_monitor(monitor_id)
        await update.message.reply_text("✅ <b>Monitor Stopped</b>\n\n<i>The monitor has been deactivated.</i>", parse_mode="HTML")
    except ValueError:
        await update.message.reply_text("❌ <b>Invalid Monitor ID. Please use a valid number.</b>", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ <b>Error:</b> {str(e)}", parse_mode="HTML")

@check_owner
async def insta_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ <b>Usage:</b> /insta [username]\n\n<i>Example: /insta instagram</i>", parse_mode="HTML")
        return

    username = context.args[0].replace("https://", "").replace("www.", "").replace("instagram.com/", "").replace("@", "").strip("/")

    await update.message.reply_text("🔍 <i>Fetching profile info...</i>", parse_mode="HTML")

    profile = get_instagram_profile(username)

    if not profile.get("available", False):
        await update.message.reply_text(f"❌ <b>Profile not found or unavailable</b>\n\n<i>@{username}</i>", parse_mode="HTML")
        return

    message = f"<b>📱 Instagram Profile</b>\n\n"
    message += f"<b>Username:</b> @{profile.get('username', username)}\n"
    message += f"<b>Name:</b> {profile.get('name', 'N/A')}\n"
    message += f"<b>Followers:</b> {profile.get('followers', 0):,}\n"
    message += f"<b>Following:</b> {profile.get('following', 0):,}\n"
    message += f"<b>Posts:</b> {profile.get('posts', 0):,}\n"
    message += f"<b>Verified:</b> {'✓ Yes' if profile.get('verified', False) else '✗ No'}\n"
    message += f"<b>Private:</b> {'🔒 Yes' if profile.get('private', False) else '🌐 No'}\n\n"
    message += f"<b>Bio:</b>\n<i>{profile.get('bio', 'No bio')}</i>"

    if profile.get('profile_pic'):
        await update.message.reply_photo(
            photo=profile['profile_pic'],
            caption=message,
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(message, parse_mode="HTML")

@check_owner
async def test_ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    
    if len(args) < 2:
        await update.message.reply_text(
            "❌ <b>Usage:</b> /testban [username] [time_taken]\n\n"
            "<i>Example: /testban instagram 2m 30s</i>",
            parse_mode="HTML"
        )
        return
    
    username = args[0].replace("@", "").strip()
    tat = " ".join(args[1:])
    
    processing_msg = await update.message.reply_text("🔍 <i>Processing...</i>", parse_mode="HTML")
    
    profile = get_instagram_profile(username)
    
    if not profile or not profile.get("available", False):
        await processing_msg.edit_text("❌ Profile not found", parse_mode="HTML")
        return
    
    ban_channel = get_channel_config(update.effective_user.id, "ban_channel")
    
    if not ban_channel:
        await processing_msg.edit_text("❌ No ban channel configured. Use /setbanchannel", parse_mode="HTML")
        return
    
    image_path = generate_instagram_header(profile)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
    
    caption = f"<b>sent to the grave | @{username} 🚫</b>\n\nFollowers: {profile.get('followers', 0):,} | Time Taken: {tat}\n\n<i>Banned at {now}</i>"
    
    try:
        if ":" in ban_channel:
            channel_id, topic_id = ban_channel.split(":")
            channel_id = int(channel_id)
            topic_id = int(topic_id)
            
            with open(image_path, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=channel_id,
                    message_thread_id=topic_id,
                    photo=photo,
                    caption=caption,
                    parse_mode="HTML"
                )
        else:
            channel_id = int(ban_channel)
            
            with open(image_path, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=channel_id,
                    photo=photo,
                    caption=caption,
                    parse_mode="HTML"
                )
        
        os.remove(image_path)
        await processing_msg.edit_text(f"✅ Test ban notification sent for @{username}", parse_mode="HTML")
        
    except Exception as e:
        if os.path.exists(image_path):
            os.remove(image_path)
        await processing_msg.edit_text(f"❌ Error: {str(e)}", parse_mode="HTML")

@check_owner
async def test_unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    
    if len(args) < 2:
        await update.message.reply_text(
            "❌ <b>Usage:</b> /testunban [username] [time_taken]\n\n"
            "<i>Example: /testunban instagram 2m 30s</i>",
            parse_mode="HTML"
        )
        return
    
    username = args[0].replace("@", "").strip()
    tat = " ".join(args[1:])
    
    processing_msg = await update.message.reply_text("🔍 <i>Processing...</i>", parse_mode="HTML")
    
    profile = get_instagram_profile(username)
    
    if not profile or not profile.get("available", False):
        await processing_msg.edit_text("❌ Profile not found", parse_mode="HTML")
        return
    
    unban_channel = get_channel_config(update.effective_user.id, "unban_channel")
    
    if not unban_channel:
        await processing_msg.edit_text("❌ No unban channel configured. Use /setunbanchannel", parse_mode="HTML")
        return
    
    image_path = generate_instagram_header(profile)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
    
    caption = f"<b>return from the grave | @{username} 🏆✅</b>\n\nFollowers: {profile.get('followers', 0):,} | Time Taken: {tat}\n\n<i>Unbanned at {now}</i>"
    
    try:
        if ":" in unban_channel:
            channel_id, topic_id = unban_channel.split(":")
            channel_id = int(channel_id)
            topic_id = int(topic_id)
            
            with open(image_path, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=channel_id,
                    message_thread_id=topic_id,
                    photo=photo,
                    caption=caption,
                    parse_mode="HTML"
                )
        else:
            channel_id = int(unban_channel)
            
            with open(image_path, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=channel_id,
                    photo=photo,
                    caption=caption,
                    parse_mode="HTML"
                )
        
        os.remove(image_path)
        await processing_msg.edit_text(f"✅ Test unban notification sent for @{username}", parse_mode="HTML")
        
    except Exception as e:
        if os.path.exists(image_path):
            os.remove(image_path)
        await processing_msg.edit_text(f"❌ Error: {str(e)}", parse_mode="HTML")

@check_owner
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in user_states:
        user_states.pop(user_id, None)
        await update.message.reply_text("✅ <b>Cancelled</b>\n\n<i>Operation cancelled successfully.</i>", parse_mode="HTML")
    else:
        await update.message.reply_text("ℹ️ <b>No active operation to cancel</b>", parse_mode="HTML")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in OWNER_IDS:
        return

    text = update.message.text

    if user_id not in user_states:
        return

    state = user_states[user_id]

    if state.get("waiting_for") == "custom_time":
        try:
            time_minutes = int(text.strip())

            if time_minutes < MIN_TIME or time_minutes > MAX_TIME:
                await update.message.reply_text(f"⚠️ Time must be between {MIN_TIME} and {MAX_TIME} minutes", parse_mode="HTML")
                return

            set_user_time(user_id, time_minutes)

            await update.message.reply_text(
                f"✅ <b>Time Interval Set</b>\n\n<i>Your monitoring interval is set to {time_minutes} minutes.</i>",
                parse_mode="HTML"
            )
            user_states.pop(user_id, None)
        except ValueError:
            await update.message.reply_text("❌ <b>Invalid Format</b>\n\n<i>Send a valid number (e.g., 30)</i>", parse_mode="HTML")

    elif state.get("waiting_for") in ["ban_channel", "unban_channel", "verify_channel"]:
        notification_type = state["waiting_for"].replace("_channel", "")
        target = text.strip()
        
        # Debug print
        print(f"Setting {notification_type} channel to: {target}")
        
        try:
            if ":" in target:
                channel_id, topic_id = target.split(":")
                channel_id = int(channel_id)
                topic_id = int(topic_id)
                
                await context.bot.send_message(
                    chat_id=channel_id,
                    message_thread_id=topic_id,
                    text="<b>Test Notification</b>\n\nThis is a test message for channel setup.",
                    parse_mode="HTML"
                )
                saved_value = target
            else:
                channel_id = int(target)
                await context.bot.send_message(
                    chat_id=channel_id,
                    text="<b>Test Notification</b>\n\nThis is a test message for channel setup.",
                    parse_mode="HTML"
                )
                saved_value = target
                
            # Save to database
            set_channel_config(user_id, saved_value, f"{notification_type}_channel", saved_value)
            
            # Verify it saved
            verify_saved = get_channel_config(user_id, f"{notification_type}_channel")
            print(f"Saved and retrieved: {verify_saved}")
            
            await update.message.reply_text(
                f"✅ <b>{notification_type.upper()} Notification Channel Set</b>\n\nTarget: {saved_value}\n\nTest message sent successfully!",
                parse_mode="HTML"
            )
            user_states.pop(user_id, None)
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ <b>Error</b>\n\nCannot send to this channel/topic.\n\nError: {str(e)}",
                parse_mode="HTML"
            )
            return

    elif state.get("waiting_for") == "username":
        username = text.replace("https://", "").replace("www.", "").replace("instagram.com/", "").replace("@", "").strip("/")

        msg = await update.message.reply_text("🔍 <i>Checking profile...</i>", parse_mode="HTML")

        profile = get_instagram_profile(username)
        monitor_type = state["type"]

        if monitor_type == "ban":
            if not profile.get("available", False):
                await msg.edit_text("❌ Profile is already unavailable. Cannot start ban monitoring.", parse_mode="HTML")
                user_states.pop(user_id, None)
                return

            monitor_id = add_monitor(user_id, username, "ban", profile)
            time_interval = get_user_time(user_id)
            start_monitor_task(context.bot, user_id, monitor_id, username, "ban", time_interval)

            await msg.edit_text(
                f"✅ <b>Ban Monitor Started</b>\n\n"
                f"<b>Username:</b> @{profile.get('username', username)}\n"
                f"<b>Interval:</b> {time_interval} minutes\n\n"
                f"<i>You'll be notified when the profile becomes unavailable.</i>",
                parse_mode="HTML"
            )

        elif monitor_type == "unban":
            if profile.get("available", False):
                await msg.edit_text("❌ Profile is already available. Cannot start unban monitoring.", parse_mode="HTML")
                user_states.pop(user_id, None)
                return

            monitor_id = add_monitor(user_id, username, "unban", {})
            time_interval = get_user_time(user_id)
            start_monitor_task(context.bot, user_id, monitor_id, username, "unban", time_interval)

            await msg.edit_text(
                f"✅ <b>Unban Monitor Started</b>\n\n"
                f"<b>Username:</b> @{username}\n"
                f"<b>Interval:</b> {time_interval} minutes\n\n"
                f"<i>You'll be notified when the profile becomes available.</i>",
                parse_mode="HTML"
            )

        elif monitor_type == "verify":
            if not profile.get("available", False):
                await msg.edit_text("❌ Profile is unavailable. Cannot start verification monitoring.", parse_mode="HTML")
                user_states.pop(user_id, None)
                return

            if profile.get("verified", False):
                await msg.edit_text("❌ Profile is already verified. Cannot start verification monitoring.", parse_mode="HTML")
                user_states.pop(user_id, None)
                return

            monitor_id = add_monitor(user_id, username, "verify", profile)
            time_interval = get_user_time(user_id)
            start_monitor_task(context.bot, user_id, monitor_id, username, "verify", time_interval)

            await msg.edit_text(
                f"✅ <b>Verification Monitor Started</b>\n\n"
                f"<b>Username:</b> @{profile.get('username', username)}\n"
                f"<b>Interval:</b> {time_interval} minutes\n\n"
                f"<i>You'll be notified when the profile gets verified.</i>",
                parse_mode="HTML"
            )

        user_states.pop(user_id, None)

def setup_handlers(application):
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("settime", settime_command))
    application.add_handler(CommandHandler("active_monitor", active_monitor_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("insta", insta_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("setbanchannel", set_ban_channel_command))
    application.add_handler(CommandHandler("setunbanchannel", set_unban_channel_command))
    application.add_handler(CommandHandler("setverifychannel", set_verify_channel_command))
    application.add_handler(CommandHandler("viewsettings", view_settings_command))
    application.add_handler(CommandHandler("testban", test_ban_command))
    application.add_handler(CommandHandler("testunban", test_unban_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))