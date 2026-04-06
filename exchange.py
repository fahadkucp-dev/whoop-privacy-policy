import json
import time
import requests

# One-time script: exchanges the authorization code for access + refresh tokens
# Run this ONCE, then use whoop.py for all future data pulls.

CLIENT_ID     = "7f29e728-a751-4bd7-90b6-3f4e76bff07c"
CLIENT_SECRET = "8e0e7d2799ee47af2e51ac05a45fb8022672b3bb66422f8defd8ce204bcece5e"
REDIRECT_URI  = "https://localhost"
TOKEN_URL     = "https://api.prod.whoop.com/oauth/oauth2/token"
TOKEN_FILE    = "whoop_tokens.json"

AUTH_CODE = "w2t20R1AmKtYn2i4id4MGRd3bO9jWo4DJVI9idoDJ-E.otQi5X7RfpuKK0k49Ukg6oPIMxtai3DvwTA0zXQc0Xc"

def exchange():
    resp = requests.post(TOKEN_URL, data={
        "grant_type":    "authorization_code",
        "code":          AUTH_CODE,
        "redirect_uri":  REDIRECT_URI,
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    })
    if not resp.ok:
        print("Error:", resp.status_code, resp.text)
        return
    tokens = resp.json()
    tokens["saved_at"] = time.time()
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)
    print("SUCCESS! Tokens saved to", TOKEN_FILE)
    print("Access Token :", tokens.get("access_token", "")[:30], "...")
    print("Refresh Token:", tokens.get("refresh_token", "")[:30], "...")
    print("\nYou can now run: python whoop.py")

if __name__ == "__main__":
    exchange()
