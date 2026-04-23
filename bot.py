import os
import time as time_module
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import time
from dotenv import load_dotenv
from strava import get_today_activities, get_recent_activities, format_activity
from coach import Coach

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
_channel_id_raw = os.getenv("DISCORD_CHANNEL_ID")
if not _channel_id_raw:
    raise RuntimeError("DISCORD_CHANNEL_ID is not set in environment variables")
CHANNEL_ID = int(_channel_id_raw.strip())

ACTIVITY_KEYWORDS = {
    "activit", "run", "ran", "ride", "rode", "cycl", "swim", "swam",
    "workout", "training", "train", "walk", "hike", "hiked", "exercise",
    "strava", "today", "yesterday", "this week", "last week", "new session",
    "did i", "have i", "what did", "how many", "any new",
}

_last_activity_fetch: float = 0.0
_FETCH_CACHE_SECS = 120  # re-fetch at most every 2 minutes


def _message_mentions_activities(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in ACTIVITY_KEYWORDS)


async def _refresh_activities(silent: bool = True) -> list:
    global _last_activity_fetch
    now = time_module.monotonic()
    if now - _last_activity_fetch < _FETCH_CACHE_SECS:
        return coach.recent_activities  # return cached

    activities = get_recent_activities(days=7)
    coach.update_activities(activities)
    _last_activity_fetch = now
    return activities

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
coach = Coach()


@bot.event
async def on_ready():
    print(f"Training Coach online as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Slash command sync error: {e}")
    daily_check.start()


@tasks.loop(time=time(hour=20, minute=0))  # Posts at 8 PM daily
async def daily_check():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f"Channel {CHANNEL_ID} not found")
        return

    try:
        activities = get_today_activities()
        if not activities:
            return  # No activities today, stay quiet

        coach.update_activities(activities)

        lines = ["**Today's Activities**\n"]
        for a in activities:
            lines.append(format_activity(a))
            lines.append("")

        lines.append("How did your training go? How are you feeling?")
        await channel.send("\n".join(lines))

    except RuntimeError as e:
        await channel.send(f"⚠️ {e}")
    except Exception as e:
        print(f"Daily check error: {e}")


@bot.tree.command(name="activities", description="Show today's Strava activities")
async def cmd_activities(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        activities = get_today_activities()
        if not activities:
            await interaction.followup.send("No activities recorded today yet.")
            return

        coach.update_activities(activities)
        lines = ["**Today's Activities**\n"]
        for a in activities:
            lines.append(format_activity(a))
            lines.append("")
        await interaction.followup.send("\n".join(lines))

    except RuntimeError as e:
        await interaction.followup.send(f"⚠️ {e}")


@bot.tree.command(name="week", description="Show this week's Strava activities")
async def cmd_week(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        activities = get_recent_activities(days=7)
        if not activities:
            await interaction.followup.send("No activities in the past 7 days.")
            return

        coach.update_activities(activities)
        lines = [f"**Last 7 Days ({len(activities)} activities)**\n"]
        for a in activities:
            lines.append(format_activity(a))
            lines.append("")
        await interaction.followup.send("\n".join(lines))

    except RuntimeError as e:
        await interaction.followup.send(f"⚠️ {e}")


@bot.tree.command(name="refresh", description="Pull the latest activities from Strava")
async def cmd_refresh(interaction: discord.Interaction):
    await interaction.response.defer()
    global _last_activity_fetch
    _last_activity_fetch = 0.0  # force a fresh fetch
    try:
        activities = await _refresh_activities()
        if not activities:
            await interaction.followup.send("No recent activities found.")
            return
        lines = [f"**Refreshed — {len(activities)} activit{'y' if len(activities) == 1 else 'ies'} loaded**\n"]
        for a in activities:
            lines.append(format_activity(a))
            lines.append("")
        await interaction.followup.send("\n".join(lines))
    except RuntimeError as e:
        await interaction.followup.send(f"⚠️ {e}")


@bot.tree.command(name="feeling", description="Tell the coach how you're feeling right now")
@app_commands.describe(status="e.g. tired, stressed, great, sore legs")
async def cmd_feeling(interaction: discord.Interaction, status: str):
    await interaction.response.defer()
    reply = coach.chat(f"Right now I'm feeling: {status}")
    await interaction.followup.send(reply)


@bot.tree.command(name="reset", description="Start a fresh conversation with the coach")
async def cmd_reset(interaction: discord.Interaction):
    coach.clear_history()
    await interaction.response.send_message("Conversation reset — fresh start!")


@bot.tree.command(name="profile", description="Show the current athlete profile")
async def cmd_profile(interaction: discord.Interaction):
    import json
    coach.reload_profile()
    p = coach.profile
    if not p:
        await interaction.response.send_message("No profile found. Edit `profile.json` to add your details.")
        return

    lines = ["**Athlete Profile**\n"]
    fields = [
        ("Name", "name"), ("Age", "age"), ("Weight", "weight_kg"),
        ("Height", "height_cm"), ("Resting HR", "resting_heart_rate"),
        ("Max HR", "max_heart_rate"), ("Goals", "fitness_goals"),
        ("Preferred Activities", "preferred_activities"), ("Notes", "notes"),
    ]
    for label, key in fields:
        val = p.get(key)
        if val:
            if isinstance(val, list):
                val = ", ".join(val)
            lines.append(f"**{label}:** {val}")

    await interaction.response.send_message("\n".join(lines))


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id != CHANNEL_ID:
        return
    if message.content.startswith("/"):
        await bot.process_commands(message)
        return

    async with message.channel.typing():
        try:
            if _message_mentions_activities(message.content):
                await _refresh_activities()
            reply = coach.chat(message.content)
            for chunk in [reply[i:i+1900] for i in range(0, len(reply), 1900)]:
                await message.reply(chunk)
        except Exception as e:
            await message.reply(f"Something went wrong: {e}")

    await bot.process_commands(message)


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN not set in .env")
    bot.run(DISCORD_TOKEN)
