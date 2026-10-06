# WebReg Checker

Monitors UCI WebSOC (and optionally De Anza.. to be improved lol) for open class spots and sends Discord alerts.

> IT WORKS. got into COMPSCI 142a using this!
> works only in the current quarter. why would you use it in previous quarters? idiot.


## Setup

### 0. creating a discord app...
> I honestly forgot how to do this. maybe ask your own AI. I mean, you can tell, after like... part of the year, it was just smoothed over with claude (hello claude). You want to create a discord app and add it to a server where you'll have the webreg instanity stuff occuring. I reccomend making your own personal server because who would want to be pinged like this? anyways. this does actually work, though you have to keep your pc running the whole time. 

### 1. Credentials — `.env`

Copy `.env.example` to `.env` and fill in your values:

```
WEBHOOK_URL=   your Discord webhook URL
BOT_TOKEN=     your Discord bot token
CHANNEL_ID=    the channel ID the bot listens in
USER_ID=       your Discord user ID (for @ mentions)

CHECK_INTERVAL=1800   seconds between checks (1800 = 30 min)
```

### 2. Classes — `classes.txt`

Copy `classes.txt.example` to `classes.txt` and add the classes you want to watch.
Three formats are supported — mix and match freely:

```
# 1. Section code only (simplest)
34210

# 2. Dept + course + instructor — watches ALL sections under that class
COMPSCI . . . . Computer Science, 164, eppstein

# 3. Full — section code + class info (validates at startup that the code matches)
34210, COMPSCI . . . . Computer Science, 164, eppstein
```

> For the dept field, copy it exactly as it appears in the WebSOC dropdown.

### 3. Run

```
py run.py
```


## Discord commands

All commands start with `.webreg`:

| Command | What it does |
|---|---|
| `.webreg list` | Show all classes and whether they're being watched |
| `.webreg remove 34210` | Pause a class (until restart) |
| `.webreg restore 34210` | Resume a paused class |
| `.webreg exit` | Stop the bot |

Pausing/restoring only lasts the current session — restarting `run.py` resets everything back to watching all classes in `classes.txt`.


## De Anza

A separate bot for De Anza College is in the `de_anza/` folder.

1. Copy `de_anza/.env.example` to `de_anza/.env` and fill it in
2. Run: `py de_anza/discord_bot.py`

---

## TODO
- ~~start from disc~~ too hard.
- ~~adjust classes from disc~~ done!
- update the de anza one
- try to make it prettier? move away from discord?

## Changelog
- 1.1.26 — De Anza added, semi works, for mia
- 10.6.26 — multiple classes support added


## File structure

```
run.py                ← run this to start
.env                  ← your credentials (copy from .env.example)
classes.txt           ← classes to watch (copy from classes.txt.example)
.env.example          ← credential template
classes.txt.example   ← classes template

uci/                  ← UCI logic — no need to edit
de_anza/              ← De Anza logic — no need to edit
```
