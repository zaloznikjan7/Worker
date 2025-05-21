import os, json, time, requests
from datetime import datetime, timedelta, timezone
print(f"***DEBUG: starting mine.py for {os.getenv('USER_ID')}***")

user = os.getenv("USER_ID", "default")
state_file = f"state_{user}.json"

if os.path.exists(state_file):
    with open(state_file, "r") as f:
        data = json.load(f)
        next_run = datetime.fromisoformat(data["next_run"])
else:
    next_run = datetime.now(timezone.utc)

now = datetime.now(timezone.utc)
print(f"[{user}] now={now.isoformat()}   next_run={next_run.isoformat()}")

if now < next_run:
    print(f"[{user}] Not yet time — exiting.")
    exit(0)

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

for i in range(1, 6):
    print(f"[{user}] Attempt {i}/5…")
    try:
        r = requests.post(api_url, headers=headers, json=payload)
        print(f"[{user}] Status {r.status_code}")
        if r.status_code == 200:
            body = r.json()
            expires_at = datetime.fromisoformat(
                body["expires_at"].rstrip("Z")
            ).replace(tzinfo=timezone.utc)
            
            new_next = expires_at + timedelta(seconds=20)
            with open(state_file, "w") as f:
                json.dump({"next_run": new_next.isoformat()}, f)
            print(f"[{user}] ✅ Success — next_run updated to {new_next.isoformat()}")
            exit(0)
    except Exception as e:
        print(f"[{user}] ❌ Exception:", e)

    if i < 5:
        print(f"[{user}] ⏳ Sleeping 60 s before retry…")
        time.sleep(60)

print(f"[{user}] 💥 All retries failed — will try again on next poll.")
exit(1)
