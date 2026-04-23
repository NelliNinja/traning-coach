# Training Coach — Status

## Vad det är
En personlig Discord-coachbot som läser Strava-aktiviteter och använder Claude AI för att diskutera träning, återhämtning och hur du mår.

## Vad som är gjort ✅
- All kod klar och testad
- `.env` konfigurerad (Strava, Anthropic, Discord)
- `profile.json` ifylld med personlig data
- `strava_tokens.json` skapad (Strava auktoriserat)
- Boten startar och svarar i Discord på vanliga meddelanden
- Slash-kommandon synkar (kan ta upp till 1h efter start)

## Köra lokalt (tillfälligt)
```bash
cd /Users/an/claude/training-coach
python3 bot.py
```
⚠️ Boten dör om du stänger locket eller startar om. För permanent drift → deploy till Railway (se nedan).

## Deploy till Railway (nästa steg)
1. Skapa konto på railway.app
2. Nytt projekt → Deploy from GitHub repo
3. Lägg till alla `.env`-variabler under Variables
4. Railway håller boten igång 24/7

## Discord-kommandon
- `/refresh` — hämta senaste aktiviteter från Strava
- `/activities` — dagens aktiviteter
- `/week` — senaste 7 dagarna
- `/feeling <status>` — berätta hur du mår
- `/profile` — visa din träningsprofil
- `/reset` — börja om konversationen

## Filer
| Fil | Syfte |
|---|---|
| `bot.py` | Huvudbot — kör denna |
| `coach.py` | Claude AI-logik med konversationsminne |
| `strava.py` | Strava API-klient |
| `setup_strava.py` | Engångsauktorisering av Strava |
| `profile.json` | Personlig data som coachen använder |
| `requirements.txt` | Python-beroenden |

## Noteringar
- Boten postar automatiskt kl 20:00 om du haft Strava-aktiviteter den dagen
- Chatta fritt i kanalen — boten hämtar automatiskt Strava-data om du frågar om aktiviteter
- Aktiviteter auto-hämtas var 2:e minut (cache) vid relevanta frågor
