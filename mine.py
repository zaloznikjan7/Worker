import os
import json
import time
import requests
from datetime import datetime, timedelta, timezone

user = os.getenv("USER_ID", "default")
state_file = f"state_{user}.json"

token   = os.getenv("Auth_bearer")
api_url = os.getenv("API_URL")
ref_url = os.getenv("REFERAL_URL")
host    = os.getenv("HOST_NAME")

headers = {
    "Host": host,
    "w": "2",
    "Accept": "application/json, text/plain, */*",
    "Authorization": f"Bearer {token}",
    "Sec-Fetch-Site": "cross-site",
    "Accept-Language": "en-GB,en;q=0.9",
    "Sec-Fetch-Mode": "cors",
    "Content-Type": "application/json",
    "Origin": ref_url,
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) "
                  "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "Referer": ref_url + "/",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
}

payload = {"recaptcha_token": None}


if os.path.exists(state_file):
    with open(state_file, "r") as f:
        s = json.load(f)
        last_succ = datetime.fromisoformat(s["last_success"])
else:
    last_succ = datetime.now(timezone.utc) - timedelta(days=1, minutes=1)

next_allowed = last_succ + timedelta(days=1, minutes=1)
now = datetime.now(timezone.utc)

print(f"[{user}] now={now.isoformat()} next_allowed={next_allowed.isoformat()}")

if now < next_allowed:
    wait_sec = (next_allowed - now).total_seconds()
    print(f"[{user}] Not yet time—sleeping for {int(wait_sec)} s…")
    time.sleep(wait_sec)

for attempt in range(1, 11):
    print(f"[{user}] Attempt {attempt}/5…")
    try:
        r = requests.post(api_url, headers=headers, json=payload)
        print(f"[{user}] Status {r.status_code}")
        if r.status_code == 200:
            new_state = {
                "last_success": datetime.now(timezone.utc).isoformat()
            }
            with open(state_file, "w") as f:
                json.dump(new_state, f)
            print(f"[{user}] ✅ Success—state updated.")
            exit(0)
    except Exception as e:
        print(f"[{user}] ❌ Exception:", e)

    if attempt < 5:
        print(f"[{user}] ⏳ Waiting 5 min before retry…")
        time.sleep(5 * 60)

print(f"[{user}] 💥 All retries exhausted—will try again tomorrow.")
exit(1)
