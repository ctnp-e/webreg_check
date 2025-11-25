import discord
import asyncio
import sys
import web_check

TOKEN =  web_check.BOT_TOKEN
EXIT_CHANNEL_ID = web_check.CHANNEL_ID


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

stop_program = False

async def check_websoc_forever():
    global stop_program
    while not stop_program:
        print("Running GO()...")
        web_check.GO()
        await asyncio.sleep(web_check.TIME_CHECK)

    print("Program stopped by Discord message")
    await client.close()
    sys.exit(0)

@client.event
async def on_ready():
    print(f"Bot logged in as {client.user}")
    open('current_vals.txt', 'w').close()
    
    asyncio.create_task(check_websoc_forever())

@client.event
async def on_message(message):
    global stop_program

    # ignore itself
    if message.author == client.user:
        return

    # only check specific channel
    if message.channel.id != EXIT_CHANNEL_ID:
        return

    if message.content.lower() == "exit":
        stop_program = True
        await message.channel.send("Stopping WebSOC monitor...")

client.run(TOKEN)