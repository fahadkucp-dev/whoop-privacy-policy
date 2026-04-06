import os
import json
import time
import webbrowser
import urllib.parse
import requests

CLIENT_ID     = "7f29e728-a751-4bd7-90b6-3f4e76bff07c"
CLIENT_SECRET = "8e0e7d2799ee47af2e51ac05a45fb8022672b3bb66422f8defd8ce204bcece5e"
REDIRECT_URI  = "https://localhost"
TOKEN_FILE    = "whoop_tokens.json"

SCOPES = "offline read:recovery read:sleep read:cycles read:workout read:profile read:body_measurement"
AUTH_URL   = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL  = "https://api.prod.whoop.com/oauth/oauth2/token"
API_BASE   = "https://api.prod.whoop.com/developer/v1"


def save_tokens(tokens):
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)
    print("Tokens saved to", TOKEN_FILE)


def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return json.load(f)
    return None


def refresh_access_token(refresh_token):
    resp = requests.post(TOKEN_URL, data={
        "grant_type":    "refresh_token",
        "refresh_token": refresh_token,
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    })
    resp.raise_for_status()
    tokens = resp.json()
    tokens["saved_at"] = time.time()
    save_tokens(tokens)
    return tokens


def get_valid_tokens():
    tokens = load_tokens()
    if not tokens:
        return None
    saved_at = tokens.get("saved_at", 0)
    expires_in = tokens.get("expires_in", 3600)
    if time.time() - saved_at > (expires_in - 300):
        print("Refreshing access token...")
        tokens = refresh_access_token(tokens["refresh_token"])
    return tokens


def authorize():
    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id":     CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "scope":         SCOPES,
        "state":         "whoop_auth",
    })
    auth_link = f"{AUTH_URL}?{params}"
    print("\nOpening browser for WHOOP authorization...")
    print("Auth URL:", auth_link)
    webbrowser.open(auth_link)
    print("\nAfter authorizing, paste the full redirect URL here")
    print("(it starts with https://localhost?code=...):")
    redirect_url = input("> ").strip()
    parsed = urllib.parse.urlparse(redirect_url)
    code = urllib.parse.parse_qs(parsed.query).get("code", [None])[0]
    if not code:
        raise ValueError("No code found. Paste the full URL from your browser address bar.")
    return code


def exchange_code_for_tokens(code):
    resp = requests.post(TOKEN_URL, data={
        "grant_type":    "authorization_code",
        "code":          code,
        "redirect_uri":  REDIRECT_URI,
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    })
    resp.raise_for_status()
    tokens = resp.json()
    tokens["saved_at"] = time.time()
    save_tokens(tokens)
    return tokens


def api_get(endpoint, tokens):
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = requests.get(f"{API_BASE}{endpoint}", headers=headers)
    resp.raise_for_status()
    return resp.json()


def main():
    tokens = get_valid_tokens()
    if not tokens:
        print("No saved tokens - starting OAuth flow...")
        code = authorize()
        tokens = exchange_code_for_tokens(code)

    print("\nAuthenticated! Fetching your WHOOP data...\n")

    # Profile
    profile = api_get("/user/profile/basic", tokens)
    print(f"Profile: {profile.get('first_name')} {profile.get('last_name')} (ID: {profile.get('user_id')})")

    # Recovery
    recovery = api_get("/recovery?limit=1", tokens)
    if recovery.get("records"):
        r = recovery["records"][0]
        score = r.get("score", {})
        print(f"Latest Recovery Score : {score.get('recovery_score')}%")
        print(f"  HRV: {score.get('hrv_rmssd_milli')} ms  |  Resting HR: {score.get('resting_heart_rate')} bpm")

    # Sleep
    sleep_data = api_get("/activity/sleep?limit=1", tokens)
    if sleep_data.get("records"):
        s = sleep_data["records"][0].get("score", {})
        print(f"Latest Sleep Performance: {s.get('sleep_performance_percentage')}%")
        print(f"  Duration: {round(s.get('total_in_bed_time_milli', 0) / 3600000, 1)}h in bed")

    # Strain / Cycle
    cycle = api_get("/cycle?limit=1", tokens)
    if cycle.get("records"):
        c = cycle["records"][0].get("score", {})
        print(f"Latest Day Strain     : {c.get('strain')}")
        print(f"  Avg HR: {c.get('average_heart_rate')} bpm  |  Kilojoules: {c.get('kilojoule')}")


if __name__ == "__main__":
    main()
