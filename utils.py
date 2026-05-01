from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO


def format_number(n):
    if n >= 1000000:
        return f"{n/1000000:.1f}M"
    if n >= 1000:
        return f"{n/1000:.1f}K"
    return str(n)


def generate_instagram_header(profile):
    width = 1000
    height = 320

    img = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Profile picture
    if profile.get("profile_pic"):
        try:
            response = requests.get(profile["profile_pic"])
            pfp = Image.open(BytesIO(response.content)).resize((170, 170)).convert("RGB")

            mask = Image.new("L", (170, 170), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, 170, 170), fill=255)

            img.paste(pfp, (40, 75), mask)
        except:
            pass

    # Fonts
    try:
        font_username = ImageFont.truetype("arial.ttf", 42)
        font_stats = ImageFont.truetype("arial.ttf", 28)
        font_name = ImageFont.truetype("arial.ttf", 26)
        font_bio = ImageFont.truetype("arial.ttf", 24)
        font_small = ImageFont.truetype("arial.ttf", 20)
    except:
        font_username = ImageFont.load_default()
        font_stats = ImageFont.load_default()
        font_name = ImageFont.load_default()
        font_bio = ImageFont.load_default()
        font_small = ImageFont.load_default()

    username = profile.get("username", "")
    followers = profile.get("followers", 0)
    following = profile.get("following", 0)
    posts = profile.get("posts", 0)
    name = profile.get("full_name", "")
    bio = profile.get("bio", "")
    verified = profile.get("verified", False)

    followers_fmt = format_number(followers)

    # Username
    username_x = 240
    username_y = 70
    draw.text((username_x, username_y), username, fill="white", font=font_username)

    # Measure username width
    bbox = draw.textbbox((username_x, username_y), username, font=font_username)
    username_width = bbox[2] - bbox[0]
    next_x = username_x + username_width + 10

    # Verified badge
    if verified:
        try:
            badge = Image.open("verified.png").convert("RGBA")
            badge = badge.resize((32, 32))
            img.paste(badge, (int(next_x), 78), badge)
            next_x += 40
        except:
            pass

    # Follow button
    follow_x = next_x
    follow_y = 70
    follow_w = 110
    follow_h = 35

    draw.rectangle(
        (follow_x, follow_y, follow_x + follow_w, follow_y + follow_h),
        fill=(0, 149, 246)
    )
    draw.text((follow_x + 25, follow_y + 5), "Follow", fill="white", font=font_small)

    # Menu dots
    draw.text((follow_x + follow_w + 20, username_y), "...", fill="white", font=font_username)

    # Stats
    stats = f"{posts} posts        {followers_fmt} followers        {following} following"
    draw.text((240, 130), stats, fill=(200, 200, 200), font=font_stats)

    # Name & Bio
    draw.text((240, 170), name, fill="white", font=font_name)
    draw.text((240, 200), bio, fill=(180, 180, 180), font=font_bio)

    # Save image
    path = f"header_{username}.png"
    img.save(path)

    return path