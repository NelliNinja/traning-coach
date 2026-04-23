import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
TOKEN_FILE = "strava_tokens.json"


def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return json.load(f)
    return None


def save_tokens(data):
    with open(TOKEN_FILE, "w") as f:
        json.dump({
            "access_token": data["access_token"],
            "refresh_token": data["refresh_token"],
            "expires_at": data["expires_at"],
        }, f)


def get_access_token():
    tokens = load_tokens()
    if not tokens:
        raise RuntimeError("No Strava tokens found. Run: python setup_strava.py")

    if tokens["expires_at"] < datetime.now().timestamp() + 60:
        resp = requests.post("https://www.strava.com/oauth/token", data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": tokens["refresh_token"],
            "grant_type": "refresh_token",
        })
        resp.raise_for_status()
        save_tokens(resp.json())
        return resp.json()["access_token"]

    return tokens["access_token"]


def get_activities_since(timestamp):
    token = get_access_token()
    resp = requests.get(
        "https://www.strava.com/api/v3/athlete/activities",
        headers={"Authorization": f"Bearer {token}"},
        params={"after": int(timestamp), "per_page": 10},
    )
    resp.raise_for_status()
    return resp.json()


def get_today_activities():
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return get_activities_since(today.timestamp())


def get_recent_activities(days=7):
    from datetime import timedelta
    since = datetime.now() - timedelta(days=days)
    return get_activities_since(since.timestamp())


def format_activity(activity):
    parts = [f"**{activity['name']}** ({activity['type']})"]

    if activity.get("distance"):
        parts.append(f"Distance: {activity['distance'] / 1000:.2f} km")

    if activity.get("moving_time"):
        mins = activity["moving_time"] // 60
        secs = activity["moving_time"] % 60
        parts.append(f"Time: {mins}:{secs:02d}")

    if activity.get("total_elevation_gain"):
        parts.append(f"Elevation: {activity['total_elevation_gain']:.0f} m")

    if activity.get("average_heartrate"):
        parts.append(f"Avg HR: {activity['average_heartrate']:.0f} bpm")

    if activity.get("max_heartrate"):
        parts.append(f"Max HR: {activity['max_heartrate']:.0f} bpm")

    if activity.get("average_speed") and activity.get("type") in ("Run", "VirtualRun"):
        pace_min_per_km = 1000 / activity["average_speed"] / 60
        parts.append(f"Avg Pace: {int(pace_min_per_km)}:{int((pace_min_per_km % 1) * 60):02d} /km")

    if activity.get("suffer_score"):
        parts.append(f"Suffer Score: {activity['suffer_score']}")

    return "\n".join(parts)
