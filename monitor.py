import asyncio
from datetime import datetime
import os
from api import get_instagram_profile
from database import get_monitor_by_id, stop_monitor, delete_monitor, get_notification_target
from image_generator import generate_instagram_header

active_tasks = {}

async def send_notification(bot, user_id, notification_type, username, message_data):
    """Send notification to configured channel/topic with image"""
    channel_id, topic_id = get_notification_target(user_id, notification_type)
    
    # Generate Instagram header image
    profile_data = {
        "username": message_data.get('username', username),
        "full_name": message_data.get('name', ''),
        "bio": message_data.get('bio', ''),
        "followers": message_data.get('followers', 0),
        "following": message_data.get('following', 0),
        "posts": message_data.get('posts', 0),
        "verified": message_data.get('verified', False),
        "profile_pic": message_data.get('profile_pic', '')
    }
    
    image_path = generate_instagram_header(profile_data)
    time_taken = message_data.get('time_taken', 'Unknown')
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
    
    if notification_type == "ban":
        caption = f"**sent to the grave | @{username} 🚫**\n\n"
        caption += f"Followers: {message_data.get('followers', 0):,} | Time Taken: {time_taken}\n\n"
        caption += f"_Banned at {now}_"
    
    elif notification_type == "unban":
        caption = f"**return from the grave | @{username} 🏆✅**\n\n"
        caption += f"Followers: {message_data.get('followers', 0):,} | Time Taken: {time_taken}\n\n"
        caption += f"_Unbanned at {now}_"
    
    elif notification_type == "verify":
        caption = f"**verified | @{username} ✓✅**\n\n"
        caption += f"Followers: {message_data.get('followers', 0):,} | Time Taken: {time_taken}\n\n"
        caption += f"_Verified at {now}_"
    
    # Send notification with image
    if channel_id:
        try:
            with open(image_path, 'rb') as photo:
                if topic_id:
                    await bot.send_photo(
                        chat_id=int(channel_id),
                        message_thread_id=int(topic_id),
                        photo=photo,
                        caption=caption,
                        parse_mode="Markdown"
                    )
                else:
                    await bot.send_photo(
                        chat_id=int(channel_id),
                        photo=photo,
                        caption=caption,
                        parse_mode="Markdown"
                    )
        except Exception as e:
            # Fallback to sending without image
            try:
                if topic_id:
                    await bot.send_message(
                        chat_id=int(channel_id),
                        message_thread_id=int(topic_id),
                        text=caption,
                        parse_mode="Markdown"
                    )
                else:
                    await bot.send_message(
                        chat_id=int(channel_id),
                        text=caption,
                        parse_mode="Markdown"
                    )
            except:
                pass
    else:
        # No channel configured, send to DM
        try:
            with open(image_path, 'rb') as photo:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=photo,
                    caption=caption,
                    parse_mode="Markdown"
                )
        except:
            await bot.send_message(
                chat_id=user_id,
                text=caption,
                parse_mode="Markdown"
            )
    
    # Clean up image file
    if os.path.exists(image_path):
        os.remove(image_path)

async def monitor_ban(bot, user_id, monitor_id, username, time_interval):
    start_time = datetime.now()

    while True:
        monitor = get_monitor_by_id(monitor_id)
        if not monitor or not monitor.get("active"):
            break

        profile = get_instagram_profile(username)

        if not profile["available"]:
            elapsed = datetime.now() - start_time
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)

            time_taken = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

            message_data = {
                "username": username,
                "followers": profile.get('followers', 0),
                "time_taken": time_taken
            }

            await send_notification(bot, user_id, "ban", username, message_data)
            stop_monitor(monitor_id)
            delete_monitor(monitor_id)
            break

        await asyncio.sleep(time_interval * 60)

async def monitor_unban(bot, user_id, monitor_id, username, time_interval):
    start_time = datetime.now()

    while True:
        monitor = get_monitor_by_id(monitor_id)
        if not monitor or not monitor.get("active"):
            break

        profile = get_instagram_profile(username)

        if profile["available"]:
            elapsed = datetime.now() - start_time
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)

            time_taken = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

            message_data = {
                "username": profile["username"],
                "name": profile.get("name", ""),
                "followers": profile.get("followers", 0),
                "following": profile.get("following", 0),
                "posts": profile.get("posts", 0),
                "bio": profile.get("bio", ""),
                "verified": profile.get("verified", False),
                "profile_pic": profile.get("profile_pic", ""),
                "time_taken": time_taken
            }

            await send_notification(bot, user_id, "unban", username, message_data)
            stop_monitor(monitor_id)
            delete_monitor(monitor_id)
            break

        await asyncio.sleep(time_interval * 60)

async def monitor_verify(bot, user_id, monitor_id, username, time_interval):
    start_time = datetime.now()

    while True:
        monitor = get_monitor_by_id(monitor_id)
        if not monitor or not monitor.get("active"):
            break

        profile = get_instagram_profile(username)

        if profile["available"] and profile["verified"]:
            elapsed = datetime.now() - start_time
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)

            time_taken = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

            message_data = {
                "username": profile["username"],
                "name": profile.get("name", ""),
                "followers": profile.get("followers", 0),
                "following": profile.get("following", 0),
                "posts": profile.get("posts", 0),
                "bio": profile.get("bio", ""),
                "verified": profile.get("verified", False),
                "profile_pic": profile.get("profile_pic", ""),
                "time_taken": time_taken
            }

            await send_notification(bot, user_id, "verify", username, message_data)
            stop_monitor(monitor_id)
            delete_monitor(monitor_id)
            break

        await asyncio.sleep(time_interval * 60)

def start_monitor_task(bot, user_id, monitor_id, username, monitor_type, time_interval):
    if monitor_type == "ban":
        task = asyncio.create_task(monitor_ban(bot, user_id, monitor_id, username, time_interval))
    elif monitor_type == "unban":
        task = asyncio.create_task(monitor_unban(bot, user_id, monitor_id, username, time_interval))
    elif monitor_type == "verify":
        task = asyncio.create_task(monitor_verify(bot, user_id, monitor_id, username, time_interval))

    active_tasks[str(monitor_id)] = task