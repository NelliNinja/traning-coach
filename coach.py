import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()
PROFILE_FILE = "profile.json"


def load_profile():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE) as f:
            return json.load(f)
    return {}


def build_system_prompt(profile, recent_activities=None):
    def val(key, unit="", default="not set"):
        v = profile.get(key)
        return f"{v} {unit}".strip() if v else default

    prompt = f"""You are a personal training coach assistant. You are talking directly with the athlete via Discord.

## Athlete Profile
Name: {val('name')}
Age: {val('age', 'years')}
Weight: {val('weight_kg', 'kg')}
Height: {val('height_cm', 'cm')}
Resting Heart Rate: {val('resting_heart_rate', 'bpm')}
Max Heart Rate: {val('max_heart_rate', 'bpm')}
Goals: {val('fitness_goals')}
Preferred activities: {', '.join(profile.get('preferred_activities', [])) or 'not set'}
Notes: {val('notes')}
"""

    if recent_activities:
        prompt += "\n## Recent Strava Activities\n"
        for a in recent_activities[:7]:
            from strava import format_activity
            prompt += format_activity(a).replace("**", "") + "\n\n"

    prompt += """
## How to coach
- Be warm, supportive, and direct — you know this athlete personally
- Always factor in how they say they are feeling (stressed, tired, energetic, etc.) when giving advice
- Ask follow-up questions about how activities felt, not just the numbers
- Give specific, actionable advice — not generic tips
- Reference their actual activity data and personal stats when relevant
- Consider recovery: if they're showing signs of fatigue or high stress, prioritise rest
- Keep responses conversational and concise; go into detail only when asked
- If they report illness, poor sleep, high stress — acknowledge it and adjust training recommendations accordingly
"""
    return prompt


class Coach:
    def __init__(self):
        self.conversation_history = []
        self.profile = load_profile()
        self.recent_activities = []

    def reload_profile(self):
        self.profile = load_profile()

    def update_activities(self, activities):
        self.recent_activities = activities

    def chat(self, message: str) -> str:
        self.conversation_history.append({"role": "user", "content": message})

        # Rolling window to stay within token limits
        history = self.conversation_history[-30:]

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": build_system_prompt(self.profile, self.recent_activities),
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=history,
        )

        reply = response.content[0].text
        self.conversation_history.append({"role": "assistant", "content": reply})
        return reply

    def clear_history(self):
        self.conversation_history = []
