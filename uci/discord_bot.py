import discord
import asyncio
import os
import web_check

TOKEN = web_check.BOT_TOKEN
EXIT_CHANNEL_ID = web_check.CHANNEL_ID

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

stop_program = False
watch = {}  # class_key -> 1 (watching) or 0 (paused)


async def check_websoc_forever():
    global stop_program
    while not stop_program:
        print("Running GO()...")
        web_check.GO(watch)
        await asyncio.sleep(web_check.TIME_CHECK)

    print("Program stopped by Discord message")
    await client.close()
    os._exit(0)


@client.event
async def on_ready():
    global watch
    print(f"Bot logged in as {client.user}")
    open('current_vals.txt', 'w').close()

    classes = web_check.load_classes()
    watch = {web_check.class_key(cls): 1 for cls in classes}
    print(f"Watching: {list(watch.keys())}")

    asyncio.create_task(check_websoc_forever())


@client.event
async def on_message(message):
    global stop_program

    if message.author == client.user:
        return
    if message.channel.id != EXIT_CHANNEL_ID:
        return

    content = message.content.strip()
    if not content.startswith(".webreg "):
        return

    args = content[8:].strip()
    cmd = args.lower()

    if cmd == "exit":
        stop_program = True
        await message.channel.send("Stopping WebSOC monitor...")

    elif cmd.startswith("remove "):
        key = args[7:].strip()
        if key in watch:
            watch[key] = 0
            await message.channel.send(f"Paused watching **{key}**.")
        else:
            await message.channel.send(f"Unknown class **{key}**. Use `.webreg list` to see valid keys.")

    elif cmd.startswith("restore "):
        key = args[8:].strip()
        if key in watch:
            watch[key] = 1
            await message.channel.send(f"Resumed watching **{key}**.")
        else:
            await message.channel.send(f"Unknown class **{key}**. Use `.webreg list` to see valid keys.")

    elif cmd == "list":
        lines = [
            f"{'✅' if status else '⏸️'} {key}"
            for key, status in watch.items()
        ]
        await message.channel.send("**Currently watching:**\n" + "\n".join(lines))

    else:
        await message.channel.send(
            "Unknown command. Available commands:\n"
            "`.webreg list` — show all classes\n"
            "`.webreg remove <code>` — pause a class\n"
            "`.webreg restore <code>` — resume a class\n"
            "`.webreg exit` — stop the bot"
        )


client.run(TOKEN)
