# Training Coach — Status

## Vad det är
En personlig Discord-coachbot som läser Strava-aktiviteter och använder Claude AI för att diskutera träning, återhämtning och hur du mår.

## Status: LIVE på Railway ✅
Boten körs 24/7 på Railway och behöver inte din Mac.
Projekt: **talented.benevolence** på railway.app

## Discord-kommandon
- `/refresh` — hämta senaste aktiviteter från Strava
- `/activities` — dagens aktiviteter
- `/week` — senaste 7 dagarna
- `/feeling <status>` — berätta hur du mår
- `/profile` — visa din träningsprofil
- `/reset` — börja om konversationen

Slash-kommandon kan ta upp till 1h att synka första gången efter deploy.
Chatta fritt i kanalen så svarar coachen direkt!

## GitHub
https://github.com/NelliNinja/traning-coach

## Köra lokalt (vid behov)
```bash
cd /Users/an/claude/training-coach
python3 bot.py
```

## Railway-variabler (service: worker)
Alla 9 variabler är satta direkt på servicen:
- ANTHROPIC_API_KEY
- DISCORD_BOT_TOKEN
- DISCORD_CHANNEL_ID
- STRAVA_CLIENT_ID / CLIENT_SECRET / REFRESH_TOKEN / ACCESS_TOKEN / WEBHOOK_VERIFY_TOKEN
- APP_URL

## Filer
| Fil | Syfte |
|---|---|
| `bot.py` | Huvudbot |
| `coach.py` | Claude AI-logik med konversationsminne |
| `strava.py` | Strava API (stödjer både lokal fil och env vars) |
| `setup_strava.py` | Engångsauktorisering av Strava (redan klar) |
| `profile.json` | Personlig data som coachen använder |
| `requirements.txt` | Python-beroenden |
| `Procfile` | Talar om för Railway hur boten startas |

## Noteringar
- Boten postar automatiskt kl 20:00 om du haft Strava-aktiviteter den dagen
- Strava-tokens förnyas automatiskt var 6:e timme
- Vid kodändringar: pusha till GitHub så deployas Railway automatiskt
