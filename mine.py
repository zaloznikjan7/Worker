import os
import requests
import json
import time

user = os.getenv("USER_ID", "default")
delay_file = f"delay_{user}.json"

# Load delay value if file exists
if os.path.exists(delay_file):
    with open(delay_file, "r") as f:
        delay = json.load(f).get("minutes", 0)
else:
    delay = 0

print(f"Delaying execution by {delay} minutes...")
time.sleep(delay * 60)

token = os.getenv("Auth_bearer")
url = os.getenv("API_URL")
ref_url = os.getenv("REFERAL_URL")
host = os.getenv("HOST_NAME")

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
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "Referer": ref_url + "/",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty"
}

data = {
    "recaptcha_token": None 
        }

response = requests.post(url, headers=headers, data=json.dumps(data))
print("Status:", response.status_code)
print("Response:", response.text)

new_delay = delay + 5

with open(delay_file, "w") as f:
    json.dump({"minutes": new_delay}, f)

print(f"Updated delay for {user}: {new_delay} minutes")
