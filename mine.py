import os
import requests
import json


token = os.getenv("auth_marusa")

url = "https://socialchain.app/api/proof_of_presences"

headers = {
    "Host": "socialchain.app",
    "w": "2",
    "Accept": "application/json, text/plain, */*",
    "Authorization": f"Bearer {token}",
    "Sec-Fetch-Site": "cross-site",
    "Accept-Language": "en-GB,en;q=0.9",
    "Sec-Fetch-Mode": "cors",
    "Content-Type": "application/json",
    "Origin": "https://app-cdn.minepi.com",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "Referer": "https://app-cdn.minepi.com/",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty"
}

data = {
    "recaptcha_token": None 

response = requests.post(url, headers=headers, data=json.dumps(data))
print("Status:", response.status_code)
print("Response:", response.text)
