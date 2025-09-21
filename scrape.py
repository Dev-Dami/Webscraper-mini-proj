import requests
import json
import os
import time
import concurrent.futures
import threading
from config import API_BASE

SAVE_FILE = "save.jsonl"
INPUT_FILE = "output.json"
MAX_WORKERS = 2

file_lock = threading.Lock()

def get_user_profile(username: str):
    url = f"{API_BASE}/users/{username}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("data")
        else:
            print(f"Error {response.status_code} for {username}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {username}: {e}")
        return None

def get_user_animelist(username: str, status="completed"):
    url = f"{API_BASE}/users/{username}/animelist?status={status}&limit=5"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            return []
    except requests.exceptions.RequestException as e:
        print(f"Request for animelist failed for {username}: {e}")
        return []

def save_to_jsonl(data: dict):
    with file_lock:
        with open(SAVE_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

def load_users_from_input():
    if os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def get_scraped_users():
    scraped_users = set()
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    user_data = json.loads(line)
                    if "user" in user_data:
                        scraped_users.add(user_data["user"])
                except json.JSONDecodeError:
                    continue
    return scraped_users

def scrape_and_save(user_data):
    username = user_data.get("user")
    if not username:
        return

    print(f"Fetching data for {username}...")
    profile = get_user_profile(username)
    if profile:
        animelist = get_user_animelist(username)
        
        new_user_data = user_data.copy()
        new_user_data.update({
            "name": profile.get("name"),
            "given_name": profile.get("given_name"),
            "family_name": profile.get("family_name"),
            "alternate_names": profile.get("alternate_names", []),
            "birthday": profile.get("birthday"),
            "favorites": profile.get("favorites", {}),
            "about": profile.get("about")
        })
        
        save_to_jsonl(new_user_data)
        print(f"Saved data for {username}")
    else:
        print(f"Could not fetch profile for {username}")
    
    time.sleep(1)

if __name__ == "__main__":
    all_users = load_users_from_input()
    
    if not all_users:
        print(f"{INPUT_FILE} is empty or not found. Please run clean.py first.")
    else:
        scraped_users = get_scraped_users()
        users_to_scrape = [user for user in all_users if user.get("user") not in scraped_users]

        if not users_to_scrape:
            print("All users have already been scraped.")
        else:
            print(f"Found {len(users_to_scrape)} new users to scrape.")
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                executor.map(scrape_and_save, users_to_scrape)

            print(f"\nAll data saved to {SAVE_FILE}")