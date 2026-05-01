import requests
import json

def generate_user_agent():
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def get_instagram_profile(username):
    url = "https://linkfinder-instagram-scraper.hamoureliasse.workers.dev"

    headers = {
        "User-Agent": generate_user_agent(),
        "Accept": "application/json",
        "Content-Type": "application/json",
        "sec-fetch-site": "cross-site",
        "priority": "u=3, i",
        "accept-language": "en-US,en;q=0.9",
        "sec-fetch-mode": "cors",
        "origin": "https://linkfinderai.com",
        "referer": "https://linkfinderai.com/",
        "sec-fetch-dest": "empty"
    }

    if "instagram.com" not in username:
        username = f"https://www.instagram.com/{username}"

    payload = {"instagram_url": username}

    try:
        r = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)
        data = r.json()[0]

        result = {
            "id": data["id"],
            "username": data["username"],
            "name": data["fullName"],
            "bio": data["biography"],
            "followers": data["followersCount"],
            "following": data["followsCount"],
            "posts": data["postsCount"],
            "private": data["private"],
            "verified": data["verified"],
            "profile_pic": data["profilePicUrlHD"],
            "profile_url": data["url"],
            "available": True
        }
        return result
    except:
        return {"available": False}
